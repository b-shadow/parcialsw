# Detalle de diagramas de estado CU11-CU18

Cada caso debe dibujarse con pseudoestado inicial, estados principales, decisiones cuando exista bifurcacion y estado final.

Formato preparado para futura transformacion a VBScript de Enterprise Architect:

- `[*] -> Estado` crea el pseudoestado inicial y una transicion.
- `EstadoA -> EstadoB : evento()` crea una transicion con etiqueta.
- `DecisionX <<choice>> : Texto?` crea un nodo decision/choice con texto visible.
- `Estado -> [*] : evento()` crea el estado final y una transicion.

## CU11. Crear y editar diagramas de clases UML

Estados:
```text
[*] -> EditorAbierto
EditorAbierto -> DiagramaSolicitado : cargarDiagrama()
DiagramaSolicitado -> DecisionDiagramaDisponible
DecisionDiagramaDisponible <<choice>> : Diagrama disponible?
DecisionDiagramaDisponible -> ErrorMostrado : [diagrama no existe o sin membresia]
DecisionDiagramaDisponible -> DiagramaCargado : [diagrama disponible]
DiagramaCargado -> ClaseCreada : agregarClase()
DiagramaCargado -> RelacionCreada : conectarClases()
DiagramaCargado -> ElementoMovido : moverElemento()
DiagramaCargado -> ElementoEliminado : deleteSupr()
ElementoEliminado -> DecisionRelacionesAsociadas
DecisionRelacionesAsociadas <<choice>> : Tiene relaciones asociadas?
DecisionRelacionesAsociadas -> RelacionesEliminadas : [tiene relaciones]
DecisionRelacionesAsociadas -> CambioPreparado : [sin relaciones]
RelacionesEliminadas -> CambioPreparado
ClaseCreada -> CambioPreparado
RelacionCreada -> CambioPreparado
ElementoMovido -> CambioPreparado
CambioPreparado -> CambioPersistido : guardarApi()
CambioPersistido -> EventoSincronizado : enviarWebSocket()
EventoSincronizado -> DiagramaCargado
DiagramaCargado -> [*] : cerrarEditor()
ErrorMostrado -> [*]
```

## CU12. Generar diagramas de clases UML mediante imagen

Estados:
```text
[*] -> ImagenSeleccionada
ImagenSeleccionada -> ImagenCodificada
ImagenCodificada -> ProcesamientoLocal
ProcesamientoLocal -> DecisionDeteccion
DecisionDeteccion <<choice>> : Imagen interpretable?
DecisionDeteccion -> GeneracionRechazada : [imagen no interpretable]
DecisionDeteccion -> ModeloUmlGenerado : [clases y relaciones detectadas]
DecisionDeteccion -> ModeloIncompleto : [resultado incompleto]
ModeloIncompleto -> AjusteManualSolicitado
AjusteManualSolicitado -> ModeloUmlGenerado : completarManual()
ModeloUmlGenerado -> DiagramaPersistido
DiagramaPersistido -> DiagramaEditable
DiagramaEditable -> [*]
GeneracionRechazada -> [*]
```

## CU13. Importar y exportar modelos UML

Estados importar:
```text
[*] -> ArchivoXmlSeleccionado
ArchivoXmlSeleccionado -> XmlLeido
XmlLeido -> XmlParseado
XmlParseado -> DecisionXml
DecisionXml <<choice>> : XML compatible?
DecisionXml -> ImportacionRechazada : [XML invalido]
DecisionXml -> ModeloVacio : [sin clases]
DecisionXml -> ModeloInternoCreado : [XML compatible]
ModeloVacio -> ImportacionRechazada
ModeloInternoCreado -> DiagramaAnteriorLimpiado
DiagramaAnteriorLimpiado -> DiagramaImportado
DiagramaImportado -> [*]
ImportacionRechazada -> [*]
```

Estados exportar:
```text
[*] -> DiagramaSeleccionado
DiagramaSeleccionado -> ModeloInternoConstruido
ModeloInternoConstruido -> DecisionExportable
DecisionExportable <<choice>> : Modelo exportable?
DecisionExportable -> ExportacionRechazada : [diagrama vacio]
DecisionExportable -> XmlEnterpriseArchitectGenerado : [modelo exportable]
XmlEnterpriseArchitectGenerado -> ArchivoDescargado
ArchivoDescargado -> [*]
ExportacionRechazada -> [*]
```

## CU14. Validar diagramas de clases UML

Estados:
```text
[*] -> ValidacionSolicitada
ValidacionSolicitada -> ModeloCargado
ModeloCargado -> ReglasEvaluadas
ReglasEvaluadas -> DecisionResultadoValidacion
DecisionResultadoValidacion <<choice>> : Resultado de validacion?
DecisionResultadoValidacion -> ConErrores : [errores > 0]
DecisionResultadoValidacion -> ConAdvertencias : [advertencias > 0]
DecisionResultadoValidacion -> Valido : [sin observaciones]
ConErrores -> ModalValidacion
ConAdvertencias -> ModalValidacion
Valido -> ModalValidacion
ModalValidacion -> [*]
```

