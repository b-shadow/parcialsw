# Detalle de diagramas de secuencia CU11-CU18

Estilo: un marco `sd` por caso de uso. Mantener el flujo principal y no dibujar cada validacion menor. Los mensajes usan nombres de funciones del codigo con parentesis vacios, no rutas HTTP.

Los fragmentos `alt [condicion] ... end` estan integrados en el flujo principal. En Enterprise Architect se dibujan como Combined Fragment con operador `alt` exactamente en esa posicion; al cerrar `end`, el flujo continua con la siguiente linea.

## CU11. Crear y editar diagramas de clases UML

Lifelines:
```text
Editor
Frontend::UmlEditorPage
Frontend::JointUmlCanvas
Frontend::umlService
API::UmlRouter
Servicio::UmlService
Repo::UmlRepository
WebSocket::ProjectSocket
DB::PostgreSQL
```

### Flujo principal
```text
Editor -> UmlEditorPage: abrirDiagrama()
UmlEditorPage -> umlService: getDiagramModel()
umlService -> UmlRouter: get_diagram_model()
UmlRouter -> UmlService: get_diagram_model()
UmlService -> UmlRepository: get_diagram()
UmlRepository --> UmlService: DiagramOrNull
alt [diagrama no encontrado o sin membresia]
UmlService --> UmlRouter: errorNoEncontradoOAutorizacion()
UmlRouter --> UmlEditorPage: mostrarError()
end
UmlService -> UmlRepository: list_classes()
UmlService -> UmlRepository: list_visual_elements()
UmlService -> UmlRepository: list_relationships()
UmlRepository -> PostgreSQL: select_modelo_uml()
UmlRouter --> UmlEditorPage: DiagramModelResponse
Editor -> JointUmlCanvas: editarClase()
JointUmlCanvas -> UmlEditorPage: onClassMove()
UmlEditorPage -> umlService: createClass()
umlService -> UmlRouter: create_class()
UmlRouter -> UmlService: create_class()
UmlService -> UmlRepository: add_class()
UmlService -> UmlRepository: add_visual_element()
UmlRepository -> PostgreSQL: insert_uml_class()
UmlEditorPage -> umlService: updateClass()
umlService -> UmlRouter: update_class()
UmlRouter -> UmlService: update_class()
UmlEditorPage -> umlService: moveElement()
umlService -> UmlRouter: move_element()
UmlRouter -> UmlService: move_element()
UmlEditorPage -> umlService: deleteClass()
umlService -> UmlRouter: delete_class()
UmlRouter -> UmlService: delete_class()
UmlService -> UmlRepository: list_relationships_for_class()
alt [clase relacionada eliminada]
UmlService -> UmlRepository: delete_relationship()
end
UmlService -> UmlRepository: delete_class()
UmlEditorPage -> ProjectSocket: sendProjectEvent()
```

## CU12. Generar diagramas de clases UML mediante imagen

Lifelines:
```text
Editor
Frontend::UmlEditorPage
Frontend::aiService
API::AiRouter
Servicio::AiService
AI::LocalAIEngine
CV::ImageUmlDetector
Frontend::umlService
API::UmlRouter
Servicio::UmlService
DB::PostgreSQL
```

### Flujo principal
```text
Editor -> UmlEditorPage: seleccionarImagen()
UmlEditorPage -> aiService: imageToUml()
aiService -> AiRouter: image_to_uml()
AiRouter -> AiService: image_to_uml()
AiService -> LocalAIEngine: generate_uml_from_image()
LocalAIEngine -> ImageUmlDetector: analyze_uml_image()
ImageUmlDetector --> LocalAIEngine: classes, relationships, observations
LocalAIEngine --> AiService: AiUmlResponse
alt [imagen no interpretable]
AiService --> AiRouter: errorProcesamiento()
AiRouter --> UmlEditorPage: mostrarError()
end
AiRouter --> UmlEditorPage: resultado estructurado
alt [resultado IA incompleto]
UmlEditorPage -> UmlEditorPage: solicitarAjusteManual()
end
UmlEditorPage -> umlService: createDiagramFromAiResult()
umlService -> UmlRouter: create_diagram()
UmlRouter -> UmlService: create_diagram()
UmlEditorPage -> umlService: createClass()
umlService -> UmlRouter: create_class()
UmlRouter -> UmlService: create_class()
UmlEditorPage -> umlService: createRelationship()
umlService -> UmlRouter: create_relationship()
UmlRouter -> UmlService: create_relationship()
UmlRouter -> PostgreSQL: insert_modelo_editable()
```

