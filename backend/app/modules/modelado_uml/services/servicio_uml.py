from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.config.configuracion import settings
from app.modules.acceso_usuarios.services.servicio_auditoria import ServicioAuditoria
from app.modules.generacion_software.repositories.repositorio_generacion import (
    RepositorioGeneracion,
)
from app.modules.modelado_uml.engine.analizador_texto import construir_uml_desde_texto
from app.modules.modelado_uml.engine.modelo_interno import (
    ModeloDiagramaUML,
)
from app.modules.modelado_uml.engine.validador import validar_modelo_interno
from app.modules.modelado_uml.engine.xmi import exportar_xmi, importar_xmi
from app.modules.modelado_uml.models import (
    AtributoUML,
    ClaseUML,
    DiagramaUML,
    ElementoVisualUML,
    IntercambioXMI,
    MetodoUML,
    ParametroUML,
    RelacionUML,
)
from app.modules.modelado_uml.repositories.repositorio_uml import RepositorioUML
from app.modules.modelado_uml.schemas.uml import (
    RespuestaExportacionXMI,
    RespuestaModeloDiagrama,
    RespuestaValidacionUML,
    SolicitudActualizacionAtributoUML,
    SolicitudActualizacionClaseUML,
    SolicitudActualizacionMetodoUML,
    SolicitudActualizacionParametroUML,
    SolicitudActualizacionRelacionUML,
    SolicitudCreacionAtributoUML,
    SolicitudCreacionClaseUML,
    SolicitudCreacionDiagrama,
    SolicitudCreacionMetodoUML,
    SolicitudCreacionParametroUML,
    SolicitudCreacionRelacionUML,
    SolicitudImportacionXMI,
    SolicitudMoverElemento,
    SolicitudTextoAUML,
)
from app.modules.modelado_uml.services.almacen_diagrama_activo import (
    AlmacenDocumentosUMLActivo,
    construir_modelo_diagrama_sql,
    marcar_diagrama_uml_para_eliminar,
    marcar_proyecto_uml_para_sincronizar,
)
from app.modules.modelado_uml.validators.validador_uml import (
    asegurar_clase_en_diagrama,
    asegurar_clase_existente,
    asegurar_diagrama_existente,
)
from app.modules.proyectos_colaboracion.models import EventoColaboracion
from app.modules.proyectos_colaboracion.repositories.repositorio_integrantes import (
    RepositorioIntegrantes,
)
from app.modules.proyectos_colaboracion.services.guardia_mutaciones_proyecto import (
    GuardiaMutacionesProyecto,
)
from app.modules.proyectos_colaboracion.validators.validador_proyecto import (
    asegurar_participacion,
    asegurar_permiso_proyecto,
)