## CU15. Transformar modelo UML a estructura de implementacion

Estados:
```text
[*] -> DiagramaSeleccionado
DiagramaSeleccionado -> TransformacionSolicitada
TransformacionSolicitada -> ModeloUmlCargado
ModeloUmlCargado -> DecisionModeloTransformable
DecisionModeloTransformable <<choice>> : Modelo transformable?
DecisionModeloTransformable -> TransformacionRechazada : [diagrama invalido]
DecisionModeloTransformable -> ModeloIntermedioConstruido : [diagrama valido]
ModeloIntermedioConstruido -> TransformacionPersistida
TransformacionPersistida -> TransformacionDisponible
TransformacionDisponible -> [*]
TransformacionRechazada -> [*]
```

## CU16. Generar backend Spring Boot

Estados:
```text
[*] -> TransformacionSeleccionada
TransformacionSeleccionada -> TransformacionConsultada
TransformacionConsultada -> DecisionTransformacionBackend
DecisionTransformacionBackend <<choice>> : Transformacion disponible?
DecisionTransformacionBackend -> BackendRechazado : [transformacion no encontrada]
DecisionTransformacionBackend -> GeneracionBackendSolicitada : [transformacion disponible]
GeneracionBackendSolicitada -> ProyectoSpringAnalizado
ProyectoSpringAnalizado -> DecisionGeneradorBackend
DecisionGeneradorBackend <<choice>> : Backend generado correctamente?
DecisionGeneradorBackend -> BackendFallido : [error generacion]
DecisionGeneradorBackend -> ArchivosBackendEscritos : [generacion correcta]
ArchivosBackendEscritos -> ZipBackendCreado
ZipBackendCreado -> ArtefactoBackendRegistrado
ArtefactoBackendRegistrado -> BackendDescargable
BackendDescargable -> [*]
BackendFallido -> [*]
BackendRechazado -> [*]
```

## CU17. Generar frontend movil Flutter

Estados:
```text
[*] -> TransformacionDisponible
TransformacionDisponible -> BackendConsultado
BackendConsultado -> DecisionBackend
DecisionBackend <<choice>> : Backend asociado disponible?
DecisionBackend -> FrontendRechazado : [backend asociado no encontrado]
DecisionBackend -> GeneracionFlutterSolicitada : [backend disponible u opcional]
GeneracionFlutterSolicitada -> ProyectoFlutterAnalizado
ProyectoFlutterAnalizado -> DecisionGeneradorFlutter
DecisionGeneradorFlutter <<choice>> : Flutter generado correctamente?
DecisionGeneradorFlutter -> FrontendFallido : [error generacion]
DecisionGeneradorFlutter -> PlataformasCreadas : [Flutter CLI disponible]
DecisionGeneradorFlutter -> SoloFuente : [Flutter CLI no disponible]
PlataformasCreadas -> ZipFlutterCreado
SoloFuente -> ZipFlutterCreado
ZipFlutterCreado -> ArtefactoFrontendRegistrado
ArtefactoFrontendRegistrado -> FrontendDescargable
FrontendDescargable -> [*]
FrontendFallido -> [*]
FrontendRechazado -> [*]
```

## CU18. Ejecutar generacion mediante IA local offline

Estados:
```text
[*] -> SolicitudIaPreparada
SolicitudIaPreparada -> EntradaNormalizada
EntradaNormalizada -> MotorLocalInvocado
MotorLocalInvocado -> DecisionMotorIa
DecisionMotorIa <<choice>> : IA local disponible?
DecisionMotorIa -> IaRechazada : [IA local no disponible]
DecisionMotorIa -> RagLocalConsultado : [IA disponible]
RagLocalConsultado -> DatasetSemillaAplicado
DatasetSemillaAplicado -> ResultadoEstructurado
ResultadoEstructurado -> DecisionResultadoIa
DecisionResultadoIa <<choice>> : Resultado util?
DecisionResultadoIa -> EntradaInsuficiente : [sin contenido util]
DecisionResultadoIa -> RespuestaMostrada : [resultado util]
EntradaInsuficiente -> [*]
RespuestaMostrada -> DecisionPersistirDiagrama
DecisionPersistirDiagrama <<choice>> : Persistir diagrama?
DecisionPersistirDiagrama -> DiagramaPersistido : [usuario confirma]
DecisionPersistirDiagrama -> SolicitudCancelada : [usuario cancela]
DiagramaPersistido -> [*]
SolicitudCancelada -> [*]
IaRechazada -> [*]
```
