# Detalle de diagramas de clases CU11-CU18 v2

Version v2: usa nombres semanticos para diagramar. Las entidades incluyen atributos del modelo persistente o del modelo interno; las clases de motor, servicio, generador y UI incluyen operaciones porque representan comportamiento.

## CU11. Crear y editar diagramas de clases UML

Marco: `class DCD CU11 Crear y editar diagramas de clases UML`

Clases:
```text
UI::EditorUML
- projectId
- diagramId
- selectedElement
- toolMode
+ refreshDiagramModel()
+ handleAddClass()
+ handleCreateRelationship()
+ saveSelectedClass()
+ deleteSelectedElement()

UI::LienzoUML
- scale
- panX
- panY
- selectedCellId
+ onClassClick()
+ onClassMove()
+ onClassRename()
+ onBlankPointerDown()
+ zoomIn()
+ zoomOut()

Cliente::ModeladoUMLClient
+ getDiagramModel(diagramId)
+ createDiagram(payload)
+ createClass(diagramId, payload)
+ updateClass(classId, payload)
+ deleteClass(classId)
+ addAttribute(classId, payload)
+ addMethod(classId, payload)
+ createRelationship(diagramId, payload)
+ moveElement(elementId, payload)

Controlador::ModeladoUMLController
+ get_diagram_model(diagram_id)
+ create_diagram(payload)
+ create_class(diagram_id, payload)
+ update_class(class_id, payload)
+ delete_class(class_id)
+ create_relationship(diagram_id, payload)
+ move_element(element_id, payload)

Servicio::ModeladoUMLService
+ get_diagram_model(diagram_id, user)
+ create_diagram(payload, user)
+ create_class(diagram_id, payload, user)
+ update_class(class_id, payload, user)
+ delete_class(class_id, user)
+ create_relationship(diagram_id, payload, user)
+ move_element(element_id, payload, user)

Repositorio::ModeloUMLRepository
+ get_diagram(diagram_id)
+ add_diagram(diagram)
+ add_class(uml_class)
+ update_class(uml_class)
+ delete_class(class_id)
+ add_attribute(attribute)
+ add_method(method)
+ add_relationship(relationship)
+ delete_relationship(relationship_id)
+ add_visual_element(element)

Entidad::DiagramaUML
- id
- project_id
- created_by_user_id
- name
- diagram_type
- status
- current_version
- description
- metadata_json

Entidad::ClaseUML
- id
- diagram_id
- name
- visibility
- element_type
- stereotype
- description
- metadata_json

Entidad::AtributoUML
- id
- class_id
- name
- data_type
- visibility
- initial_value
- multiplicity
- is_required
- order_index
- constraints

Entidad::MetodoUML
- id
- class_id
- name
- return_type
- visibility
- order_index
- metadata_json

Entidad::RelacionUML
- id
- diagram_id
- source_class_id
- target_class_id
- relationship_type
- source_cardinality
- target_cardinality
- direction
- label
- metadata_json

Entidad::ElementoVisualUML
- id
- diagram_id
- element_type
- element_id
- position_x
- position_y
- width
- height
- style
```

Relaciones:
```text
EditorUML -> LienzoUML
EditorUML -> ModeladoUMLClient
ModeladoUMLClient -> ModeladoUMLController
ModeladoUMLController -> ModeladoUMLService
ModeladoUMLService -> ModeloUMLRepository
DiagramaUML 1 -- * ClaseUML
ClaseUML 1 -- * AtributoUML
ClaseUML 1 -- * MetodoUML
DiagramaUML 1 -- * RelacionUML
DiagramaUML 1 -- * ElementoVisualUML
RelacionUML * -- 1 ClaseUML : source
RelacionUML * -- 1 ClaseUML : target
```

## CU12. Generar diagramas de clases UML mediante imagen

Marco: `class DCD CU12 Generar diagramas de clases UML mediante imagen`

Clases:
```text
UI::EditorUML
- imageFile
- importStatus
+ seleccionarImagen()
+ enviarImagenAUML()
+ renderizarModeloDetectado()

Cliente::IaClient
+ imageToUML(payload)

Controlador::IaController
+ image_to_uml(payload)

Servicio::IaService
+ image_to_uml(payload)

AI::LocalAIEngine
- selected_model
- runtime
- offline
+ generate_uml_from_image(request)

AI::DetectorImagenUML
+ analyze_uml_image(base64)
+ extract_classes(result)
+ extract_relationships(result)

Modelo::DeteccionImagenUML
- classes
- relationships
- boxes
- observations

Modelo::ClaseUMLDetectada
- name
- attributes
- methods
- confidence
- bounding_box

Modelo::RelacionUMLDetectada
- source
- target
- relationship_type
- cardinality
- confidence
```