class ServicioUML:
    def __init__(self, db: Session) -> None:
        self.db = db
        if settings.nosql_consolidated_mode:
            from app.modules.modelado_uml.repositories.repositorio_mongo_uml import (
                RepositorioMongoUML,
            )

            self.uml = RepositorioMongoUML(db)
        else:
            self.uml = RepositorioUML(db)
        self.generations = RepositorioGeneracion(db)
        self.members = RepositorioIntegrantes(db)
        self.audit = ServicioAuditoria(db)
        self.mutations = GuardiaMutacionesProyecto(db)
        self.documents = AlmacenDocumentosUMLActivo()

    def crear_diagrama(self, payload: SolicitudCreacionDiagrama, user_id: UUID) -> DiagramaUML:
        asegurar_permiso_proyecto(self.db, payload.project_id, user_id, "uml.edit")
        existing = self.uml.listar_diagramas_por_proyecto(payload.project_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PROJECT_DIAGRAM_ALREADY_EXISTS",
                    "message": "El proyecto ya tiene su diagrama de clases",
                    "diagram_id": str(existing[0].id),
                },
            )
        self._iniciar_mutacion(payload.project_id)
        diagram = self.uml.agregar_diagrama(
            DiagramaUML(
                project_id=payload.project_id,
                created_by_user_id=user_id,
                name=payload.name,
                diagram_type="class",
                description=payload.description,
                metadata_json=payload.metadata_json,
            )
        )
        self.audit.record(
            module="modelado_uml",
            action="CREATE_DIAGRAM",
            user_id=user_id,
            project_id=payload.project_id,
            metadata={"diagram_id": str(diagram.id)},
        )
        self.db.commit()
        self._actualizar(diagram)
        return diagram

    def listar_diagramas(self, project_id: UUID, user_id: UUID) -> list[DiagramaUML]:
        asegurar_participacion(self.members.obtener_participacion(project_id, user_id))
        return self.uml.listar_diagramas_por_proyecto(project_id)

    def eliminar_diagrama(self, diagram_id: UUID, user_id: UUID) -> None:
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(diagram_id))
        asegurar_participacion(self.members.obtener_participacion(diagram.project_id, user_id))
        self._iniciar_mutacion(diagram.project_id)
        marcar_diagrama_uml_para_eliminar(self.db, diagram.id)
        self.generations.eliminar_arbol_generacion_por_diagrama(diagram_id)
        self.uml.eliminar_elementos_visuales_por_diagrama(diagram_id)
        self.uml.eliminar_relaciones_por_diagrama(diagram_id)
        self.uml.eliminar_clases_por_diagrama(diagram_id)
        self.uml.eliminar_intercambios_xmi_por_diagrama(diagram_id)
        self._desvincular_eventos_colaboracion(diagram_id)
        self.uml.eliminar_diagrama(diagram)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_DIAGRAM",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"diagram_id": str(diagram_id)},
        )
        self.db.commit()

    def _asegurar_nombre_clase_unico(
        self, diagram_id: UUID, name: str, exclude_id: UUID | None = None
    ) -> None:
        normalized_target = name.strip().casefold()
        existing_classes = self.uml.listar_clases(diagram_id)
        for cls in existing_classes:
            if exclude_id and cls.id == exclude_id:
                continue
            if cls.name.strip().casefold() == normalized_target:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "CLASS_NAME_DUPLICATED",
                        "message": "Ya existe una clase con ese nombre en el diagrama",
                    },
                )

    def crear_clase(
        self, diagram_id: UUID, payload: SolicitudCreacionClaseUML, user_id: UUID
    ) -> ClaseUML:
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        self._asegurar_nombre_clase_unico(diagram_id, payload.name)
        self._iniciar_mutacion(diagram.project_id)
        uml_class = self.uml.agregar_clase(
            ClaseUML(
                diagram_id=diagram_id,
                name=payload.name,
                visibility=payload.visibility,
                element_type=payload.element_type,
                stereotype=payload.stereotype,
                description=payload.description,
                metadata_json=payload.metadata_json,
            )
        )
        self.uml.agregar_elemento_visual(
            ElementoVisualUML(
                diagram_id=diagram_id,
                element_type="class",
                element_id=uml_class.id,
                position_x=payload.position_x,
                position_y=payload.position_y,
            )
        )
        self.audit.record(
            module="modelado_uml",
            action="CREATE_CLASS",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"diagram_id": str(diagram_id), "class_id": str(uml_class.id)},
        )
        self.db.commit()
        self._actualizar(uml_class)
        return uml_class

    def listar_clases(self, diagram_id: UUID, user_id: UUID) -> list[ClaseUML]:
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(diagram_id))
        asegurar_participacion(self.members.obtener_participacion(diagram.project_id, user_id))
        return self.uml.listar_clases(diagram_id)

    def obtener_modelo_diagrama(self, diagram_id: UUID, user_id: UUID) -> RespuestaModeloDiagrama:
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(diagram_id))
        asegurar_participacion(self.members.obtener_participacion(diagram.project_id, user_id))
        model = self._construir_modelo_interno(diagram)
        class_details = []
        for item in model.classes:
            class_id = UUID(item.id) if item.id else uuid5(NAMESPACE_URL, item.name)
            visual_id = (
                UUID(item.visual.id)
                if item.visual.id
                else uuid5(NAMESPACE_URL, f"visual:{diagram_id}:{class_id}")
            )
            class_details.append(
                {
                    **item.model_dump(exclude={"attributes", "methods", "visual"}),
                    "id": class_id,
                    "diagram_id": diagram_id,
                    "attributes": [
                        {**attribute.model_dump(), "id": UUID(attribute.id), "class_id": class_id}
                        for attribute in item.attributes
                        if attribute.id
                    ],
                    "methods": [
                        {
                            **method.model_dump(
                                exclude={"parameters", "specification", "readiness"}
                            ),
                            "id": UUID(method.id),
                            "class_id": class_id,
                            "parameters": [
                                {
                                    **parameter.model_dump(),
                                    "id": UUID(parameter.id),
                                    "method_id": UUID(method.id),
                                }
                                for parameter in method.parameters
                                if parameter.id
                            ],
                        }
                        for method in item.methods
                        if method.id
                    ],
                    "visual": {
                        "id": visual_id,
                        "diagram_id": diagram_id,
                        "element_type": "class",
                        "element_id": class_id,
                        "position_x": item.visual.x,
                        "position_y": item.visual.y,
                        "width": item.visual.width,
                        "height": item.visual.height,
                        "style": item.visual.style,
                    },
                }
            )
        return RespuestaModeloDiagrama.model_validate(
            {
                "diagram": {
                    "id": diagram.id,
                    "project_id": diagram.project_id,
                    "created_by_user_id": diagram.created_by_user_id,
                    "name": model.name,
                    "diagram_type": model.diagram_type,
                    "status": model.status,
                    "current_version": model.current_version,
                    "description": model.description,
                    "metadata_json": model.metadata_json,
                    "created_at": diagram.created_at,
                },
                "classes": class_details,
                "relationships": [
                    {
                        **item.model_dump(),
                        "id": UUID(item.id),
                        "diagram_id": diagram_id,
                        "source_class_id": UUID(item.source_class_id),
                        "target_class_id": UUID(item.target_class_id),
                    }
                    for item in model.relationships
                    if item.id
                ],
            }
        )

    def actualizar_clase(
        self, class_id: UUID, payload: SolicitudActualizacionClaseUML, user_id: UUID
    ) -> ClaseUML:
        uml_class = asegurar_clase_existente(self.uml.obtener_clase(class_id))
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(uml_class.diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        if payload.name is not None:
            self._asegurar_nombre_clase_unico(diagram.id, payload.name, exclude_id=class_id)
        self._iniciar_mutacion(diagram.project_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(uml_class, field, value)
        self.audit.record(
            module="modelado_uml",
            action="UPDATE_CLASS",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"class_id": str(class_id)},
        )
        self.db.commit()
        self._actualizar(uml_class)
        return uml_class

    def eliminar_clase(self, class_id: UUID, user_id: UUID) -> None:
        uml_class = asegurar_clase_existente(self.uml.obtener_clase(class_id))
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(uml_class.diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        self._iniciar_mutacion(diagram.project_id)
        for relationship in self.uml.listar_relaciones_clase(class_id):
            self.uml.eliminar_elemento_visual(diagram.id, "relationship", relationship.id)
            self.uml.eliminar_relacion(relationship)
        self.db.flush()
        self.uml.eliminar_elemento_visual(diagram.id, "class", class_id)
        self.uml.eliminar_clase(uml_class)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_CLASS",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"class_id": str(class_id)},
        )
        self.db.commit()

    def agregar_atributo(
        self, class_id: UUID, payload: SolicitudCreacionAtributoUML, user_id: UUID
    ) -> AtributoUML:
        uml_class = asegurar_clase_existente(self.uml.obtener_clase(class_id))
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(uml_class.diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        self._iniciar_mutacion(diagram.project_id)
        attribute = self.uml.agregar_atributo(AtributoUML(class_id=class_id, **payload.model_dump()))
        self.audit.record(
            module="modelado_uml",
            action="CREATE_ATTRIBUTE",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"class_id": str(class_id), "attribute_id": str(attribute.id)},
        )
        self.db.commit()
        self._actualizar(attribute)
        return attribute

    def actualizar_atributo(
        self, attribute_id: UUID, payload: SolicitudActualizacionAtributoUML, user_id: UUID
    ) -> AtributoUML:
        from fastapi import HTTPException, status

        attribute = self.uml.obtener_atributo(attribute_id)
        if attribute is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Atributo UML no encontrado"
            )
        uml_class = asegurar_clase_existente(self.uml.obtener_clase(attribute.class_id))
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(uml_class.diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        self._iniciar_mutacion(diagram.project_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(attribute, field, value)
        self.audit.record(
            module="modelado_uml",
            action="UPDATE_ATTRIBUTE",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"attribute_id": str(attribute_id), "class_id": str(attribute.class_id)},
        )
        self.db.commit()
        self._actualizar(attribute)
        return attribute

    def eliminar_atributo(self, attribute_id: UUID, user_id: UUID) -> None:
        from fastapi import HTTPException, status

        attribute = self.uml.obtener_atributo(attribute_id)
        if attribute is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Atributo UML no encontrado"
            )
        uml_class = asegurar_clase_existente(self.uml.obtener_clase(attribute.class_id))
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(uml_class.diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        self._iniciar_mutacion(diagram.project_id)
        self.uml.eliminar_atributo(attribute)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_ATTRIBUTE",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"attribute_id": str(attribute_id), "class_id": str(uml_class.id)},
        )
        self.db.commit()

    def agregar_metodo(
        self, class_id: UUID, payload: SolicitudCreacionMetodoUML, user_id: UUID
    ) -> MetodoUML:
        uml_class = asegurar_clase_existente(self.uml.obtener_clase(class_id))
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(uml_class.diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        self._iniciar_mutacion(diagram.project_id)
        method = self.uml.agregar_metodo(MetodoUML(class_id=class_id, **payload.model_dump()))
        self.audit.record(
            module="modelado_uml",
            action="CREATE_METHOD",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"class_id": str(class_id), "method_id": str(method.id)},
        )
        self.db.commit()
        self._actualizar(method)
        return method

    def actualizar_metodo(
        self, method_id: UUID, payload: SolicitudActualizacionMetodoUML, user_id: UUID
    ) -> MetodoUML:
        from fastapi import HTTPException, status

        method = self.uml.obtener_metodo(method_id)
        if method is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Metodo UML no encontrado"
            )
        uml_class = asegurar_clase_existente(self.uml.obtener_clase(method.class_id))
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(uml_class.diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        self._iniciar_mutacion(diagram.project_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(method, field, value)
        self.audit.record(
            module="modelado_uml",
            action="UPDATE_METHOD",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"method_id": str(method_id), "class_id": str(method.class_id)},
        )
        self.db.commit()
        self._actualizar(method)
        return method

    def eliminar_metodo(self, method_id: UUID, user_id: UUID) -> None:
        from fastapi import HTTPException, status

        method = self.uml.obtener_metodo(method_id)
        if method is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Metodo UML no encontrado"
            )
        uml_class = asegurar_clase_existente(self.uml.obtener_clase(method.class_id))
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(uml_class.diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        self._iniciar_mutacion(diagram.project_id)
        self.uml.eliminar_metodo(method)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_METHOD",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"method_id": str(method_id), "class_id": str(uml_class.id)},
        )
        self.db.commit()

    def agregar_parametro(
        self, method_id: UUID, payload: SolicitudCreacionParametroUML, user_id: UUID
    ) -> ParametroUML:
        method = self.uml.obtener_metodo(method_id)
        if method is None:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Metodo UML no encontrado"
            )
        uml_class = asegurar_clase_existente(self.uml.obtener_clase(method.class_id))
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(uml_class.diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        self._iniciar_mutacion(diagram.project_id)
        self._validar_parametro(method, payload.name, payload.data_type, payload.default_value)
        parameter = self.uml.agregar_parametro(
            ParametroUML(method_id=method_id, **payload.model_dump())
        )
        self.audit.record(
            module="modelado_uml",
            action="CREATE_PARAMETER",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"method_id": str(method_id), "parameter_id": str(parameter.id)},
        )
        self.db.commit()
        self._actualizar(parameter)
        return parameter

    def actualizar_parametro(
        self, parameter_id: UUID, payload: SolicitudActualizacionParametroUML, user_id: UUID
    ) -> ParametroUML:
        parameter = self.uml.obtener_parametro(parameter_id)
        if parameter is None:
            raise HTTPException(status_code=404, detail="Parametro UML no encontrado")
        method = self.uml.obtener_metodo(parameter.method_id)
        uml_class = asegurar_clase_existente(self.uml.obtener_clase(method.class_id))
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(uml_class.diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        self._iniciar_mutacion(diagram.project_id)
        values = payload.model_dump(exclude_unset=True)
        self._validar_parametro(
            method,
            values.get("name", parameter.name),
            values.get("data_type", parameter.data_type),
            values.get("default_value", parameter.default_value),
            exclude_id=parameter.id,
        )
        for field, value in values.items():
            setattr(parameter, field, value)
        self.audit.record(
            module="modelado_uml",
            action="UPDATE_PARAMETER",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"method_id": str(method.id), "parameter_id": str(parameter.id)},
        )
        self.db.commit()
        self._actualizar(parameter)
        return parameter

    def eliminar_parametro(self, parameter_id: UUID, user_id: UUID) -> None:
        parameter = self.uml.obtener_parametro(parameter_id)
        if parameter is None:
            raise HTTPException(status_code=404, detail="Parametro UML no encontrado")
        method = self.uml.obtener_metodo(parameter.method_id)
        uml_class = asegurar_clase_existente(self.uml.obtener_clase(method.class_id))
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(uml_class.diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        self._iniciar_mutacion(diagram.project_id)
        specification = self.uml.obtener_especificacion_metodo(method.id)
        if specification and self._parametro_esta_referenciado(
            specification, parameter.id, parameter.name
        ):
            raise HTTPException(
                status_code=409,
                detail="El parametro esta referenciado por la especificacion funcional",
            )
        self.uml.eliminar_parametro(parameter)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_PARAMETER",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"method_id": str(method.id), "parameter_id": str(parameter.id)},
        )
        self.db.commit()

    def _validar_parametro(
        self,
        method,
        name: str,
        data_type: str,
        default_value: str | None,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        if any(
            item.id != exclude_id and item.name.casefold() == name.casefold()
            for item in method.parameters
        ):
            raise HTTPException(
                status_code=409, detail="El metodo ya contiene un parametro con ese nombre"
            )
        normalized = data_type.casefold()
        if default_value not in {None, ""}:
            compatible = True
            try:
                if normalized in {"int", "integer", "long"}:
                    int(default_value)
                elif normalized in {"float", "double", "decimal"}:
                    float(default_value)
                elif normalized in {"bool", "boolean"}:
                    compatible = default_value.casefold() in {"true", "false"}
            except ValueError:
                compatible = False
            if not compatible:
                raise HTTPException(
                    status_code=422, detail="El valor por defecto no coincide con el tipo"
                )

    @staticmethod
    def _parametro_esta_referenciado(specification, parameter_id: UUID, name: str) -> bool:
        serialized = str(
            {
                "preconditions": specification.preconditions,
                "postconditions": specification.postconditions,
                "business_rules": specification.business_rules,
                "validations": specification.validations,
                "related_entities": specification.related_entities,
                "frontend_contract": specification.frontend_contract,
            }
        )
        return (
            str(parameter_id) in serialized
            or f"'{name}'" in serialized
            or f'"{name}"' in serialized
        )

    def crear_relacion(
        self, diagram_id: UUID, payload: SolicitudCreacionRelacionUML, user_id: UUID
    ) -> RelacionUML:
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        self._iniciar_mutacion(diagram.project_id)
        source = asegurar_clase_existente(self.uml.obtener_clase(payload.source_class_id))
        target = asegurar_clase_existente(self.uml.obtener_clase(payload.target_class_id))
        asegurar_clase_en_diagrama(source, diagram_id)
        asegurar_clase_en_diagrama(target, diagram_id)
        relationship = self.uml.agregar_relacion(
            RelacionUML(diagram_id=diagram_id, **payload.model_dump())
        )
        self.audit.record(
            module="modelado_uml",
            action="CREATE_RELATION",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"relationship_id": str(relationship.id)},
        )
        self.db.commit()
        self._actualizar(relationship)
        return relationship

    def actualizar_relacion(
        self, relationship_id: UUID, payload: SolicitudActualizacionRelacionUML, user_id: UUID
    ) -> RelacionUML:
        relationship = self.uml.obtener_relacion(relationship_id)
        if relationship is None:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Relacion UML no encontrada"
            )
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(relationship.diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        self._iniciar_mutacion(diagram.project_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(relationship, field, value)
        self.audit.record(
            module="modelado_uml",
            action="UPDATE_RELATION",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"relationship_id": str(relationship_id)},
        )
        self.db.commit()
        self._actualizar(relationship)
        return relationship

    def eliminar_relacion(self, relationship_id: UUID, user_id: UUID) -> None:
        relationship = self.uml.obtener_relacion(relationship_id)
        if relationship is None:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Relacion UML no encontrada"
            )
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(relationship.diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        self._iniciar_mutacion(diagram.project_id)
        self.uml.eliminar_elemento_visual(diagram.id, "relationship", relationship_id)
        self.uml.eliminar_relacion(relationship)
        self.audit.record(
            module="modelado_uml",
            action="DELETE_RELATION",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"relationship_id": str(relationship_id)},
        )
        self.db.commit()

    def mover_elemento(
        self, diagram_id: UUID, payload: SolicitudMoverElemento, user_id: UUID
    ) -> ElementoVisualUML:
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        self._iniciar_mutacion(diagram.project_id)
        visual = self.uml.obtener_elemento_visual(diagram_id, payload.element_type, payload.element_id)
        if visual is None:
            visual = self.uml.agregar_elemento_visual(
                ElementoVisualUML(
                    diagram_id=diagram_id,
                    element_type=payload.element_type,
                    element_id=payload.element_id,
                    position_x=payload.position_x,
                    position_y=payload.position_y,
                    width=payload.width,
                    height=payload.height,
                    style=payload.style,
                )
            )
        else:
            visual.position_x = payload.position_x
            visual.position_y = payload.position_y
            visual.width = payload.width
            visual.height = payload.height
            visual.style = payload.style
        self.audit.record(
            module="modelado_uml",
            action="MOVE_ELEMENT",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"element_type": payload.element_type, "element_id": str(payload.element_id)},
        )
        self.db.commit()
        self._actualizar(visual)
        return visual

    def validar_diagrama(self, diagram_id: UUID, user_id: UUID) -> RespuestaValidacionUML:
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(diagram_id))
        asegurar_participacion(self.members.obtener_participacion(diagram.project_id, user_id))
        model = self._construir_modelo_interno(diagram)
        errors, warnings, recommendations = validar_modelo_interno(model)
        return RespuestaValidacionUML(
            diagram_id=diagram_id,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations,
        )

    def exportar_diagrama_xmi(self, diagram_id: UUID, user_id: UUID) -> RespuestaExportacionXMI:
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(diagram_id))
        asegurar_participacion(self.members.obtener_participacion(diagram.project_id, user_id))
        content = exportar_xmi(self._construir_modelo_interno(diagram))
        file_name = f"{diagram.name.lower().replace(' ', '-')}.xml"
        self.uml.agregar_intercambio_xmi(
            IntercambioXMI(
                diagram_id=diagram_id,
                user_id=user_id,
                exchange_type="export",
                tool_name="Enterprise Architect",
                file_name=file_name,
                status="completed",
                metadata_json={"format": "xmi"},
            )
        )
        self.audit.record(
            module="modelado_uml",
            action="EXPORT_XMI",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"diagram_id": str(diagram_id), "file_name": file_name},
        )
        self.db.commit()
        return RespuestaExportacionXMI(diagram_id=diagram_id, file_name=file_name, content=content)

    def importar_diagrama_xmi(self, payload: SolicitudImportacionXMI, user_id: UUID) -> DiagramaUML:
        asegurar_permiso_proyecto(self.db, payload.project_id, user_id, "uml.edit")
        existing = self.uml.listar_diagramas_por_proyecto(payload.project_id)
        if existing:
            return self.importar_diagrama_xmi_en_existente(existing[0].id, payload, user_id)
        self._iniciar_mutacion(payload.project_id)
        model = importar_xmi(payload.content, payload.name)
        diagram = self._persistir_modelo_interno(model, payload.project_id, user_id)
        self.uml.agregar_intercambio_xmi(
            IntercambioXMI(
                diagram_id=diagram.id,
                user_id=user_id,
                exchange_type="import",
                tool_name=payload.tool_name,
                file_name=payload.file_name,
                status="completed",
                metadata_json={"class_count": len(model.classes)},
            )
        )
        self.audit.record(
            module="modelado_uml",
            action="IMPORT_XMI",
            user_id=user_id,
            project_id=payload.project_id,
            metadata={"diagram_id": str(diagram.id), "file_name": payload.file_name},
        )
        self.db.commit()
        self._actualizar(diagram)
        return diagram

    def importar_diagrama_xmi_en_existente(
        self, diagram_id: UUID, payload: SolicitudImportacionXMI, user_id: UUID
    ) -> DiagramaUML:
        diagram = asegurar_diagrama_existente(self.uml.obtener_diagrama(diagram_id))
        asegurar_permiso_proyecto(self.db, diagram.project_id, user_id, "uml.edit")
        if diagram.project_id != payload.project_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="El diagrama no pertenece al proyecto indicado",
            )
        self._iniciar_mutacion(diagram.project_id)
        model = importar_xmi(payload.content, payload.name)

        self.generations.eliminar_arbol_generacion_por_diagrama(diagram_id)
        self.uml.eliminar_elementos_visuales_por_diagrama(diagram_id)
        self.uml.eliminar_relaciones_por_diagrama(diagram_id)
        self.uml.eliminar_clases_por_diagrama(diagram_id)
        self.db.flush()

        diagram.name = payload.name
        diagram.diagram_type = model.diagram_type
        diagram.status = model.status
        diagram.current_version = model.current_version
        diagram.description = model.description
        diagram.metadata_json = {
            **diagram.metadata_json,
            **model.metadata_json,
            "imported_file_name": payload.file_name,
        }
        self._poblar_diagrama_existente_desde_modelo(diagram, model)
        self.uml.agregar_intercambio_xmi(
            IntercambioXMI(
                diagram_id=diagram.id,
                user_id=user_id,
                exchange_type="import",
                tool_name=payload.tool_name,
                file_name=payload.file_name,
                status="completed",
                metadata_json={"class_count": len(model.classes), "mode": "replace"},
            )
        )
        self.audit.record(
            module="modelado_uml",
            action="IMPORT_XMI_REPLACE_DIAGRAM",
            user_id=user_id,
            project_id=diagram.project_id,
            metadata={"diagram_id": str(diagram.id), "file_name": payload.file_name},
        )
        self.db.commit()
        self._actualizar(diagram)
        return diagram

    def generar_desde_instruccion(self, payload: SolicitudTextoAUML, user_id: UUID) -> DiagramaUML:
        asegurar_permiso_proyecto(self.db, payload.project_id, user_id, "uml.edit")
        self._iniciar_mutacion(payload.project_id)
        model = construir_uml_desde_texto(payload.prompt, payload.name)
        existing = self.uml.listar_diagramas_por_proyecto(payload.project_id)
        if existing:
            diagram = existing[0]
            self.generations.eliminar_arbol_generacion_por_diagrama(diagram.id)
            self.uml.eliminar_elementos_visuales_por_diagrama(diagram.id)
            self.uml.eliminar_relaciones_por_diagrama(diagram.id)
            self.uml.eliminar_clases_por_diagrama(diagram.id)
            self.db.flush()
            diagram.name = model.name
            diagram.diagram_type = model.diagram_type
            diagram.status = model.status
            diagram.current_version += 1
            diagram.description = model.description
            diagram.metadata_json = {
                **diagram.metadata_json,
                **model.metadata_json,
                "source_type": payload.source_type,
                "source_prompt": payload.prompt,
            }
            self._poblar_diagrama_existente_desde_modelo(diagram, model)
        else:
            diagram = self._persistir_modelo_interno(
                model,
                payload.project_id,
                user_id,
                metadata={"source_type": payload.source_type, "source_prompt": payload.prompt},
            )
        self.audit.record(
            module="modelado_uml",
            action="GENERATE_UML_FROM_SOURCE",
            user_id=user_id,
            project_id=payload.project_id,
            metadata={"diagram_id": str(diagram.id), "source_type": payload.source_type},
        )
        self.db.commit()
        self._actualizar(diagram)
        return diagram

    def restaurar_instantanea_proyecto(
        self, project_id: UUID, snapshot: dict, user_id: UUID
    ) -> list[UUID]:
        asegurar_participacion(self.members.obtener_participacion(project_id, user_id))
        try:
            snapshot_models = [
                ModeloDiagramaUML.model_validate(item) for item in snapshot.get("diagrams", [])
            ]
            desired_ids = [UUID(model.id) for model in snapshot_models if model.id]
            if len(desired_ids) != len(snapshot_models):
                raise ValueError("Todos los diagramas del snapshot deben tener identificador")
            if len(set(desired_ids)) != len(desired_ids):
                raise ValueError("El snapshot contiene diagramas duplicados")
            if any(
                model.project_id and UUID(model.project_id) != project_id
                for model in snapshot_models
            ):
                raise ValueError("El snapshot pertenece a otro proyecto")
        except (TypeError, ValueError, ValidationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="El snapshot de la version no es valido",
            ) from exc

        current_diagrams = {
            str(diagram.id): diagram for diagram in self.uml.listar_diagramas_por_proyecto(project_id)
        }
        snapshot_ids = {str(diagram_id) for diagram_id in desired_ids}

        for diagram_id, diagram in current_diagrams.items():
            self.generations.eliminar_arbol_generacion_por_diagrama(diagram.id)
            if diagram_id not in snapshot_ids:
                self.uml.eliminar_elementos_visuales_por_diagrama(diagram.id)
                self.uml.eliminar_relaciones_por_diagrama(diagram.id)
                self.uml.eliminar_clases_por_diagrama(diagram.id)
                self.uml.eliminar_intercambios_xmi_por_diagrama(diagram.id)
                self._desvincular_eventos_colaboracion(diagram.id)
                self.uml.eliminar_diagrama(diagram)

        self.db.flush()
        restored_ids: list[UUID] = []
        for model, desired_id in zip(snapshot_models, desired_ids, strict=True):
            diagram = current_diagrams.get(str(desired_id))
            if diagram is None:
                diagram = self.uml.agregar_diagrama(
                    DiagramaUML(
                        id=desired_id,
                        project_id=project_id,
                        created_by_user_id=user_id,
                        name=model.name,
                        diagram_type=model.diagram_type,
                        status=model.status,
                        current_version=model.current_version + 1,
                        description=model.description,
                        metadata_json=model.metadata_json,
                    )
                )
            else:
                previous_revision = diagram.current_version
                self.uml.eliminar_elementos_visuales_por_diagrama(diagram.id)
                self.uml.eliminar_relaciones_por_diagrama(diagram.id)
                self.uml.eliminar_clases_por_diagrama(diagram.id)
                self.db.flush()
                diagram.name = model.name
                diagram.diagram_type = model.diagram_type
                diagram.status = model.status
                diagram.current_version = previous_revision + 1
                diagram.description = model.description
                diagram.metadata_json = model.metadata_json

            self._poblar_diagrama_existente_desde_modelo(diagram, model)
            restored_ids.append(diagram.id)

        return restored_ids

    def _iniciar_mutacion(self, project_id: UUID) -> None:
        project = self.mutations.acquire(project_id)
        self.mutations.avanzar(project)
        marcar_proyecto_uml_para_sincronizar(self.db, project_id)

    def _actualizar(self, item) -> None:
        if not settings.nosql_consolidated_mode or isinstance(item, DiagramaUML):
            self.db.refresh(item)

    def _desvincular_eventos_colaboracion(self, diagram_id: UUID) -> None:
        self.db.execute(
            update(EventoColaboracion)
            .where(EventoColaboracion.diagram_id == diagram_id)
            .values(diagram_id=None)
        )

    def _construir_modelo_interno(self, diagram: DiagramaUML) -> ModeloDiagramaUML:
        if settings.nosql_consolidated_mode:
            return self.uml.model(diagram)
        return self.documents.modelo_para(self.db, diagram)

    def _construir_modelo_sql_interno(self, diagram: DiagramaUML) -> ModeloDiagramaUML:
        if settings.nosql_consolidated_mode:
            return self.uml.model(diagram)
        return construir_modelo_diagrama_sql(self.db, diagram)

    def _persistir_modelo_interno(
        self,
        model: ModeloDiagramaUML,
        project_id: UUID,
        user_id: UUID,
        metadata: dict | None = None,
    ) -> DiagramaUML:
        diagram = self.uml.agregar_diagrama(
            DiagramaUML(
                project_id=project_id,
                created_by_user_id=user_id,
                name=model.name,
                diagram_type=model.diagram_type,
                status=model.status,
                current_version=model.current_version,
                description=model.description,
                metadata_json={**model.metadata_json, **(metadata or {})},
            )
        )
        self._poblar_diagrama_existente_desde_modelo(diagram, model)
        return diagram

    def _poblar_diagrama_existente_desde_modelo(
        self, diagram: DiagramaUML, model: ModeloDiagramaUML
    ) -> None:
        id_by_external_ref: dict[str, UUID] = {}
        for uml_class_model in model.classes:
            uml_class = self.uml.agregar_clase(
                ClaseUML(
                    diagram_id=diagram.id,
                    name=uml_class_model.name,
                    visibility=uml_class_model.visibility,
                    element_type=uml_class_model.element_type,
                    stereotype=uml_class_model.stereotype,
                    description=uml_class_model.description,
                    metadata_json=uml_class_model.metadata_json,
                )
            )
            if uml_class_model.id:
                id_by_external_ref[uml_class_model.id] = uml_class.id
            id_by_external_ref[uml_class_model.name] = uml_class.id
            self.uml.agregar_elemento_visual(
                ElementoVisualUML(
                    diagram_id=diagram.id,
                    element_type="class",
                    element_id=uml_class.id,
                    position_x=uml_class_model.visual.x,
                    position_y=uml_class_model.visual.y,
                    width=uml_class_model.visual.width,
                    height=uml_class_model.visual.height,
                    style=uml_class_model.visual.style,
                )
            )
            for attribute_model in uml_class_model.attributes:
                self.uml.agregar_atributo(
                    AtributoUML(
                        class_id=uml_class.id, **attribute_model.model_dump(exclude={"id"})
                    )
                )
            for method_model in uml_class_model.methods:
                method = self.uml.agregar_metodo(
                    MetodoUML(
                        class_id=uml_class.id,
                        **method_model.model_dump(
                            exclude={"id", "parameters", "specification", "readiness"}
                        ),
                    )
                )
                if method_model.specification:
                    from app.modules.modelado_uml.models import EspecificacionMetodoUML
                    from app.modules.modelado_uml.schemas.especificacion_metodo import (
                        BaseEspecificacionMetodoUML,
                    )

                    try:
                        raw_values = dict(method_model.specification)
                        revision = max(1, int(raw_values.pop("revision", 1)))
                        raw_values.pop("readiness", None)
                        specification_values = BaseEspecificacionMetodoUML.model_validate(
                            raw_values
                        ).model_dump(mode="json")
                        specification_values["backend_contract"] = (
                            specification_values["backend_contract"] or {}
                        )
                        specification_values["frontend_contract"] = (
                            specification_values["frontend_contract"] or {}
                        )
                        self.uml.agregar_especificacion_metodo(
                            EspecificacionMetodoUML(
                                method_id=method.id,
                                revision=revision,
                                **specification_values,
                            )
                        )
                    except (TypeError, ValueError, ValidationError):
                        pass
                for parameter_model in method_model.parameters:
                    self.uml.agregar_parametro(
                        ParametroUML(
                            method_id=method.id, **parameter_model.model_dump(exclude={"id"})
                        )
                    )
        for relationship_model in model.relationships:
            source_id = id_by_external_ref.get(relationship_model.source_class_id)
            target_id = id_by_external_ref.get(relationship_model.target_class_id)
            if source_id and target_id:
                metadata_json = dict(relationship_model.metadata_json)
                association_class_id = metadata_json.get("association_class_id")
                if association_class_id in id_by_external_ref:
                    metadata_json["association_class_id"] = str(
                        id_by_external_ref[association_class_id]
                    )
                self.uml.agregar_relacion(
                    RelacionUML(
                        diagram_id=diagram.id,
                        source_class_id=source_id,
                        target_class_id=target_id,
                        relationship_type=relationship_model.relationship_type,
                        source_cardinality=relationship_model.source_cardinality,
                        target_cardinality=relationship_model.target_cardinality,
                        direction=relationship_model.direction,
                        label=relationship_model.label,
                        metadata_json=metadata_json,
                    )
                )
