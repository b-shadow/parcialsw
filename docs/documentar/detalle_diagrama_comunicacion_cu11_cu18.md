# Detalle de diagramas de comunicacion CU11-CU18

En Enterprise Architect ubicar objetos libremente y numerar mensajes sobre cada enlace. Los mensajes usan nombres de funciones con parentesis vacios, no rutas HTTP.

El diagrama de comunicacion representa el mismo comportamiento que el diagrama de secuencia, pero no usa marcos `alt`. Los flujos alternativos se dibujan como mensajes condicionados con guardas, por ejemplo `3 [diagramaNoExiste] servicio -> pagina: mostrarError()`. Si el diagrama queda muy cargado, puede separarse en otro diagrama de comunicacion del mismo CU.

## CU11. Crear y editar diagramas de clases UML

Objetos:
```text
editor:Editor
pagina:UmlEditorPage
canvas:JointUmlCanvas
uml:umlService
router:UmlRouter
servicio:UmlService
repo:UmlRepository
socket:ProjectSocket
```

### Flujo principal

Mensajes:
```text
1 editor -> pagina: abrirEditor()
1.1 pagina -> uml: getDiagramModel()
1.2 uml -> router: get_diagram_model()
1.3 router -> servicio: get_diagram_model()
1.4 servicio -> repo: list_classes()
1.5 servicio -> repo: list_visual_elements()
1.6 servicio -> repo: list_relationships()
2 editor -> canvas: editarClase()
2.1 canvas -> pagina: onClassMove()
2.2 pagina -> uml: createClass()
2.3 uml -> router: create_class()
2.4 router -> servicio: create_class()
2.5 pagina -> uml: updateClass()
2.6 uml -> router: update_class()
2.7 pagina -> uml: moveElement()
2.8 uml -> router: move_element()
2.9 pagina -> socket: sendProjectEvent()
```

### Condiciones alternativas: Diagrama no encontrado / Clase relacionada eliminada

Mensajes:
```text
3 [diagramaNoExiste] servicio -> repo: get_diagram()
3.1 [diagramaNoExiste] repo -> servicio: DiagramOrNull
3.2 [diagramaNoExiste] servicio -> pagina: mostrarError()
4 [claseConRelaciones] pagina -> uml: deleteClass()
4.1 [claseConRelaciones] servicio -> repo: list_relationships_for_class()
4.2 [claseConRelaciones] servicio -> repo: delete_relationship()
4.3 [claseConRelaciones] servicio -> repo: delete_class()
```

## CU12. Generar diagramas UML mediante imagen

### Flujo principal

Mensajes:
```text
1 editor -> pagina: seleccionarImagen()
1.1 pagina -> aiService: imageToUml()
1.2 aiService -> AiRouter: image_to_uml()
1.3 AiRouter -> AiService: image_to_uml()
1.4 AiService -> LocalAIEngine: generate_uml_from_image()
1.5 LocalAIEngine -> ImageUmlDetector: analyze_uml_image()
1.6 pagina -> umlService: createDiagramFromAiResult()
1.7 umlService -> UmlRouter: create_diagram()
1.8 UmlRouter -> UmlService: create_diagram()
1.9 pagina -> umlService: createClass()
1.10 umlService -> UmlRouter: create_class()
1.11 pagina -> umlService: createRelationship()
1.12 umlService -> UmlRouter: create_relationship()
```

### Condiciones alternativas: Imagen no interpretable / Resultado incompleto

Mensajes:
```text
2 [imagenNoInterpretable] AiService -> LocalAIEngine: generate_uml_from_image()
2.1 [imagenNoInterpretable] LocalAIEngine -> AiService: resultadoInsuficiente()
2.2 [imagenNoInterpretable] AiService -> pagina: mostrarError()
3 [resultadoIncompleto] AiRouter -> pagina: clasesSinRelaciones()
3.1 [resultadoIncompleto] pagina -> pagina: solicitarAjusteManual()
```

