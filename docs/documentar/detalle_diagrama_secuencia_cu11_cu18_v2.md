# Detalle de diagramas de secuencia CU11-CU18

Estilo: un marco `sd` por caso de uso. Mantener el flujo principal y no dibujar cada validacion menor. Los mensajes usan nombres de funciones del codigo con parentesis vacios, no rutas HTTP.

Los fragmentos `alt [condicion] ... end` estan integrados en el flujo principal. En Enterprise Architect se dibujan como Combined Fragment con operador `alt` exactamente en esa posicion; al cerrar `end`, el flujo continua con la siguiente linea.

## CU11. Crear y editar diagramas de clases UML

Lifelines:
```text
Editor
UI::EditorUML
UI::LienzoUML
Cliente::ModeladoUMLClient
Controlador::ModeladoUMLController
Servicio::ModeladoUMLService
Repositorio::ModeloUMLRepository
WebSocket::ProjectSocket
DB::BaseDatos
```

### Flujo principal
```text
Editor -> EditorUML: abrirDiagrama()
EditorUML -> ModeladoUMLClient: getDiagramModel()
ModeladoUMLClient -> ModeladoUMLController: get_diagram_model()
ModeladoUMLController -> ModeladoUMLService: get_diagram_model()
ModeladoUMLService -> ModeloUMLRepository: get_diagram()
ModeloUMLRepository --> ModeladoUMLService: DiagramOrNull
alt [diagrama no encontrado o sin membresia]
ModeladoUMLService --> ModeladoUMLController: errorNoEncontradoOAutorizacion()
ModeladoUMLController --> EditorUML: mostrarError()
end
ModeladoUMLService -> ModeloUMLRepository: list_classes()
ModeladoUMLService -> ModeloUMLRepository: list_visual_elements()
ModeladoUMLService -> ModeloUMLRepository: list_relationships()
ModeloUMLRepository -> BaseDatos: select_modelo_uml()
ModeladoUMLController --> EditorUML: DiagramModelResponse
Editor -> LienzoUML: editarClase()
LienzoUML -> EditorUML: onClassMove()
EditorUML -> ModeladoUMLClient: createClass()
ModeladoUMLClient -> ModeladoUMLController: create_class()
ModeladoUMLController -> ModeladoUMLService: create_class()
ModeladoUMLService -> ModeloUMLRepository: add_class()
ModeladoUMLService -> ModeloUMLRepository: add_visual_element()
ModeloUMLRepository -> BaseDatos: insert_uml_class()
EditorUML -> ModeladoUMLClient: updateClass()
ModeladoUMLClient -> ModeladoUMLController: update_class()
ModeladoUMLController -> ModeladoUMLService: update_class()
EditorUML -> ModeladoUMLClient: moveElement()
ModeladoUMLClient -> ModeladoUMLController: move_element()
ModeladoUMLController -> ModeladoUMLService: move_element()
EditorUML -> ModeladoUMLClient: deleteClass()
ModeladoUMLClient -> ModeladoUMLController: delete_class()
ModeladoUMLController -> ModeladoUMLService: delete_class()
ModeladoUMLService -> ModeloUMLRepository: list_relationships_for_class()
alt [clase relacionada eliminada]
ModeladoUMLService -> ModeloUMLRepository: delete_relationship()
end
ModeladoUMLService -> ModeloUMLRepository: delete_class()
EditorUML -> ProjectSocket: sendProjectEvent()
```

## CU12. Generar diagramas de clases UML mediante imagen

Lifelines:
```text
Editor
UI::EditorUML
Cliente::IaClient
Controlador::IaController
Servicio::IaService
AI::LocalAIEngine
CV::ImageUmlDetector
Cliente::ModeladoUMLClient
Controlador::ModeladoUMLController
Servicio::ModeladoUMLService
DB::BaseDatos
```

### Flujo principal
```text
Editor -> EditorUML: seleccionarImagen()
EditorUML -> IaClient: imageToUml()
IaClient -> IaController: image_to_uml()
IaController -> IaService: image_to_uml()
IaService -> LocalAIEngine: generate_uml_from_image()
LocalAIEngine -> ImageUmlDetector: analyze_uml_image()
ImageUmlDetector --> LocalAIEngine: classes, relationships, observations
LocalAIEngine --> IaService: AiUmlResponse
alt [imagen no interpretable]
IaService --> IaController: errorProcesamiento()
IaController --> EditorUML: mostrarError()
end
IaController --> EditorUML: resultado estructurado
alt [resultado IA incompleto]
EditorUML -> EditorUML: solicitarAjusteManual()
end
EditorUML -> ModeladoUMLClient: createDiagramFromAiResult()
ModeladoUMLClient -> ModeladoUMLController: create_diagram()
ModeladoUMLController -> ModeladoUMLService: create_diagram()
EditorUML -> ModeladoUMLClient: createClass()
ModeladoUMLClient -> ModeladoUMLController: create_class()
ModeladoUMLController -> ModeladoUMLService: create_class()
EditorUML -> ModeladoUMLClient: createRelationship()
ModeladoUMLClient -> ModeladoUMLController: create_relationship()
ModeladoUMLController -> ModeladoUMLService: create_relationship()
ModeladoUMLController -> BaseDatos: insert_modelo_editable()
```