## CU13. Importar y exportar modelos UML

Lifelines:
```text
Editor
Frontend::UmlEditorPage
Frontend::umlService
API::UmlRouter
Servicio::UmlService
Motor::XmiEngine
Repo::UmlRepository
DB::PostgreSQL
```

### Flujo principal importar
```text
Editor -> UmlEditorPage: importarXml()
UmlEditorPage -> umlService: importXmiIntoDiagram()
umlService -> UmlRouter: import_xmi_into_diagram()
UmlRouter -> UmlService: import_diagram_xmi_into_existing()
UmlService -> XmiEngine: import_xmi()
XmiEngine --> UmlService: UmlDiagramModel
alt [XML invalido o no compatible]
XmiEngine --> UmlService: errorParseo()
UmlService --> UmlRouter: errorImportacion()
UmlRouter --> UmlEditorPage: mostrarError()
end
alt [importacion sin clases]
XmiEngine --> UmlService: modeloVacio()
UmlService --> UmlRouter: errorValidacion()
UmlRouter --> UmlEditorPage: mostrarError()
end
UmlService -> UmlRepository: delete_visual_elements_by_diagram()
UmlService -> UmlRepository: delete_relationships_by_diagram()
UmlService -> UmlRepository: delete_classes_by_diagram()
UmlRepository -> PostgreSQL: delete_modelo_anterior()
UmlService -> UmlService: _populate_existing_diagram_from_model()
UmlRepository -> PostgreSQL: insert_modelo_importado()
UmlRouter --> UmlEditorPage: DiagramResponse
```

### Flujo principal exportar
```text
Editor -> UmlEditorPage: exportarXml()
UmlEditorPage -> umlService: exportXmi()
umlService -> UmlRouter: export_xmi_diagram()
UmlRouter -> UmlService: export_diagram_xmi()
UmlService -> UmlService: _build_internal_model()
alt [diagrama vacio]
UmlService --> UmlRouter: errorValidacion()
UmlRouter --> UmlEditorPage: mostrarError()
end
UmlService -> XmiEngine: export_xmi()
XmiEngine --> UmlService: XML Enterprise Architect
UmlRouter --> UmlEditorPage: XmiExportResponse
UmlEditorPage -> UmlEditorPage: descargarXml()
```

## CU14. Validar diagramas de clases UML

Lifelines:
```text
Editor
Frontend::UmlEditorPage
Frontend::umlService
API::UmlRouter
Servicio::UmlService
Motor::UmlValidator
DB::PostgreSQL
```

### Flujo principal
```text
Editor -> UmlEditorPage: validar()
UmlEditorPage -> umlService: validate()
umlService -> UmlRouter: validate_diagram()
UmlRouter -> UmlService: validate_diagram()
UmlService -> UmlService: _build_internal_model()
UmlService -> UmlValidator: validate_internal_model()
UmlValidator --> UmlService: errors, warnings, recommendations
alt [modelo con errores]
UmlService --> UmlRouter: UmlValidationResponse
UmlRouter --> UmlEditorPage: mostrarErrores()
end
UmlRouter --> UmlEditorPage: UmlValidationResponse
UmlEditorPage -> UmlEditorPage: mostrarValidacion()
```

## CU15. Transformar modelo UML a estructura de implementacion

Lifelines:
```text
Editor
Frontend::GenerationPage
Frontend::generationService
API::GenerationRouter
Servicio::GenerationService
Repo::UmlRepository
Repo::GenerationRepository
DB::PostgreSQL
```

### Flujo principal
```text
Editor -> GenerationPage: transformarUml()
GenerationPage -> generationService: transform()
generationService -> GenerationRouter: transform()
GenerationRouter -> GenerationService: transform()
GenerationService -> UmlRepository: get_diagram()
GenerationService -> UmlRepository: list_classes()
UmlRepository --> GenerationService: List<UmlClass>
alt [diagrama invalido para transformar]
GenerationService --> GenerationRouter: errorValidacion()
GenerationRouter --> GenerationPage: mostrarError()
end
GenerationService -> UmlRepository: list_relationships()
UmlRepository -> PostgreSQL: select_modelo_uml()
GenerationService -> GenerationService: build_intermediate_model()
GenerationService -> GenerationRepository: add_transformation()
GenerationRepository -> PostgreSQL: insert_uml_transformations()
GenerationRouter --> GenerationPage: TransformationResponse
```

## CU16. Generar backend Spring Boot

Lifelines:
```text
Editor
Frontend::GenerationPage
Frontend::generationService
API::GenerationRouter
Servicio::GenerationService
Generador::SpringBootGeneratorService
Repo::GenerationRepository
Storage::GeneratedFiles
DB::PostgreSQL
```