## CU13. Importar y exportar modelos UML

### Flujo principal importar

Mensajes:
```text
1 editor -> pagina: importarXml()
1.1 pagina -> umlService: importXmiIntoDiagram()
1.2 umlService -> UmlRouter: import_xmi_into_diagram()
1.3 UmlRouter -> UmlService: import_diagram_xmi_into_existing()
1.4 UmlService -> XmiEngine: import_xmi()
1.5 UmlService -> UmlRepository: delete_visual_elements_by_diagram()
1.6 UmlService -> UmlRepository: delete_relationships_by_diagram()
1.7 UmlService -> UmlRepository: delete_classes_by_diagram()
1.8 UmlService -> UmlService: _populate_existing_diagram_from_model()
```

### Condiciones alternativas: XML invalido / Importacion sin clases

Mensajes:
```text
3 [xmlInvalido] UmlService -> XmiEngine: import_xmi()
3.1 [xmlInvalido] XmiEngine -> UmlService: errorParseo()
3.2 [xmlInvalido] UmlService -> pagina: mostrarError()
4 [importacionSinClases] XmiEngine -> UmlService: modeloVacio()
4.1 [importacionSinClases] UmlService -> pagina: mostrarError()
```

### Flujo principal exportar

Mensajes:
```text
2 editor -> pagina: exportarXml()
2.1 pagina -> umlService: exportXmi()
2.2 umlService -> UmlRouter: export_xmi_diagram()
2.3 UmlRouter -> UmlService: export_diagram_xmi()
2.4 UmlService -> UmlService: _build_internal_model()
2.5 UmlService -> XmiEngine: export_xmi()
2.6 pagina -> navegador: descargarXml()
```

### Condicion alternativa: Diagrama vacio

Mensajes:
```text
5 [diagramaVacio] UmlService -> UmlService: _build_internal_model()
5.1 [diagramaVacio] UmlService -> pagina: mostrarError()
```

## CU14. Validar diagramas UML

### Flujo principal

Mensajes:
```text
1 editor -> pagina: validar()
1.1 pagina -> umlService: validate()
1.2 umlService -> UmlRouter: validate_diagram()
1.3 UmlRouter -> UmlService: validate_diagram()
1.4 UmlService -> UmlService: _build_internal_model()
1.5 UmlService -> UmlValidator: validate_internal_model()
1.6 pagina -> pagina: mostrarValidacion()
```

### Condicion alternativa: Modelo con errores

Mensajes:
```text
2 [modeloConErrores] UmlService -> UmlValidator: validate_internal_model()
2.1 [modeloConErrores] UmlValidator -> UmlService: errors()
2.2 [modeloConErrores] UmlService -> pagina: mostrarErrores()
```

## CU15. Transformar modelo UML

### Flujo principal

Mensajes:
```text
1 editor -> generacion: transformarUml()
1.1 generacion -> generationService: transform()
1.2 generationService -> GenerationRouter: transform()
1.3 GenerationRouter -> GenerationService: transform()
1.4 GenerationService -> UmlRepository: get_diagram()
1.5 GenerationService -> UmlRepository: list_classes()
1.6 GenerationService -> UmlRepository: list_relationships()
1.7 GenerationService -> GenerationRepository: add_transformation()
```

### Condicion alternativa: Diagrama invalido para transformar

Mensajes:
```text
2 [diagramaInvalido] GenerationService -> UmlRepository: list_classes()
2.1 [diagramaInvalido] UmlRepository -> GenerationService: listaVacia()
2.2 [diagramaInvalido] GenerationService -> generacion: mostrarError()
```

## CU16. Generar backend Spring Boot

### Flujo principal