## CU13. Importar y exportar modelos UML

Lifelines:
```text
Editor
UI::EditorUML
Cliente::ModeladoUMLClient
Controlador::ModeladoUMLController
Servicio::ModeladoUMLService
Motor::IntercambioXML
Repositorio::ModeloUMLRepository
DB::BaseDatos
```

### Flujo principal importar
```text
Editor -> EditorUML: importarXml()
EditorUML -> ModeladoUMLClient: importXmiIntoDiagram()
ModeladoUMLClient -> ModeladoUMLController: import_xmi_into_diagram()
ModeladoUMLController -> ModeladoUMLService: import_diagram_xmi_into_existing()
ModeladoUMLService -> IntercambioXML: import_xmi()
IntercambioXML --> ModeladoUMLService: ModeloDiagramaUML
alt [XML invalido o no compatible]
IntercambioXML --> ModeladoUMLService: errorParseo()
ModeladoUMLService --> ModeladoUMLController: errorImportacion()
ModeladoUMLController --> EditorUML: mostrarError()
end
alt [importacion sin clases]
IntercambioXML --> ModeladoUMLService: modeloVacio()
ModeladoUMLService --> ModeladoUMLController: errorValidacion()
ModeladoUMLController --> EditorUML: mostrarError()
end
ModeladoUMLService -> ModeloUMLRepository: delete_visual_elements_by_diagram()
ModeladoUMLService -> ModeloUMLRepository: delete_relationships_by_diagram()
ModeladoUMLService -> ModeloUMLRepository: delete_classes_by_diagram()
ModeloUMLRepository -> BaseDatos: delete_modelo_anterior()
ModeladoUMLService -> ModeladoUMLService: _populate_existing_diagram_from_model()
ModeloUMLRepository -> BaseDatos: insert_modelo_importado()
ModeladoUMLController --> EditorUML: DiagramResponse
```

### Flujo principal exportar
```text
Editor -> EditorUML: exportarXml()
EditorUML -> ModeladoUMLClient: exportXmi()
ModeladoUMLClient -> ModeladoUMLController: export_xmi_diagram()
ModeladoUMLController -> ModeladoUMLService: export_diagram_xmi()
ModeladoUMLService -> ModeladoUMLService: _build_internal_model()
alt [diagrama vacio]
ModeladoUMLService --> ModeladoUMLController: errorValidacion()
ModeladoUMLController --> EditorUML: mostrarError()
end
ModeladoUMLService -> IntercambioXML: export_xmi()
IntercambioXML --> ModeladoUMLService: XML Enterprise Architect
ModeladoUMLController --> EditorUML: XmiExportResponse
EditorUML -> EditorUML: descargarXml()
```

## CU14. Validar diagramas de clases UML

Lifelines:
```text
Editor
UI::EditorUML
Cliente::ModeladoUMLClient
Controlador::ModeladoUMLController
Servicio::ModeladoUMLService
Motor::ValidadorUML
DB::BaseDatos
```

### Flujo principal
```text
Editor -> EditorUML: validar()
EditorUML -> ModeladoUMLClient: validate()
ModeladoUMLClient -> ModeladoUMLController: validate_diagram()
ModeladoUMLController -> ModeladoUMLService: validate_diagram()
ModeladoUMLService -> ModeladoUMLService: _build_internal_model()
ModeladoUMLService -> ValidadorUML: validate_internal_model()
ValidadorUML --> ModeladoUMLService: errors, warnings, recommendations
alt [modelo con errores]
ModeladoUMLService --> ModeladoUMLController: UmlValidationResponse
ModeladoUMLController --> EditorUML: mostrarErrores()
end
ModeladoUMLController --> EditorUML: UmlValidationResponse
EditorUML -> EditorUML: mostrarValidacion()
```

## CU15. Transformar modelo UML a estructura de implementacion

Lifelines:
```text
Editor
UI::GeneracionSoftware
Cliente::GeneracionClient
Controlador::GeneracionController
Servicio::GeneracionService
Repositorio::ModeloUMLRepository
Repositorio::GeneracionRepository
DB::BaseDatos
```

### Flujo principal
```text
Editor -> GeneracionSoftware: transformarUml()
GeneracionSoftware -> GeneracionClient: transform()
GeneracionClient -> GeneracionController: transform()
GeneracionController -> GeneracionService: transform()
GeneracionService -> ModeloUMLRepository: get_diagram()
GeneracionService -> ModeloUMLRepository: list_classes()
ModeloUMLRepository --> GeneracionService: List<ClaseUML>
alt [diagrama invalido para transformar]
GeneracionService --> GeneracionController: errorValidacion()
GeneracionController --> GeneracionSoftware: mostrarError()
end
GeneracionService -> ModeloUMLRepository: list_relationships()
ModeloUMLRepository -> BaseDatos: select_modelo_uml()
GeneracionService -> GeneracionService: build_intermediate_model()
GeneracionService -> GeneracionRepository: add_transformation()
GeneracionRepository -> BaseDatos: insert_uml_transformations()
GeneracionController --> GeneracionSoftware: TransformationResponse
```

