# Detalle de diagramas de clases CU11-CU18

## CU11. Crear y editar diagramas de clases UML

Clases:
```text
Frontend::UmlEditorPage
+ refreshDiagramModel()
+ handleAddClass()
+ handleCreateRelationship()
+ saveSelectedClass()

Frontend::JointUmlCanvas
+ onClassClick()
+ onClassMove()
+ onClassRename()

Frontend::umlService
+ createDiagram()
+ createClass()
+ addAttribute()
+ addMethod()
+ createRelationship()
+ moveElement()

Servicio::UmlService
+ create_diagram()
+ create_class()
+ add_attribute()
+ add_method()
+ create_relationship()
+ move_element()

Entidad::UmlDiagram
Entidad::UmlClass
Entidad::UmlAttribute
Entidad::UmlMethod
Entidad::UmlRelationship
Entidad::UmlVisualElement
```

Relaciones:
```text
UmlEditorPage -> JointUmlCanvas
UmlEditorPage -> umlService
UmlService -> UmlRepository
UmlDiagram 1 -- * UmlClass
UmlClass 1 -- * UmlAttribute
UmlClass 1 -- * UmlMethod
UmlDiagram 1 -- * UmlRelationship
UmlDiagram 1 -- * UmlVisualElement
```

## CU12. Generar diagramas de clases UML mediante imagen

Clases:
```text
Frontend::aiService
+ imageToUml(payload)

API::AiRouter
+ image_to_uml(payload)

Servicio::AiService
+ image_to_uml(payload)

AI::LocalAIEngine
+ generate_uml_from_image(request)

AI::ImageUmlDetector
+ analyze_uml_image(base64)

AI::ImageUmlDetection
- classes
- relationships
- boxes
- observations
```

Relaciones:
```text
aiService -> AiRouter
AiRouter -> AiService
AiService -> LocalAIEngine
LocalAIEngine -> ImageUmlDetector
ImageUmlDetection -- DetectedUmlClass
ImageUmlDetection -- DetectedUmlRelationship
```

## CU13. Importar y exportar modelos UML

Clases:
```text
Motor::XmiEngine
+ import_xmi(content, name)
+ export_xmi(diagram)

Servicio::UmlService
+ import_diagram_xmi()
+ import_diagram_xmi_into_existing()
+ export_diagram_xmi()

Entidad::XmiExchange
- exchange_type
- tool_name
- file_name
- status
- metadata_json
```

Relaciones:
```text
UmlService -> XmiEngine
UmlService -> UmlRepository
UmlDiagram 1 -- * XmiExchange
XmiEngine -> UmlDiagramModel
```

## CU14. Validar diagramas de clases UML

Clases:
```text
Motor::UmlValidator
+ validate_internal_model(diagram)

Modelo::UmlDiagramModel
- classes
- relationships

Modelo::UmlClassModel
- attributes
- methods

Modelo::UmlRelationshipModel
- source_class_id
- target_class_id
- relationship_type
```

Relaciones:
```text
UmlService -> UmlValidator
UmlValidator -> UmlDiagramModel
UmlDiagramModel 1 -- * UmlClassModel
UmlDiagramModel 1 -- * UmlRelationshipModel
```

## CU15. Transformar modelo UML a estructura de implementacion

Clases:
```text
Frontend::GenerationPage
+ handleTransform()

Frontend::generationService
+ transform(payload)

Servicio::GenerationService
+ transform(payload, user)

Entidad::UmlTransformation
- diagram_id
- source_version
- target_platform
- intermediate_model
- status
```

Relaciones:
```text
GenerationPage -> generationService
GenerationService -> GenerationRepository
GenerationService -> UmlRepository
UmlDiagram 1 -- * UmlTransformation
```

## CU16. Generar backend Spring Boot

Clases:
```text
Servicio::GenerationService
+ generate_backend(payload, user)

Generador::SpringBootGeneratorService
+ generate(intermediate_model, name, generation_id)

Generador::SpringBootModelAnalyzer
+ analyze_model(intermediate_model, name)

Entidad::GeneratedBackend
- transformation_id
- name
- artifact_path
- manifest
```

Relaciones:
```text
GenerationService -> SpringBootGeneratorService
SpringBootGeneratorService -> SpringBootModelAnalyzer
UmlTransformation 1 -- * GeneratedBackend
GeneratedBackend 1 -- * GeneratedArtifact
```

## CU17. Generar frontend movil Flutter

Clases:
```text
Servicio::GenerationService
+ generate_frontend(payload, user)

Generador::FlutterGeneratorService
+ generate(intermediate_model, name, generation_id, api_base_url)

Generador::FlutterProjectWriter
+ write_flutter_project(project, output_dir)

Entidad::GeneratedFrontend
- transformation_id
- backend_id
- artifact_path
- manifest
```

Relaciones:
```text
GenerationService -> FlutterGeneratorService
FlutterGeneratorService -> FlutterProjectWriter
UmlTransformation 1 -- * GeneratedFrontend
GeneratedBackend 0..1 -- * GeneratedFrontend
GeneratedFrontend 1 -- * GeneratedArtifact
```

## CU18. Ejecutar generacion mediante IA local offline

Clases:
```text
Servicio::AiService
+ text_to_uml()
+ voice_to_uml()
+ image_to_uml()
+ validate_uml()
+ software_plan()

AI::LocalAIEngine
+ generate_uml()
+ generate_uml_from_voice()
+ generate_uml_from_image()
+ validate_uml()
+ generate_code_guidance()

AI::LocalVectorStore
+ search(query, limit)

AI::SeedDataset
+ get_seed_dataset()

AI::ModelProfile
- selected_model
- runtime
- offline
```

Relaciones:
```text
AiService -> LocalAIEngine
LocalAIEngine -> LocalVectorStore
LocalAIEngine -> SeedDataset
LocalAIEngine -> ModelProfile
```