Relaciones:
```text
EditorUML -> IaClient
IaClient -> IaController
IaController -> IaService
IaService -> LocalAIEngine
LocalAIEngine -> DetectorImagenUML
DeteccionImagenUML 1 -- * ClaseUMLDetectada
DeteccionImagenUML 1 -- * RelacionUMLDetectada
```

## CU13. Importar y exportar modelos UML

Marco: `class DCD CU13 Importar y exportar modelos UML`

Clases:
```text
UI::EditorUML
- importMessage
- exportStatus
+ seleccionarArchivoXML()
+ importarXML()
+ exportarXML()
+ limpiarLienzo()

Cliente::ModeladoUMLClient
+ importXml(diagramId, file)
+ exportXml(diagramId)

Controlador::ModeladoUMLController
+ import_diagram_xmi_into_existing(diagram_id, file)
+ export_diagram_xmi(diagram_id)

Servicio::ModeladoUMLService
+ import_diagram_xmi(content, name, user)
+ import_diagram_xmi_into_existing(diagram_id, content, user)
+ export_diagram_xmi(diagram_id, user)
- _populate_existing_diagram_from_model(model)
- _build_internal_model(diagram)

Motor::IntercambioXML
+ import_xmi(content, name)
+ export_xmi(diagram)

Repositorio::ModeloUMLRepository
+ delete_visual_elements_by_diagram(diagram_id)
+ delete_relationships_by_diagram(diagram_id)
+ delete_classes_by_diagram(diagram_id)
+ insert_modelo_importado(model)

Entidad::IntercambioXML
- id
- diagram_id
- user_id
- exchange_type
- tool_name
- file_name
- file_path
- status
- error_detail
- metadata_json

Modelo::ModeloDiagramaUML
- name
- classes
- relationships
- visual_elements
```

Relaciones:
```text
EditorUML -> ModeladoUMLClient
ModeladoUMLClient -> ModeladoUMLController
ModeladoUMLController -> ModeladoUMLService
ModeladoUMLService -> IntercambioXML
ModeladoUMLService -> ModeloUMLRepository
DiagramaUML 1 -- * IntercambioXML
IntercambioXML -> ModeloDiagramaUML
```

## CU14. Validar diagramas de clases UML

Marco: `class DCD CU14 Validar diagramas de clases UML`

Clases:
```text
UI::EditorUML
- validationResult
+ validarDiagrama()
+ mostrarErrores()
+ mostrarRecomendaciones()

Cliente::ModeladoUMLClient
+ validateDiagram(diagramId)

Controlador::ModeladoUMLController
+ validate_diagram(diagram_id)

Servicio::ModeladoUMLService
+ validate_diagram(diagram_id, user)
- _build_internal_model(diagram)

Motor::ValidadorUML
+ validate_internal_model(diagram)
- validate_classes(classes)
- validate_relationships(relationships)

Modelo::ModeloDiagramaUML
- classes
- relationships

Modelo::ModeloClaseUML
- name
- attributes
- methods

Modelo::ModeloRelacionUML
- source_class_id
- target_class_id
- relationship_type
- source_cardinality
- target_cardinality

Modelo::ResultadoValidacion
- errors
- warnings
- recommendations
```

Relaciones:
```text
EditorUML -> ModeladoUMLClient
ModeladoUMLClient -> ModeladoUMLController
ModeladoUMLController -> ModeladoUMLService
ModeladoUMLService -> ValidadorUML
ValidadorUML -> ModeloDiagramaUML
ModeloDiagramaUML 1 -- * ModeloClaseUML
ModeloDiagramaUML 1 -- * ModeloRelacionUML
ValidadorUML --> ResultadoValidacion
```

## CU15. Transformar modelo UML a estructura de implementacion

Marco: `class DCD CU15 Transformar modelo UML a estructura de implementacion`

Clases:
```text
UI::GeneracionSoftware
- selectedDiagram
- targetPlatform
- transformationResult
+ handleTransform()
+ mostrarResultado()
+ mostrarError()

Cliente::GeneracionClient
+ transform(payload)

Controlador::GeneracionController
+ transform(payload)

Servicio::GeneracionService
+ transform(payload, user)
- build_intermediate_model(diagram)

Repositorio::ModeloUMLRepository
+ get_diagram(diagram_id)
+ list_classes(diagram_id)
+ list_relationships(diagram_id)

Repositorio::GeneracionRepository
+ add_transformation(transformation)

Entidad::TransformacionUML
- id
- project_id
- diagram_id
- requested_by_user_id
- source_version
- target_platform
- intermediate_model
- status
- error_detail
```

Relaciones:
```text
GeneracionSoftware -> GeneracionClient
GeneracionClient -> GeneracionController
GeneracionController -> GeneracionService
GeneracionService -> ModeloUMLRepository
GeneracionService -> GeneracionRepository
DiagramaUML 1 -- * TransformacionUML
```

