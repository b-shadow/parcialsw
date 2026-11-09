import re
import unicodedata
from uuid import UUID

from ai_engine.context.contratos import ContextoIAProyecto
from ai_engine.inference.motor_local import MotorIALocal
from ai_engine.orchestration.contratos import (
    AccionPlanificada,
    IntencionDetectada,
    RecomendacionPlanificada,
    ResultadoIAUnificado,
)


def _normalized(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(character)
    )


class ProveedorReglas:
    """Fallback seguro que conserva y complementa el motor determinista existente."""

    def __init__(self, engine: MotorIALocal | None = None) -> None:
        self.engine = engine or MotorIALocal()

    def puede_preparar_atributos_recomendados(
        self, request_text: str, context: ContextoIAProyecto
    ) -> bool:
        if context.active_diagram is None:
            return False
        normalized = _normalized(request_text)
        if "mi criterio:" not in normalized or not self._solicita_resolver_recomendacion(normalized):
            return False
        actions, issues = self._planificar_cambios_recomendacion(normalized, context)
        return bool(actions) and not issues and all(
            action.action_type == "create_attribute" for action in actions
        )

    def puede_responder_con_contexto(
        self,
        request_text: str,
        context: ContextoIAProyecto,
        intents: list[IntencionDetectada],
    ) -> bool:
        intent_names = {item.name for item in intents}
        if "coordinate_team" in intent_names:
            return True
        if context.active_diagram is None:
            return False
        normalized_request = _normalized(request_text)
        if "modify_uml" in intent_names and self._solicita_resolver_recomendacion(
            normalized_request
        ):
            return True
        if "modify_uml" in intent_names and self._atributos_para_clase_existente(
            normalized_request, self._classes(context)
        ):
            return True
        if not intent_names & {"answer_question", "explain_uml", "recommend", "review_uml", "validate_uml"}:
            return False
        if "recommend" in intent_names:
            return True
        effective_request = self._resolver_seguimiento(request_text, context)
        normalized = _normalized(effective_request)
        diagram_terms = (
            "diagrama",
            "modelo",
            "clase",
            "atributo",
            "metodo",
            "relacion",
            "multiplicidad",
            "cardinalidad",
            "orientado",
            "como se ve",
            "opinas",
            "correcto",
        )
        return any(term in normalized for term in diagram_terms)

    def complete(
        self,
        request_text: str,
        context: ContextoIAProyecto,
        intents: list[IntencionDetectada],
    ) -> ResultadoIAUnificado:
        normalized = _normalized(request_text)
        intent_names = {item.name for item in intents}
        actions: list[AccionPlanificada] = []
        recommendations: list[RecomendacionPlanificada] = []
        warnings: list[str] = []
        unresolved_recommendations: list[str] = []
        resolves_recommendations = self._solicita_resolver_recomendacion(normalized)

        if intent_names & {"recommend", "review_uml", "validate_uml"} and not resolves_recommendations:
            recommendations.extend(self._revisar(context))
        if "modify_uml" in intent_names:
            if resolves_recommendations:
                planned, unresolved_recommendations = self._planificar_cambios_recomendacion(
                    normalized, context
                )
                actions.extend(planned)
            else:
                actions.extend(self._planificar_cambios_uml(normalized, context))
        if "specify_method" in intent_names:
            action = self._plan_method_specification(normalized, context)
            if action:
                actions.append(action)
        if "prepare_generation" in intent_names:
            if "spring" in normalized or "backend" in normalized:
                actions.append(
                    AccionPlanificada(
                        order=len(actions) + 1,
                        action_type="prepare_backend_generation",
                        target_type="project",
                        target_id=context.project.id,
                        payload={},
                        explanation="Preparar generacion Spring Boot.",
                    )
                )
            if "flutter" in normalized or "frontend" in normalized:
                actions.append(
                    AccionPlanificada(
                        order=len(actions) + 1,
                        action_type="prepare_flutter_generation",
                        target_type="project",
                        target_id=context.project.id,
                        payload={},
                        explanation="Preparar generacion Flutter.",
                    )
                )

        for index, action in enumerate(actions, start=1):
            action.order = index
        unsupported = not actions and not recommendations and intent_names == {"unknown"}
        if unsupported:
            warnings.append("El proveedor Ollama no esta disponible y la regla local no cubre la solicitud.")
        answer = self._answer(
            request_text,
            context,
            intent_names,
            actions,
            recommendations,
            unsupported,
            unresolved_recommendations,
        )
        return ResultadoIAUnificado(
            answer=answer,
            detected_intents=intents,
            actions=actions,
            recommendations=recommendations,
            warnings=warnings,
            provider="rule_engine",
            model="deterministic-v2",
            fallback_used=True,
            requires_user_input=bool(unresolved_recommendations and not actions),
            clarification_question=(
                "Indica como deseas resolver: " + ", ".join(unresolved_recommendations)
                if unresolved_recommendations and not actions
                else None
            ),
        )

    def __getattr__(self, name: str):
        return getattr(self.engine, name)

    def _answer(
        self,
        request_text: str,
        context: ContextoIAProyecto,
        intents: set[str],
        actions: list[AccionPlanificada],
        recommendations: list[RecomendacionPlanificada],
        unsupported: bool,
        unresolved_recommendations: list[str],
    ) -> str:
        if self._solicita_resolver_recomendacion(_normalized(request_text)):
            unresolved = ", ".join(unresolved_recommendations)
            if actions:
                suffix = (
                    f" No improvise las recomendaciones que requieren una decision: {unresolved}."
                    if unresolved
                    else ""
                )
                return (
                    f"Prepare {len(actions)} correccion(es) seguras como propuesta. "
                    "Revisalas y pulsa Aplicar para modificar el diagrama."
                    f"{suffix}"
                )
            if unresolved:
                if "mi criterio:" in _normalized(request_text):
                    return (
                        "Recibí tu criterio, pero el motor local de reglas no puede convertir "
                        "esta recomendación en cambios UML seguros. Conecta el modelo de IA "
                        "configurado o aplica el cambio en el editor. No modifiqué el diagrama."
                    )
                return (
                    "No marque la recomendacion como resuelta ni modifique el diagrama porque "
                    f"requiere una decision concreta: {unresolved}. Indica el criterio que deseas "
                    "usar y preparare el cambio para confirmarlo."
                )
            return "No encontré un cambio pendiente para esa recomendación en el diagrama actual."
        if "coordinate_team" in intents:
            return self._respuesta_coordinacion_equipo(context)
        if "summarize_conversation" in intents:
            if context.conversation_summary:
                return f"Resumen de la conversación: {context.conversation_summary}"
            recent = [
                item.content.strip()
                for item in context.recent_messages
                if item.role in {"user", "assistant"} and item.content.strip()
            ][-4:]
            return (
                "En los últimos mensajes se habló de: " + "; ".join(recent)
                if recent else "Todavía no hay mensajes previos para resumir en este chat."
            )
        if "summarize_project" in intents:
            diagram = context.active_diagram
            summary = f"El proyecto {context.project.name}"
            if context.project.description:
                summary += f" tiene como objetivo: {context.project.description}."
            else:
                summary += " no tiene una descripción registrada."
            if diagram:
                summary += (
                    f" Su diagrama {diagram.name} contiene {len(diagram.classes)} "
                    f"clases y {len(diagram.relationships)} relaciones."
                )
            return summary
        if "explain_system" in intents:
            return (
                "En Proyectos abre el editor para consultar o modificar el diagrama. "
                "En el asistente puedes pedir explicaciones, mejoras o cambios; los cambios "
                "aparecen como propuestas y solo se aplican al confirmarlos. "
                "La generación de Spring Boot o Flutter se inicia desde Generación."
            )
        if {"explain_uml", "answer_question", "recommend", "review_uml", "validate_uml"} & intents:
            return self._respuesta_uml_contextual(
                request_text, context, intents, actions, recommendations
            )
        if unsupported:
            return (
                "No pude interpretar esa solicitud con suficiente precision. Puedes preguntarme "
                "por las clases y relaciones del diagrama o solicitar un cambio concreto."
            )
        parts: list[str] = []
        if recommendations:
            parts.append(f"Prepare {len(recommendations)} recomendacion(es) para revisar el modelo.")
        if actions:
            parts.append(
                f"Preparé {len(actions)} cambio(s) como propuesta. Revísalos y confirma cada uno para aplicarlos."
            )
        if not parts:
            parts.append(
                "No pude preparar un cambio concreto con esa indicación. "
                "Nombra la clase, el atributo, el método o la relación que quieres modificar."
            )
        return " ".join(parts)

    @staticmethod
    def _solicita_resolver_recomendacion(text: str) -> bool:
        resolution_terms = (
            "recomendacion", "recomendaciones", "sugerencia", "sugerencias",
            "mejora", "mejoras", "observacion", "observaciones", "lo que me dijiste",
            "lo que me dijo", "lo recomendado", "todo lo anterior",
        )
        action_terms = (
            "corrige", "aplica", "implementa", "resuelve", "resolver", "soluciona",
        )
        return any(item in text for item in resolution_terms) and any(
            item in text for item in action_terms
        )

    def _planificar_cambios_recomendacion(
        self, text: str, context: ContextoIAProyecto
    ) -> tuple[list[AccionPlanificada], list[str]]:
        diagram = context.active_diagram
        if diagram is None:
            return [], ["abre primero el diagrama que deseas corregir"]
        raw_items = context.generation_state.get("pending_recommendations") or []
        pending = [item for item in raw_items if isinstance(item, dict)]
        selected_id = re.search(r"\bid de recomendacion:\s*([0-9a-f-]{36})\b", text)
        if selected_id:
            explicitly_selected = [
                item for item in pending if str(item.get("id")) == selected_id.group(1)
            ]
            if not explicitly_selected:
                return [], ["la recomendación seleccionada ya no está abierta"]
        else:
            explicitly_selected = [
                item for item in pending
                if _normalized(str(item.get("title") or "")) in text
            ]
            if len(explicitly_selected) > 1:
                explicitly_selected = [
                    item for item in explicitly_selected
                    if _normalized(str(item.get("description") or "")) in text
                ]
            if len(explicitly_selected) > 1:
                return [], ["identifica una sola recomendación antes de corregirla"]
        selected = explicitly_selected or pending
        if not selected:
            return [], ["no hay recomendaciones abiertas que pueda relacionar con la orden"]

        actions: list[AccionPlanificada] = []
        unresolved: list[str] = []
        selected_titles = {_normalized(str(item.get("title") or "")) for item in selected}
        if "identificadores ausentes" in selected_titles:
            for uml_class in diagram.classes:
                attributes = [
                    item for item in uml_class.get("attributes", []) if isinstance(item, dict)
                ]
                if any(str(item.get("name", "")).casefold() == "id" for item in attributes):
                    continue
                actions.append(
                    AccionPlanificada(
                        order=len(actions) + 1,
                        action_type="create_attribute",
                        target_type="uml_attribute",
                        diagram_id=diagram.id,
                        base_diagram_version=diagram.current_version,
                        depends_on=[actions[-1].id] if actions else [],
                        payload={
                            "class_id": str(uml_class.get("id")),
                            "name": "id",
                            "data_type": "UUID",
                            "is_required": True,
                            "constraints": {"primary_key": True, "unique": True},
                        },
                        explanation=f"Agregar el identificador UUID a {uml_class.get('name')}.",
                    )
                )

        for item in selected:
            if _normalized(str(item.get("title") or "")) != "sugerencia de diseno":
                continue
            planned, issue = self._atributos_de_criterio(item, text, diagram)
            actions.extend(planned)
            if issue:
                unresolved.append(issue)

        non_automatic = {
            "clases sin estado definido": "define los atributos esenciales de cada clase vacia",
            "estados controlados": "elige los valores permitidos para cada estado",
            "reglas para calificaciones": "define la escala valida y la nota de aprobacion",
            "modelo desconectado": "indica que clases se relacionan y sus multiplicidades",
            "multiplicidades incompletas": "indica las multiplicidades correctas de cada extremo",
            "unicidad de la clase asociativa": "confirma que combinacion de referencias debe ser unica",
            "completar reglas del dominio": "indica las reglas de negocio que deben cumplir los metodos",
        }
        for title in selected_titles:
            if title in non_automatic:
                unresolved.append(non_automatic[title])
        return actions, unresolved

    def _atributos_de_criterio(
        self, recommendation: dict, text: str, diagram
    ) -> tuple[list[AccionPlanificada], str | None]:
        description = _normalized(str(recommendation.get("description") or ""))
        target = re.fullmatch(
            r"\s*(?:agregar|agrega|anadir|anade)\s+(?:los\s+)?atributos?\s+"
            r"(?:a|en|para)\s+(?:la\s+clase\s+)?([a-z][a-z0-9_]*)\s*\.?\s*",
            description,
        )
        if target is None:
            return [], "la sugerencia no identifica una clase para agregar atributos"
        uml_class = self._buscar_clase(diagram.classes, target.group(1))
        if uml_class is None or self._uuid(uml_class.get("id")) is None:
            return [], "la clase indicada por la sugerencia ya no existe"
        criterion = re.search(r"\bmi criterio:\s*([^\r\n]+)", text)
        if criterion is None:
            return [], f"indica los nombres y tipos de los atributos de {uml_class['name']}"
        value = criterion.group(1).strip()
        supported = r"uuid|string|char|int|integer|long|double|decimal|boolean|bool|date|datetime"
        pattern = re.compile(
            rf"\b([a-z][a-z0-9_]*)\s+(?:con\s+valor\s+|de\s+tipo\s+|tipo\s+|:\s*)"
            rf"({supported})\b"
        )
        matches = list(pattern.finditer(value))
        rest = pattern.sub("", value)
        rest = re.sub(r"\b(?:anade|agrega|incluye|los|las|atributos?|campos?|y)\b|[\s,.;:]+", "", rest)
        if not matches or rest or len(matches) > 20:
            return [], "escribe cada atributo como 'nombre con valor String' y separa los demás con comas"
        canonical = {
            "uuid": "UUID", "string": "String", "char": "String", "int": "Integer",
            "integer": "Integer", "long": "Long", "double": "Double",
            "decimal": "Double", "boolean": "Boolean", "bool": "Boolean",
            "date": "Date", "datetime": "DateTime",
        }
        existing = {
            str(attribute.get("name", "")).casefold(): str(attribute.get("data_type", "")).casefold()
            for attribute in uml_class.get("attributes", []) if isinstance(attribute, dict)
        }
        requested: dict[str, str] = {}
        for match in matches:
            name, data_type = match.groups()
            normalized_type = canonical[data_type]
            if name in requested and requested[name] != normalized_type:
                return [], f"el atributo {name} tiene dos tipos distintos en tu criterio"
            if name in existing and existing[name] != normalized_type.casefold():
                return [], f"el atributo {name} ya existe con otro tipo en {uml_class['name']}"
            requested[name] = normalized_type

        actions: list[AccionPlanificada] = []
        for name, data_type in requested.items():
            if name in existing:
                continue
            actions.append(
                AccionPlanificada(
                    order=len(actions) + 1,
                    action_type="create_attribute",
                    target_type="uml_attribute",
                    diagram_id=diagram.id,
                    base_diagram_version=diagram.current_version,
                    depends_on=[actions[-1].id] if actions else [],
                    payload={
                        "class_id": str(uml_class["id"]), "name": name, "data_type": data_type,
                    },
                    explanation=f"Agregar {name}: {data_type} a {uml_class['name']}.",
                )
            )
        if not actions:
            return [], f"los atributos solicitados ya existen en {uml_class['name']}"
        return actions, None

    def _respuesta_coordinacion_equipo(self, context: ContextoIAProyecto) -> str:
        if not context.team_activity:
            return "No hay actividad reciente registrada en el equipo."

        lines: list[str] = []
        for item in context.team_activity:
            if item.actions:
                actions_str = "; ".join(item.actions)
                lines.append(f"{item.display_name}: {actions_str}")
            else:
                lines.append(f"{item.display_name}: sin actividad reciente registrada.")

        known_classes: set[str] = set()
        if context.active_diagram and context.active_diagram.classes:
            for cls in context.active_diagram.classes:
                cname = cls.get("name") if isinstance(cls, dict) else getattr(cls, "name", None)
                if cname:
                    known_classes.add(cname)

        class_to_members: dict[str, set[str]] = {}
        for item in context.team_activity:
            all_text = " ".join(item.actions)
            for cname in known_classes:
                if re.search(rf"\b{re.escape(cname)}\b", all_text, re.IGNORECASE):
                    class_to_members.setdefault(cname, set()).add(item.display_name)
            words = set(re.findall(r"\b[A-Z][a-zA-Z0-9_]{2,}\b", all_text))
            stopwords = {"UML", "JPA", "DTO", "DAO", "REST", "API", "SQL", "CRUD", item.display_name}
            for word in words:
                if word not in stopwords:
                    class_to_members.setdefault(word, set()).add(item.display_name)

        shared_classes = [
            cname for cname, members in class_to_members.items() if len(members) >= 2
        ]

        if shared_classes:
            classes_str = ", ".join(sorted(shared_classes))
            suggestion = (
                f"Sugerencia de coordinación: dos o más integrantes tocaron la misma clase ({classes_str}). "
                "Se sugiere coordinarse y repartir el trabajo para evitar conflictos de edición."
            )
            return "\n".join(lines) + f"\n\n{suggestion}"

        return "\n".join(lines)

    def _respuesta_uml_contextual(
        self,
        request_text: str,
        context: ContextoIAProyecto,
        intents: set[str],
        actions: list[AccionPlanificada],
        recommendations: list[RecomendacionPlanificada],
    ) -> str:
        diagram = context.active_diagram
        if diagram is None:
            return (
                "No tengo un diagrama activo en este contexto. Abre un diagrama y vuelve a "
                "preguntarme para poder analizar sus clases y relaciones concretas."
            )
        if not diagram.classes:
            return f"El diagrama {diagram.name} esta vacio; todavia no hay clases que analizar."

        effective_request = self._resolver_seguimiento(request_text, context)
        normalized = _normalized(effective_request)
        if "recommend" in intents:
            if not recommendations:
                return (
                    "Revise el diagrama como evaluacion tecnica, pero no encontre una mejora "
                    "concreta y segura que recomendar con la informacion disponible."
                )
            detail = "\n".join(
                f"{index}. [{self._prioridad_recomendacion(item.severity)}] "
                f"{item.title}: {item.description}"
                for index, item in enumerate(recommendations, start=1)
            )
            relationship_text = (
                f" y {len(diagram.relationships)} relaciones principales"
                if diagram.relationships
                else ""
            )
            return (
                f"El modelo tiene una base clara: representa {len(diagram.classes)} "
                f"clases{relationship_text}.\n\n"
                "Como retroalimentacion de profesor, estas son las mejoras que "
                f"priorizaria:\n{detail}\n\nNo aplique cambios; son recomendaciones "
                "para que decidas cuales incorporar."
            )
        classes_by_id = {
            str(item.get("id")): item for item in diagram.classes if item.get("id")
        }
        class_names = [str(item.get("name") or "Clase sin nombre") for item in diagram.classes]
        relationship_descriptions = self._describir_relaciones(
            diagram.relationships, classes_by_id
        )
        answer_parts = [
            (
                f"El diagrama {diagram.name} se ve orientado a "
                f"{self._inferir_orientacion(class_names)}."
            ),
            self._describir_clases(diagram.classes),
        ]
        if relationship_descriptions:
            answer_parts.append(
                "En las relaciones se observa " + "; ".join(relationship_descriptions) + "."
            )
        else:
            answer_parts.append(
                "No hay relaciones registradas entre las clases, asi que el dominio aun esta desconectado."
            )

        review_phrases = (
            "opinas",
            "opinion",
            "como se ve",
            "esta bien",
            "correcto",
            "revisa",
            "analiza",
            "orientado",
            "entonces",
        )
        if any(phrase in normalized for phrase in review_phrases):
            answer_parts.append(
                self._observacion_calidad(diagram.classes, diagram.relationships)
            )
        if recommendations:
            answer_parts.append(recommendations[0].description)
        if actions:
            answer_parts.append(
                f"Tambien prepare {len(actions)} cambio(s) como propuesta; no se aplicaron automaticamente."
            )
        return " ".join(part for part in answer_parts if part)

    @staticmethod
    def _prioridad_recomendacion(severity: str) -> str:
        normalized = severity.strip().lower()
        if normalized in {"critical", "error"}:
            return "urgente"
        if normalized == "warning":
            return "prioridad alta"
        return "prioridad media"

    @staticmethod
    def _resolver_seguimiento(request_text: str, context: ContextoIAProyecto) -> str:
        normalized = _normalized(request_text).strip(" ?.!")
        follow_ups = {
            "entonces",
            "y entonces",
            "y eso",
            "que opinas",
            "continua",
            "explicame mas",
        }
        if normalized not in follow_ups:
            return request_text
        for message in reversed(context.recent_messages):
            if message.role == "user" and _normalized(message.content) != _normalized(request_text):
                return f"{message.content} {request_text}"
        return request_text

    @staticmethod
    def _describir_clases(classes: list[dict]) -> str:
        details: list[str] = []
        for item in classes[:8]:
            name = str(item.get("name") or "Clase sin nombre")
            attributes = [
                str(attribute.get("name"))
                for attribute in item.get("attributes", [])
                if isinstance(attribute, dict) and attribute.get("name")
            ]
            methods = [
                str(method.get("name"))
                for method in item.get("methods", [])
                if isinstance(method, dict) and method.get("name")
            ]
            description = name
            if attributes:
                description += f" contiene {', '.join(attributes[:6])}"
            if methods:
                description += f" y ofrece {', '.join(methods[:4])}"
            details.append(description)
        suffix = "" if len(classes) <= 8 else f", entre otras {len(classes) - 8} clases"
        return f"Actualmente hay {len(classes)} clases: " + "; ".join(details) + suffix + "."

    @staticmethod
    def _describir_relaciones(
        relationships: list[dict], classes_by_id: dict[str, dict]
    ) -> list[str]:
        descriptions: list[str] = []
        for relation in relationships[:8]:
            source = classes_by_id.get(str(relation.get("source_class_id")), {})
            target = classes_by_id.get(str(relation.get("target_class_id")), {})
            source_name = str(source.get("name") or "una clase")
            target_name = str(target.get("name") or "otra clase")
            source_cardinality = relation.get("source_cardinality") or "sin multiplicidad"
            target_cardinality = relation.get("target_cardinality") or "sin multiplicidad"
            label = f" ({relation.get('label')})" if relation.get("label") else ""
            text = (
                f"{source_name} {source_cardinality} con {target_name} "
                f"{target_cardinality}{label}"
            )
            metadata = relation.get("metadata_json") or {}
            association_id = metadata.get("association_class_id") if isinstance(metadata, dict) else None
            association_class = classes_by_id.get(str(association_id)) if association_id else None
            if association_class:
                text += f", mediante la clase asociativa {association_class.get('name')}"
            descriptions.append(text)
        return descriptions

    @staticmethod
    def _observacion_calidad(classes: list[dict], relationships: list[dict]) -> str:
        without_attributes = [
            str(item.get("name") or "Clase sin nombre")
            for item in classes
            if not item.get("attributes")
        ]
        without_id = [
            str(item.get("name") or "Clase sin nombre")
            for item in classes
            if not any(
                str(attribute.get("name", "")).casefold() == "id"
                for attribute in item.get("attributes", [])
                if isinstance(attribute, dict)
            )
        ]
        observations: list[str] = []
        if relationships:
            observations.append("la estructura principal esta conectada")
        if without_attributes:
            observations.append("faltan atributos en " + ", ".join(without_attributes[:5]))
        if without_id:
            observations.append(
                "conviene revisar identificadores en " + ", ".join(without_id[:5])
            )
        if not observations:
            return "Como base, el modelo es coherente y no presenta omisiones estructurales basicas."
        return "Como evaluacion: " + "; ".join(observations) + "."

    @staticmethod
    def _inferir_orientacion(class_names: list[str]) -> str:
        names = {_normalized(name) for name in class_names}
        domains = (
            (
                {"estudiante", "curso", "inscripcion", "matricula", "docente"},
                "un sistema academico de cursos e inscripciones",
            ),
            (
                {"venta", "producto", "cliente", "detalleventa", "factura"},
                "un sistema comercial de ventas y productos",
            ),
            (
                {"usuario", "prestamo", "libro", "autor"},
                "un sistema de biblioteca y prestamos",
            ),
            (
                {"paciente", "medico", "consulta", "cita"},
                "un sistema de gestion clinica",
            ),
            (
                {"pedido", "producto", "cliente", "detallepedido"},
                "un sistema de pedidos",
            ),
        )
        best_label = "un dominio centrado en " + ", ".join(class_names[:4])
        best_score = 0
        for vocabulary, label in domains:
            score = len(names & vocabulary)
            if score > best_score:
                best_score = score
                best_label = label
        return best_label

    @staticmethod
    def _classes(context: ContextoIAProyecto) -> list[dict]:
        return context.active_diagram.classes if context.active_diagram else []

    def _revisar(self, context: ContextoIAProyecto) -> list[RecomendacionPlanificada]:
        classes = self._classes(context)
        if not classes:
            return [
                RecomendacionPlanificada(
                    category="uml_quality",
                    severity="warning",
                    title="Diagrama sin clases",
                    description="Agrega al menos una clase antes de revisar la estructura del dominio.",
                )
            ]
        recommendations: list[RecomendacionPlanificada] = []
        without_id = [
            item.get("name", "Clase")
            for item in classes
            if str(item.get("element_type") or "class").casefold() == "class"
            if not any(
                str(attribute.get("name", "")).casefold() == "id"
                for attribute in item.get("attributes", [])
                if isinstance(attribute, dict)
            )
        ]
        if without_id:
            recommendations.append(
                RecomendacionPlanificada(
                    category="uml_quality",
                    severity="warning",
                    title="Identificadores ausentes",
                    description=(
                        f"Agrega un identificador estable a {', '.join(without_id[:10])}; "
                        "sin el sera dificil persistir, relacionar y generar operaciones CRUD confiables."
                    ),
                )
            )

        without_attributes = [
            str(item.get("name") or "Clase")
            for item in classes
            if str(item.get("element_type") or "class").casefold() == "class"
            and not item.get("attributes")
        ]
        if without_attributes:
            recommendations.append(
                RecomendacionPlanificada(
                    category="uml_quality",
                    severity="warning",
                    title="Clases sin estado definido",
                    description=(
                        f"Define los atributos esenciales de {', '.join(without_attributes[:10])}; "
                        "una clase vacia no permite validar bien su responsabilidad ni generar formularios utiles."
                    ),
                )
            )

        string_states: list[str] = []
        numeric_grades: list[str] = []
        for uml_class in classes:
            class_name = str(uml_class.get("name") or "Clase")
            for attribute in uml_class.get("attributes", []):
                if not isinstance(attribute, dict):
                    continue
                attribute_name = str(attribute.get("name") or "")
                attribute_type = str(attribute.get("data_type") or attribute.get("type") or "")
                normalized_name = _normalized(attribute_name)
                normalized_type = _normalized(attribute_type)
                if normalized_name in {"estado", "status", "tipo"} and normalized_type in {"string", "texto", "str"}:
                    string_states.append(f"{class_name}.{attribute_name}")
                if any(term in normalized_name for term in ("nota", "calificacion", "puntaje")):
                    numeric_grades.append(f"{class_name}.{attribute_name}")

        if string_states:
            recommendations.append(
                RecomendacionPlanificada(
                    category="architecture",
                    severity="info",
                    title="Estados controlados",
                    description=(
                        f"Convierte {', '.join(string_states[:8])} en una enumeracion o catalogo de "
                        "valores permitidos para evitar estados escritos de formas incompatibles."
                    ),
                )
            )
        if numeric_grades:
            recommendations.append(
                RecomendacionPlanificada(
                    category="method_specification",
                    severity="warning",
                    title="Reglas para calificaciones",
                    description=(
                        f"Especifica rango, precision y reglas de aprobacion para {', '.join(numeric_grades[:8])}; "
                        "el tipo numerico por si solo no impide notas invalidas."
                    ),
                )
            )

        diagram = context.active_diagram
        relationships = diagram.relationships if diagram else []
        if len(classes) > 1 and not relationships:
            recommendations.append(
                RecomendacionPlanificada(
                    category="uml_quality",
                    severity="warning",
                    title="Modelo desconectado",
                    description="Relaciona las clases que colaboran e indica multiplicidades en ambos extremos.",
                )
            )
        else:
            missing_multiplicity = [
                relation for relation in relationships
                if not relation.get("source_cardinality") or not relation.get("target_cardinality")
            ]
            if missing_multiplicity:
                recommendations.append(
                    RecomendacionPlanificada(
                        category="uml_quality",
                        severity="warning",
                        title="Multiplicidades incompletas",
                        description=(
                            f"Completa las multiplicidades de {len(missing_multiplicity)} relacion(es); "
                            "esto determina claves foraneas, obligatoriedad y colecciones en el codigo generado."
                        ),
                    )
                )

        association_classes: list[str] = []
        classes_by_id = {str(item.get("id")): item for item in classes if item.get("id")}
        for relation in relationships:
            metadata = relation.get("metadata_json") or {}
            association_id = metadata.get("association_class_id") if isinstance(metadata, dict) else None
            association = classes_by_id.get(str(association_id)) if association_id else None
            if association:
                association_classes.append(str(association.get("name") or "Clase asociativa"))
        if association_classes:
            recommendations.append(
                RecomendacionPlanificada(
                    category="architecture",
                    severity="info",
                    title="Unicidad de la clase asociativa",
                    description=(
                        f"Define una regla de unicidad para {', '.join(association_classes[:5])} usando "
                        "las referencias de sus dos extremos; asi evitaras asociaciones duplicadas."
                    ),
                )
            )

        if not recommendations:
            recommendations.append(
                RecomendacionPlanificada(
                    category="uml_quality",
                    severity="info",
                    title="Completar reglas del dominio",
                    description=(
                        "La estructura basica es coherente. El siguiente paso es especificar precondiciones, "
                        "validaciones, resultados y errores de los metodos antes de generar backend y Flutter."
                    ),
                )
            )
        return recommendations[:6]

    def _planificar_cambios_uml(
        self, text: str, context: ContextoIAProyecto
    ) -> list[AccionPlanificada]:
        classes = self._classes(context)
        diagram = context.active_diagram
        if diagram is None:
            return []
        if re.search(r"\b(borra|elimina|quita)\s+(todas|las)\s+(clases|tablas)", text):
            return [
                AccionPlanificada(
                    order=index,
                    action_type="delete_class",
                    target_type="uml_class",
                    target_id=self._uuid(item.get("id")),
                    target_name=str(item.get("name")),
                    diagram_id=diagram.id,
                    base_diagram_version=diagram.current_version,
                    payload={},
                    risk_level="high",
                    requires_confirmation=True,
                    explanation=f"Eliminar la clase {item.get('name')}.",
                )
                for index, item in enumerate(classes, start=1)
                if self._uuid(item.get("id"))
            ]

        actions: list[AccionPlanificada] = []
        create_matches = list(re.finditer(
            r"\b(?:crea|agrega|anade|incluye)\s+(?:una\s+)?(?:clase|tabla|entidad)\s+([a-z][a-z0-9_]*)",
            text,
        ))
        created_names: list[str] = []
        class_action_ids: dict[str, UUID] = {}
        for create_match in create_matches:
            created_name = self._pascal(create_match.group(1))
            if created_name.casefold() in {item.casefold() for item in created_names}:
                continue
            created_names.append(created_name)
            if self._buscar_clase(classes, created_name):
                continue
            class_action = AccionPlanificada(
                order=len(actions) + 1,
                action_type="create_class",
                target_type="uml_class",
                target_name=created_name,
                diagram_id=diagram.id,
                base_diagram_version=diagram.current_version,
                payload={"name": created_name},
                explanation=f"Crear la clase {created_name}.",
            )
            actions.append(class_action)
            class_action_ids[created_name.casefold()] = class_action.id
            attributes = self._atributos_despues_clase(text, create_match.end())
            for attribute_name, data_type in attributes:
                actions.append(
                    AccionPlanificada(
                        order=len(actions) + 1,
                        action_type="create_attribute",
                        target_type="uml_attribute",
                        diagram_id=diagram.id,
                        base_diagram_version=diagram.current_version,
                        payload={
                            "class_name": created_name,
                            "name": attribute_name,
                            "data_type": data_type,
                        },
                        depends_on=[class_action.id],
                        explanation=f"Agregar {attribute_name} a {created_name}.",
                    )
                )

        attribute_request = self._atributos_para_clase_existente(text, classes)
        if attribute_request:
            target_class, attributes = attribute_request
            existing_names = {
                str(item.get("name", "")).casefold()
                for item in target_class.get("attributes", [])
                if isinstance(item, dict)
            }
            for attribute_name, data_type in attributes:
                if attribute_name.casefold() in existing_names:
                    continue
                actions.append(
                    AccionPlanificada(
                        order=len(actions) + 1,
                        action_type="create_attribute",
                        target_type="uml_attribute",
                        diagram_id=diagram.id,
                        base_diagram_version=diagram.current_version,
                        payload={
                            "class_id": str(target_class["id"]),
                            "name": attribute_name,
                            "data_type": data_type,
                            "is_required": attribute_name.casefold() == "id",
                        },
                        depends_on=[actions[-1].id] if actions else [],
                        explanation=f"Agregar {attribute_name}: {data_type} a {target_class['name']}.",
                    )
                )
                existing_names.add(attribute_name.casefold())

        relation_requested = any(
            marker in text for marker in ("conecta", "relaciona", "asocia", "vincula", "uno a uno", "1 a 1")
        )
        if relation_requested:
            explicit_relation = re.search(
                r"\b(?:conecta|relaciona|asocia|vincula)\s+(?:la\s+clase\s+)?"
                r"([a-z][a-z0-9_]*)\s+(?:con|a)\s+(?:la\s+clase\s+)?([a-z][a-z0-9_]*)",
                text,
            )
            mentioned = [
                item for item in classes if str(item.get("name", "")).casefold() in text
            ]
            source_name = (
                self._pascal(explicit_relation.group(1))
                if explicit_relation
                else (created_names[0] if created_names else None)
            ) or (str(mentioned[0].get("name")) if mentioned else None)
            target_candidates = [
                str(item.get("name"))
                for item in mentioned
                if str(item.get("name")).casefold() != (source_name or "").casefold()
            ]
            target_name = (
                self._pascal(explicit_relation.group(2)) if explicit_relation else None
            ) or (target_candidates[0] if target_candidates else self._destino_despues_de_con(text, classes))
            if source_name and target_name:
                dependency = [
                    class_action_ids[name.casefold()]
                    for name in (source_name, target_name)
                    if name.casefold() in class_action_ids
                ]
                source_cardinality, target_cardinality = self._cardinalidades(text)
                actions.append(
                    AccionPlanificada(
                        order=len(actions) + 1,
                        action_type="create_relationship",
                        target_type="uml_relationship",
                        diagram_id=diagram.id,
                        base_diagram_version=diagram.current_version,
                        payload={
                            "source_class_name": source_name,
                            "target_class_name": target_name,
                            "relationship_type": "association",
                            "source_cardinality": source_cardinality,
                            "target_cardinality": target_cardinality,
                        },
                        depends_on=dependency,
                        explanation=f"Relacionar {source_name} con {target_name}.",
                    )
                )
        return actions

    @staticmethod
    def _atributos_despues_clase(text: str, start: int) -> list[tuple[str, str]]:
        tail = text[start:]
        match = re.match(
            r"\s+con\s+(?:los\s+)?atributos?\s+(.+?)"
            r"(?=\s+(?:y\s+)?(?:crea|agrega|anade|conecta|relaciona|genera)\b|$)",
            tail,
        )
        if not match:
            return []
        supported = r"uuid|string|char|int|integer|long|double|decimal|boolean|bool|date|datetime"
        pairs = re.findall(
            rf"\b([a-z][a-z0-9_]*)\s+(?:que\s+)?(?:es\s+|de\s+tipo\s+)?({supported})\b",
            match.group(1),
        )
        aliases = {"integer": "int", "bool": "boolean"}
        return [(name, aliases.get(data_type, data_type)) for name, data_type in pairs]

    @classmethod
    def _atributos_para_clase_existente(
        cls, text: str, classes: list[dict]
    ) -> tuple[dict, list[tuple[str, str]]] | None:
        target = re.search(
            r"\b(?:a|en|para)\s+(?:(?:la|el)\s+)?(?:clase|tabla|entidad)\s+([a-z][a-z0-9_]*)\b",
            text,
        )
        if not target or not re.search(r"\b(?:agrega|anade|pon|ponle|incluye)\b", text):
            return None
        uml_class = cls._buscar_clase(classes, target.group(1))
        if uml_class is None or cls._uuid(uml_class.get("id")) is None:
            return None
        supported = r"uuid|string|char|int|integer|long|double|decimal|boolean|bool|date|datetime"
        pairs = re.findall(
            rf"\b([a-z][a-z0-9_]*)\s+(?:con\s+valor\s+|de\s+tipo\s+|tipo\s+|:\s*|es\s+)?({supported})\b",
            text[:target.start()],
        )
        aliases = {"integer": "Integer", "int": "Integer", "bool": "Boolean"}
        canonical = {
            "uuid": "UUID", "string": "String", "char": "String", "long": "Long",
            "double": "Double", "decimal": "Double", "boolean": "Boolean",
            "date": "Date", "datetime": "DateTime",
        }
        attributes = [
            (name, aliases.get(data_type, canonical.get(data_type, data_type)))
            for name, data_type in pairs
            if name not in {"atributo", "atributos", "campo", "campos"}
        ]
        return (uml_class, attributes) if attributes else None

    @staticmethod
    def _cardinalidades(text: str) -> tuple[str | None, str | None]:
        if re.search(r"\b(?:1|uno)\s+a\s+(?:1|uno)\b", text):
            return "1", "1"
        if re.search(r"\b(?:1|uno)\s+a\s+(?:muchos|varios|\*)\b", text):
            return "1", "*"
        if re.search(r"\b(?:muchos|varios|\*)\s+a\s+(?:1|uno)\b", text):
            return "*", "1"
        if re.search(r"\b(?:muchos|varios|\*)\s+a\s+(?:muchos|varios|\*)\b", text):
            return "*", "*"
        return None, None

    def _plan_method_specification(
        self, text: str, context: ContextoIAProyecto
    ) -> AccionPlanificada | None:
        diagram = context.active_diagram
        if diagram is None:
            return None
        for uml_class in diagram.classes:
            for method in uml_class.get("methods", []):
                method_name = str(method.get("name", ""))
                if method_name and method_name.casefold() in text:
                    method_id = self._uuid(method.get("id"))
                    if method_id is None:
                        continue
                    fields = []
                    for parameter in method.get("parameters", []):
                        parameter_name = str(parameter.get("name", ""))
                        source = parameter_name.removesuffix("Id").removesuffix("_id")
                        source_class = self._buscar_clase(diagram.classes, self._pascal(source))
                        display_fields = [
                            str(attribute.get("name"))
                            for attribute in (source_class or {}).get("attributes", [])[:2]
                            if attribute.get("name")
                        ]
                        fields.append(
                            {
                                "parameter_id": str(parameter.get("id")) if parameter.get("id") else None,
                                "parameter": parameter_name,
                                "control": "entity_selector" if source_class else "text_input",
                                "source_entity_id": str(source_class.get("id")) if source_class else None,
                                "source_entity": str(source_class.get("name")) if source_class else None,
                                "display_fields": display_fields,
                                "hidden": False,
                            }
                        )
                    return AccionPlanificada(
                        order=1,
                        action_type="update_method_specification",
                        target_type="uml_method",
                        target_id=method_id,
                        target_name=method_name,
                        diagram_id=diagram.id,
                        base_diagram_version=diagram.current_version,
                        payload={
                            "description": f"Ejecutar {method_name} segun las reglas del dominio.",
                            "operation_kind": "business_action",
                            "exposure": "user_action",
                            "business_rules": [
                                "No permitir registros duplicados"
                            ] if "duplic" in text else [],
                            "backend_contract": {
                                "http_method": "POST",
                                "path": f"/{self._snake(method_name)}",
                                "transactional": True,
                                "authorization": [],
                                "error_codes": ["DUPLICATE_RECORD"] if "duplic" in text else [],
                            },
                            "frontend_contract": {
                                "interaction": "form",
                                "label": self._label(method_name),
                                "confirmation_required": "confirm" in text,
                                "refresh_targets": [str(uml_class.get("id"))],
                                "success_message": "Operacion completada",
                                "fields": fields,
                            },
                        },
                        explanation=f"Completar la especificacion funcional de {method_name}.",
                    )
        return None

    @staticmethod
    def _buscar_clase(classes: list[dict], name: str) -> dict | None:
        return next(
            (item for item in classes if str(item.get("name", "")).casefold() == name.casefold()),
            None,
        )

    def _destino_despues_de_con(self, text: str, classes: list[dict]) -> str | None:
        for item in classes:
            name = str(item.get("name", ""))
            if re.search(rf"\b(?:con|a)\s+(?:la\s+clase\s+)?{re.escape(name.casefold())}\b", text):
                return name
        return None

    @staticmethod
    def _uuid(value: object) -> UUID | None:
        if value is None:
            return None
        try:
            return UUID(str(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _pascal(value: str) -> str:
        return "".join(part[:1].upper() + part[1:] for part in re.split(r"[_ -]+", value) if part)

    @staticmethod
    def _snake(value: str) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "_", value).replace(" ", "_").casefold()

    @staticmethod
    def _label(value: str) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", " ", value).strip().capitalize()
