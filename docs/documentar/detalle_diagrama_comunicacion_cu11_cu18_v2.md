# Detalle de diagramas de comunicacion CU11-CU18

En Enterprise Architect ubicar objetos libremente y numerar mensajes sobre cada enlace. Los mensajes usan nombres de funciones con parentesis vacios, no rutas HTTP.

El diagrama de comunicacion representa el mismo comportamiento que el diagrama de secuencia, pero no usa marcos `alt`. Los flujos alternativos se dibujan como mensajes condicionados con guardas, por ejemplo `3 [diagramaNoExiste] servicio -> pagina: mostrarError()`. Si el diagrama queda muy cargado, puede separarse en otro diagrama de comunicacion del mismo CU.

## CU11. Crear y editar diagramas de clases UML

Objetos:
```text
editor:Editor
pagina:EditorUML
canvas:LienzoUML
uml:ModeladoUMLClient
router:ModeladoUMLController
servicio:ModeladoUMLService
repo:ModeloUMLRepository
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
1.1 pagina -> IaClient: imageToUml()
1.2 IaClient -> IaController: image_to_uml()
1.3 IaController -> IaService: image_to_uml()
1.4 IaService -> LocalAIEngine: generate_uml_from_image()
1.5 LocalAIEngine -> ImageUmlDetector: analyze_uml_image()
1.6 pagina -> ModeladoUMLClient: createDiagramFromAiResult()
1.7 ModeladoUMLClient -> ModeladoUMLController: create_diagram()
1.8 ModeladoUMLController -> ModeladoUMLService: create_diagram()
1.9 pagina -> ModeladoUMLClient: createClass()
1.10 ModeladoUMLClient -> ModeladoUMLController: create_class()
1.11 pagina -> ModeladoUMLClient: createRelationship()
1.12 ModeladoUMLClient -> ModeladoUMLController: create_relationship()
```

### Condiciones alternativas: Imagen no interpretable / Resultado incompleto

Mensajes:
```text
2 [imagenNoInterpretable] IaService -> LocalAIEngine: generate_uml_from_image()
2.1 [imagenNoInterpretable] LocalAIEngine -> IaService: resultadoInsuficiente()
2.2 [imagenNoInterpretable] IaService -> pagina: mostrarError()
3 [resultadoIncompleto] IaController -> pagina: clasesSinRelaciones()
3.1 [resultadoIncompleto] pagina -> pagina: solicitarAjusteManual()
```

## CU13. Importar y exportar modelos UML

### Flujo principal importar

Mensajes:
```text
1 editor -> pagina: importarXml()
1.1 pagina -> ModeladoUMLClient: importXmiIntoDiagram()
1.2 ModeladoUMLClient -> ModeladoUMLController: import_xmi_into_diagram()
1.3 ModeladoUMLController -> ModeladoUMLService: import_diagram_xmi_into_existing()
1.4 ModeladoUMLService -> IntercambioXML: import_xmi()
1.5 ModeladoUMLService -> ModeloUMLRepository: delete_visual_elements_by_diagram()
1.6 ModeladoUMLService -> ModeloUMLRepository: delete_relationships_by_diagram()
1.7 ModeladoUMLService -> ModeloUMLRepository: delete_classes_by_diagram()
1.8 ModeladoUMLService -> ModeladoUMLService: _populate_existing_diagram_from_model()
```

### Condiciones alternativas: XML invalido / Importacion sin clases

Mensajes:
```text
3 [xmlInvalido] ModeladoUMLService -> IntercambioXML: import_xmi()
3.1 [xmlInvalido] IntercambioXML -> ModeladoUMLService: errorParseo()
3.2 [xmlInvalido] ModeladoUMLService -> pagina: mostrarError()
4 [importacionSinClases] IntercambioXML -> ModeladoUMLService: modeloVacio()
4.1 [importacionSinClases] ModeladoUMLService -> pagina: mostrarError()
```

### Flujo principal exportar

Mensajes:
```text
2 editor -> pagina: exportarXml()
2.1 pagina -> ModeladoUMLClient: exportXmi()
2.2 ModeladoUMLClient -> ModeladoUMLController: export_xmi_diagram()
2.3 ModeladoUMLController -> ModeladoUMLService: export_diagram_xmi()
2.4 ModeladoUMLService -> ModeladoUMLService: _build_internal_model()
2.5 ModeladoUMLService -> IntercambioXML: export_xmi()
2.6 pagina -> navegador: descargarXml()
```

### Condicion alternativa: Diagrama vacio

Mensajes:
```text
5 [diagramaVacio] ModeladoUMLService -> ModeladoUMLService: _build_internal_model()
5.1 [diagramaVacio] ModeladoUMLService -> pagina: mostrarError()
```

## CU14. Validar diagramas UML

### Flujo principal

Mensajes:
```text
1 editor -> pagina: validar()
1.1 pagina -> ModeladoUMLClient: validate()
1.2 ModeladoUMLClient -> ModeladoUMLController: validate_diagram()
1.3 ModeladoUMLController -> ModeladoUMLService: validate_diagram()
1.4 ModeladoUMLService -> ModeladoUMLService: _build_internal_model()
1.5 ModeladoUMLService -> ValidadorUML: validate_internal_model()
1.6 pagina -> pagina: mostrarValidacion()
```

### Condicion alternativa: Modelo con errores