## CU16. Generar backend Spring Boot

Marco: `class DCD CU16 Generar backend Spring Boot`

Clases:
```text
UI::GeneracionSoftware
+ generarBackend()
+ descargarBackend()

Cliente::GeneracionClient
+ springBoot(payload)

Controlador::GeneracionController
+ generate_backend(payload)

Servicio::GeneracionService
+ generate_backend(payload, user)

Generador::SpringBootGeneratorService
+ generate(intermediate_model, name, generation_id)

Generador::SpringBootModelAnalyzer
+ analyze_model(intermediate_model, name)

Repositorio::GeneracionRepository
+ get_transformation(transformation_id)
+ add_backend(backend)
+ add_artifact(artifact)

Entidad::BackendGenerado
- id
- project_id
- transformation_id
- generated_by_user_id
- name
- technology
- language
- database_engine
- version_label
- status
- artifact_path
- manifest
- error_detail

Entidad::ArtefactoGenerado
- id
- project_id
- generated_backend_id
- generated_frontend_id
- artifact_type
- file_name
- file_path
- checksum
- metadata_json
```

Relaciones:
```text
GeneracionSoftware -> GeneracionClient
GeneracionClient -> GeneracionController
GeneracionController -> GeneracionService
GeneracionService -> SpringBootGeneratorService
SpringBootGeneratorService -> SpringBootModelAnalyzer
GeneracionService -> GeneracionRepository
TransformacionUML 1 -- * BackendGenerado
BackendGenerado 1 -- * ArtefactoGenerado
```

## CU17. Generar frontend movil Flutter

Marco: `class DCD CU17 Generar frontend movil Flutter`

Clases:
```text
UI::GeneracionSoftware
+ generarFrontend()
+ descargarFrontend()

Cliente::GeneracionClient
+ flutter(payload)

Controlador::GeneracionController
+ generate_frontend(payload)

Servicio::GeneracionService
+ generate_frontend(payload, user)

Generador::FlutterGeneratorService
+ generate(intermediate_model, name, generation_id, api_base_url)

Generador::FlutterProjectWriter
+ write_flutter_project(project, output_dir)

Repositorio::GeneracionRepository
+ get_transformation(transformation_id)
+ add_frontend(frontend)
+ add_artifact(artifact)

Entidad::FrontendGenerado
- id
- project_id
- transformation_id
- generated_by_user_id
- backend_id
- name
- technology
- language
- version_label
- status
- artifact_path
- manifest
- error_detail

Entidad::BackendGenerado
- id
- name
- technology
- artifact_path
- manifest

Entidad::ArtefactoGenerado
- id
- project_id
- generated_backend_id
- generated_frontend_id
- artifact_type
- file_name
- file_path
- checksum
```

Relaciones:
```text
GeneracionSoftware -> GeneracionClient
GeneracionClient -> GeneracionController
GeneracionController -> GeneracionService
GeneracionService -> FlutterGeneratorService
FlutterGeneratorService -> FlutterProjectWriter
GeneracionService -> GeneracionRepository
TransformacionUML 1 -- * FrontendGenerado
BackendGenerado 0..1 -- * FrontendGenerado
FrontendGenerado 1 -- * ArtefactoGenerado
```

## CU18. Ejecutar generacion mediante IA local offline

Marco: `class DCD CU18 Ejecutar generacion mediante IA local offline`

Clases:
```text
UI::EditorUML
- prompt
- inputMode
+ generarDesdeTexto()
+ generarDesdeVoz()
+ generarDesdeImagen()

Cliente::IaClient
+ textToUML(payload)
+ voiceToUML(payload)
+ imageToUML(payload)
+ validateUML(payload)

Servicio::IaService
+ text_to_uml(payload)
+ voice_to_uml(payload)
+ image_to_uml(payload)
+ validate_uml(payload)
+ software_plan(payload)

AI::LocalAIEngine
- selected_model
- runtime
- offline
+ generate_uml(prompt)
+ generate_uml_from_voice(audio)
+ generate_uml_from_image(image)
+ validate_uml(model)
+ generate_code_guidance(model)

AI::LocalVectorStore
- index_path
- embedding_model
+ search(query, limit)

AI::SeedDataset
- examples
+ get_seed_dataset()

AI::ModelProfile
- selected_model
- runtime
- offline

Entidad::ProcesoIA
- id
- user_id
- project_id
- diagram_id
- process_type
- model_provider
- model_name
- input_payload
- output_payload
- status
- error_detail
```

Relaciones:
```text
EditorUML -> IaClient
IaClient -> IaService
IaService -> LocalAIEngine
IaService -> ProcesoIA
LocalAIEngine -> LocalVectorStore
LocalAIEngine -> SeedDataset
LocalAIEngine -> ModelProfile
```