Mensajes:
```text
1 editor -> generacion: generarBackend()
1.1 generacion -> generationService: springBoot()
1.2 generationService -> GenerationRouter: generate_backend()
1.3 GenerationRouter -> GenerationService: generate_backend()
1.4 GenerationService -> GenerationRepository: get_transformation()
1.5 GenerationService -> SpringBootGeneratorService: generate()
1.6 SpringBootGeneratorService -> Storage: write_project()
1.7 SpringBootGeneratorService -> Storage: create_zip_archive()
1.8 GenerationService -> GenerationRepository: add_backend()
1.9 GenerationService -> GenerationRepository: add_artifact()
```

### Condiciones alternativas: Transformacion no encontrada / Generador backend falla

Mensajes:
```text
2 [transformacionNoExiste] GenerationService -> GenerationRepository: get_transformation()
2.1 [transformacionNoExiste] GenerationRepository -> GenerationService: TransformationOrNull
2.2 [transformacionNoExiste] GenerationService -> generacion: mostrarError()
3 [generadorBackendFalla] GenerationService -> SpringBootGeneratorService: generate()
3.1 [generadorBackendFalla] SpringBootGeneratorService -> GenerationService: errorGeneracion()
3.2 [generadorBackendFalla] GenerationService -> GenerationRepository: add_backend()
3.3 [generadorBackendFalla] GenerationService -> generacion: mostrarError()
```

## CU17. Generar frontend movil Flutter

### Flujo principal

Mensajes:
```text
1 editor -> generacion: generarFrontend()
1.1 generacion -> generationService: flutter()
1.2 generationService -> GenerationRouter: generate_frontend()
1.3 GenerationRouter -> GenerationService: generate_frontend()
1.4 GenerationService -> GenerationRepository: get_transformation()
1.5 GenerationService -> GenerationRepository: get_backend()
1.6 GenerationService -> FlutterGeneratorService: generate()
1.7 FlutterGeneratorService -> Storage: write_project()
1.8 FlutterGeneratorService -> Storage: create_zip_archive()
1.9 GenerationService -> GenerationRepository: add_frontend()
1.10 GenerationService -> GenerationRepository: add_artifact()
```

### Condiciones alternativas: Backend asociado no encontrado / Generador Flutter falla

Mensajes:
```text
2 [backendNoExiste] GenerationService -> GenerationRepository: get_backend()
2.1 [backendNoExiste] GenerationRepository -> GenerationService: BackendOrNull
2.2 [backendNoExiste] GenerationService -> generacion: mostrarError()
3 [generadorFlutterFalla] GenerationService -> FlutterGeneratorService: generate()
3.1 [generadorFlutterFalla] FlutterGeneratorService -> GenerationService: errorGeneracion()
3.2 [generadorFlutterFalla] GenerationService -> GenerationRepository: add_frontend()
3.3 [generadorFlutterFalla] GenerationService -> generacion: mostrarError()
```

## CU18. Ejecutar generacion mediante IA local offline

### Flujo principal

Mensajes:
```text
1 editor -> pagina: pedirIa()
1.1 pagina -> aiService: textToUml()
1.2 pagina -> aiService: voiceToUml()
1.3 pagina -> aiService: imageToUml()
1.4 aiService -> AiRouter: text_to_uml()
1.5 AiRouter -> AiService: text_to_uml()
1.6 AiService -> LocalAIEngine: generate_uml()
1.7 LocalAIEngine -> LocalVectorStore: search()
1.8 LocalAIEngine -> SeedDataset: get_seed_dataset()
1.9 LocalAIEngine -> AiService: build_response()
```

### Condiciones alternativas: IA local no disponible / Entrada sin contenido util

Mensajes:
```text
2 [iaLocalNoDisponible] AiService -> LocalAIEngine: generate_uml()
2.1 [iaLocalNoDisponible] LocalAIEngine -> AiService: errorModeloLocal()
2.2 [iaLocalNoDisponible] AiService -> pagina: mostrarError()
3 [entradaSinContenidoUtil] LocalAIEngine -> AiService: resultadoInsuficiente()
3.1 [entradaSinContenidoUtil] AiService -> pagina: pedirEntradaMasClara()
```