## CU16. Generar backend Spring Boot

Lifelines:
```text
Editor
UI::GeneracionSoftware
Cliente::GeneracionClient
Controlador::GeneracionController
Servicio::GeneracionService
Generador::SpringBootGeneratorService
Repositorio::GeneracionRepository
Storage::ArchivosGenerados
DB::BaseDatos
```

### Flujo principal
```text
Editor -> GeneracionSoftware: generarBackend()
GeneracionSoftware -> GeneracionClient: springBoot()
GeneracionClient -> GeneracionController: generate_backend()
GeneracionController -> GeneracionService: generate_backend()
GeneracionService -> GeneracionRepository: get_transformation()
GeneracionRepository -> BaseDatos: select_uml_transformations()
GeneracionRepository --> GeneracionService: TransformationOrNull
alt [transformacion no encontrada]
GeneracionService --> GeneracionController: errorNoEncontrado()
GeneracionController --> GeneracionSoftware: mostrarError()
end
GeneracionService -> SpringBootGeneratorService: generate()
alt [generador backend falla]
SpringBootGeneratorService --> GeneracionService: errorGeneracion()
GeneracionService -> GeneracionRepository: add_backend()
GeneracionService --> GeneracionController: errorGeneracion()
end
SpringBootGeneratorService -> Storage: write_project()
SpringBootGeneratorService -> Storage: create_zip_archive()
SpringBootGeneratorService --> GeneracionService: manifest, artifact_path
GeneracionService -> GeneracionRepository: add_backend()
GeneracionService -> GeneracionRepository: add_artifact()
GeneracionRepository -> BaseDatos: insert_generated_backends()
GeneracionController --> GeneracionSoftware: BackendGeneradoResponse
```

## CU17. Generar frontend movil Flutter

Lifelines:
```text
Editor
UI::GeneracionSoftware
Cliente::GeneracionClient
Controlador::GeneracionController
Servicio::GeneracionService
Generador::FlutterGeneratorService
Repositorio::GeneracionRepository
Storage::ArchivosGenerados
DB::BaseDatos
```

### Flujo principal
```text
Editor -> GeneracionSoftware: generarFrontend()
GeneracionSoftware -> GeneracionClient: flutter()
GeneracionClient -> GeneracionController: generate_frontend()
GeneracionController -> GeneracionService: generate_frontend()
GeneracionService -> GeneracionRepository: get_transformation()
GeneracionService -> GeneracionRepository: get_backend()
GeneracionRepository -> BaseDatos: select_generation()
GeneracionRepository --> GeneracionService: BackendOrNull
alt [backend asociado no encontrado]
GeneracionService --> GeneracionController: errorNoEncontrado()
GeneracionController --> GeneracionSoftware: mostrarError()
end
GeneracionService -> FlutterGeneratorService: generate()
alt [generador Flutter falla]
FlutterGeneratorService --> GeneracionService: errorGeneracion()
GeneracionService -> GeneracionRepository: add_frontend()
GeneracionService --> GeneracionController: errorGeneracion()
end
FlutterGeneratorService -> Storage: write_project()
FlutterGeneratorService -> Storage: create_zip_archive()
GeneracionService -> GeneracionRepository: add_frontend()
GeneracionService -> GeneracionRepository: add_artifact()
GeneracionRepository -> BaseDatos: insert_generated_frontends()
GeneracionController --> GeneracionSoftware: FrontendGeneradoResponse
```

## CU18. Ejecutar generacion mediante IA local offline

Lifelines:
```text
Editor
UI::EditorUML
Cliente::IaClient
Controlador::IaController
Servicio::IaService
AI::LocalAIEngine
AI::LocalVectorStore
Dataset::SeedDataset
```

### Flujo principal
```text
Editor -> EditorUML: solicitarIa()
EditorUML -> IaClient: textToUml()
EditorUML -> IaClient: voiceToUml()
EditorUML -> IaClient: imageToUml()
IaClient -> IaController: text_to_uml()
IaClient -> IaController: voice_to_uml()
IaClient -> IaController: image_to_uml()
IaController -> IaService: text_to_uml()
IaService -> LocalAIEngine: generate_uml()
alt [IA local no disponible]
LocalAIEngine --> IaService: errorModeloLocal()
IaService --> IaController: errorProcesamiento()
IaController --> EditorUML: mostrarError()
end
LocalAIEngine -> LocalVectorStore: search()
LocalVectorStore --> LocalAIEngine: conocimiento local
LocalAIEngine -> SeedDataset: get_seed_dataset()
SeedDataset --> LocalAIEngine: ejemplos locales
LocalAIEngine --> IaService: AiUmlResponse
alt [voz o imagen sin contenido util]
IaService --> IaController: pedirEntradaMasClara()
IaController --> EditorUML: mostrarMensaje()
end
IaController --> EditorUML: clases, relaciones, confianza
```