### Flujo principal
```text
Editor -> GenerationPage: generarBackend()
GenerationPage -> generationService: springBoot()
generationService -> GenerationRouter: generate_backend()
GenerationRouter -> GenerationService: generate_backend()
GenerationService -> GenerationRepository: get_transformation()
GenerationRepository -> PostgreSQL: select_uml_transformations()
GenerationRepository --> GenerationService: TransformationOrNull
alt [transformacion no encontrada]
GenerationService --> GenerationRouter: errorNoEncontrado()
GenerationRouter --> GenerationPage: mostrarError()
end
GenerationService -> SpringBootGeneratorService: generate()
alt [generador backend falla]
SpringBootGeneratorService --> GenerationService: errorGeneracion()
GenerationService -> GenerationRepository: add_backend()
GenerationService --> GenerationRouter: errorGeneracion()
end
SpringBootGeneratorService -> Storage: write_project()
SpringBootGeneratorService -> Storage: create_zip_archive()
SpringBootGeneratorService --> GenerationService: manifest, artifact_path
GenerationService -> GenerationRepository: add_backend()
GenerationService -> GenerationRepository: add_artifact()
GenerationRepository -> PostgreSQL: insert_generated_backends()
GenerationRouter --> GenerationPage: GeneratedBackendResponse
```

## CU17. Generar frontend movil Flutter

Lifelines:
```text
Editor
Frontend::GenerationPage
Frontend::generationService
API::GenerationRouter
Servicio::GenerationService
Generador::FlutterGeneratorService
Repo::GenerationRepository
Storage::GeneratedFiles
DB::PostgreSQL
```

### Flujo principal
```text
Editor -> GenerationPage: generarFrontend()
GenerationPage -> generationService: flutter()
generationService -> GenerationRouter: generate_frontend()
GenerationRouter -> GenerationService: generate_frontend()
GenerationService -> GenerationRepository: get_transformation()
GenerationService -> GenerationRepository: get_backend()
GenerationRepository -> PostgreSQL: select_generation()
GenerationRepository --> GenerationService: BackendOrNull
alt [backend asociado no encontrado]
GenerationService --> GenerationRouter: errorNoEncontrado()
GenerationRouter --> GenerationPage: mostrarError()
end
GenerationService -> FlutterGeneratorService: generate()
alt [generador Flutter falla]
FlutterGeneratorService --> GenerationService: errorGeneracion()
GenerationService -> GenerationRepository: add_frontend()
GenerationService --> GenerationRouter: errorGeneracion()
end
FlutterGeneratorService -> Storage: write_project()
FlutterGeneratorService -> Storage: create_zip_archive()
GenerationService -> GenerationRepository: add_frontend()
GenerationService -> GenerationRepository: add_artifact()
GenerationRepository -> PostgreSQL: insert_generated_frontends()
GenerationRouter --> GenerationPage: GeneratedFrontendResponse
```

## CU18. Ejecutar generacion mediante IA local offline

Lifelines:
```text
Editor
Frontend::UmlEditorPage
Frontend::aiService
API::AiRouter
Servicio::AiService
AI::LocalAIEngine
AI::LocalVectorStore
Dataset::SeedDataset
```

### Flujo principal
```text
Editor -> UmlEditorPage: solicitarIa()
UmlEditorPage -> aiService: textToUml()
UmlEditorPage -> aiService: voiceToUml()
UmlEditorPage -> aiService: imageToUml()
aiService -> AiRouter: text_to_uml()
aiService -> AiRouter: voice_to_uml()
aiService -> AiRouter: image_to_uml()
AiRouter -> AiService: text_to_uml()
AiService -> LocalAIEngine: generate_uml()
alt [IA local no disponible]
LocalAIEngine --> AiService: errorModeloLocal()
AiService --> AiRouter: errorProcesamiento()
AiRouter --> UmlEditorPage: mostrarError()
end
LocalAIEngine -> LocalVectorStore: search()
LocalVectorStore --> LocalAIEngine: conocimiento local
LocalAIEngine -> SeedDataset: get_seed_dataset()
SeedDataset --> LocalAIEngine: ejemplos locales
LocalAIEngine --> AiService: AiUmlResponse
alt [voz o imagen sin contenido util]
AiService --> AiRouter: pedirEntradaMasClara()
AiRouter --> UmlEditorPage: mostrarMensaje()
end
AiRouter --> UmlEditorPage: clases, relaciones, confianza
```