Mensajes:
```text
2 [modeloConErrores] ModeladoUMLService -> ValidadorUML: validate_internal_model()
2.1 [modeloConErrores] ValidadorUML -> ModeladoUMLService: errors()
2.2 [modeloConErrores] ModeladoUMLService -> pagina: mostrarErrores()
```

## CU15. Transformar modelo UML

### Flujo principal

Mensajes:
```text
1 editor -> generacion: transformarUml()
1.1 generacion -> GeneracionClient: transform()
1.2 GeneracionClient -> GeneracionController: transform()
1.3 GeneracionController -> GeneracionService: transform()
1.4 GeneracionService -> ModeloUMLRepository: get_diagram()
1.5 GeneracionService -> ModeloUMLRepository: list_classes()
1.6 GeneracionService -> ModeloUMLRepository: list_relationships()
1.7 GeneracionService -> GeneracionRepository: add_transformation()
```

### Condicion alternativa: Diagrama invalido para transformar

Mensajes:
```text
2 [diagramaInvalido] GeneracionService -> ModeloUMLRepository: list_classes()
2.1 [diagramaInvalido] ModeloUMLRepository -> GeneracionService: listaVacia()
2.2 [diagramaInvalido] GeneracionService -> generacion: mostrarError()
```

## CU16. Generar backend Spring Boot

### Flujo principal

Mensajes:
```text
1 editor -> generacion: generarBackend()
1.1 generacion -> GeneracionClient: springBoot()
1.2 GeneracionClient -> GeneracionController: generate_backend()
1.3 GeneracionController -> GeneracionService: generate_backend()
1.4 GeneracionService -> GeneracionRepository: get_transformation()
1.5 GeneracionService -> SpringBootGeneratorService: generate()
1.6 SpringBootGeneratorService -> Storage: write_project()
1.7 SpringBootGeneratorService -> Storage: create_zip_archive()
1.8 GeneracionService -> GeneracionRepository: add_backend()
1.9 GeneracionService -> GeneracionRepository: add_artifact()
```

### Condiciones alternativas: Transformacion no encontrada / Generador backend falla

Mensajes:
```text
2 [transformacionNoExiste] GeneracionService -> GeneracionRepository: get_transformation()
2.1 [transformacionNoExiste] GeneracionRepository -> GeneracionService: TransformationOrNull
2.2 [transformacionNoExiste] GeneracionService -> generacion: mostrarError()
3 [generadorBackendFalla] GeneracionService -> SpringBootGeneratorService: generate()
3.1 [generadorBackendFalla] SpringBootGeneratorService -> GeneracionService: errorGeneracion()
3.2 [generadorBackendFalla] GeneracionService -> GeneracionRepository: add_backend()
3.3 [generadorBackendFalla] GeneracionService -> generacion: mostrarError()
```

## CU17. Generar frontend movil Flutter

### Flujo principal

Mensajes:
```text
1 editor -> generacion: generarFrontend()
1.1 generacion -> GeneracionClient: flutter()
1.2 GeneracionClient -> GeneracionController: generate_frontend()
1.3 GeneracionController -> GeneracionService: generate_frontend()
1.4 GeneracionService -> GeneracionRepository: get_transformation()
1.5 GeneracionService -> GeneracionRepository: get_backend()
1.6 GeneracionService -> FlutterGeneratorService: generate()
1.7 FlutterGeneratorService -> Storage: write_project()
1.8 FlutterGeneratorService -> Storage: create_zip_archive()
1.9 GeneracionService -> GeneracionRepository: add_frontend()
1.10 GeneracionService -> GeneracionRepository: add_artifact()
```

### Condiciones alternativas: Backend asociado no encontrado / Generador Flutter falla

Mensajes:
```text
2 [backendNoExiste] GeneracionService -> GeneracionRepository: get_backend()
2.1 [backendNoExiste] GeneracionRepository -> GeneracionService: BackendOrNull
2.2 [backendNoExiste] GeneracionService -> generacion: mostrarError()
3 [generadorFlutterFalla] GeneracionService -> FlutterGeneratorService: generate()
3.1 [generadorFlutterFalla] FlutterGeneratorService -> GeneracionService: errorGeneracion()
3.2 [generadorFlutterFalla] GeneracionService -> GeneracionRepository: add_frontend()
3.3 [generadorFlutterFalla] GeneracionService -> generacion: mostrarError()
```

## CU18. Ejecutar generacion mediante IA local offline

### Flujo principal

Mensajes:
```text
1 editor -> pagina: pedirIa()
1.1 pagina -> IaClient: textToUml()
1.2 pagina -> IaClient: voiceToUml()
1.3 pagina -> IaClient: imageToUml()
1.4 IaClient -> IaController: text_to_uml()
1.5 IaController -> IaService: text_to_uml()
1.6 IaService -> LocalAIEngine: generate_uml()
1.7 LocalAIEngine -> LocalVectorStore: search()
1.8 LocalAIEngine -> SeedDataset: get_seed_dataset()
1.9 LocalAIEngine -> IaService: build_response()
```

### Condiciones alternativas: IA local no disponible / Entrada sin contenido util

Mensajes:
```text
2 [iaLocalNoDisponible] IaService -> LocalAIEngine: generate_uml()
2.1 [iaLocalNoDisponible] LocalAIEngine -> IaService: errorModeloLocal()
2.2 [iaLocalNoDisponible] IaService -> pagina: mostrarError()
3 [entradaSinContenidoUtil] LocalAIEngine -> IaService: resultadoInsuficiente()
3.1 [entradaSinContenidoUtil] IaService -> pagina: pedirEntradaMasClara()
```




