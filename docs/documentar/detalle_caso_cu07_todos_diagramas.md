# CU07. Consultar manual guiado

Caso basado en el asistente implementado en `AssistantWidget`. El CU07 no usa backend ni base de datos en la version actual; resuelve la ayuda en frontend con temas locales, palabras clave y respuesta fallback.

## Diagrama de clases v2

Marco: `class DCD CU07 Consultar manual guiado`

Clases:
```text
UI::AsistenteCASE
- isOpen
- isExpanded
- question
- messages
+ abrirAsistente()
+ cerrarAsistente()
+ alternarTamano()
+ ask(question)
+ handleSubmit(event)

Modelo::MensajeAsistente
- role
- text

Modelo::TemaAyuda
- title
- keywords
- answer

Servicio::ManualGuiado
+ normalizeQuestion(value)
+ answerQuestion(question)

Store::ThemeStore
- mode
+ toggleMode()

UI::AppLayout
+ renderAssistant()
+ logout()
```

Relaciones:
```text
AppLayout *-- AsistenteCASE
AsistenteCASE *-- MensajeAsistente
AsistenteCASE -> ManualGuiado
AsistenteCASE -> ThemeStore
ManualGuiado -> TemaAyuda
```

## Diagrama de secuencia v2

Marco: `sd CU07 Consultar manual guiado`

Lifelines:
```text
Usuario
UI::AppLayout
UI::AsistenteCASE
Servicio::ManualGuiado
Modelo::TemaAyuda
Modelo::MensajeAsistente
```

### Flujo principal
```text
Usuario -> AppLayout: accederSistema()
AppLayout -> AsistenteCASE: renderAssistant()
Usuario -> AsistenteCASE: abrirAsistente()
AsistenteCASE -> AsistenteCASE: setIsOpen(true)
Usuario -> AsistenteCASE: enviarConsulta()
AsistenteCASE -> AsistenteCASE: trim(question)
alt [consulta vacia]
AsistenteCASE --> Usuario: noRegistrarMensaje()
end
AsistenteCASE -> ManualGuiado: answerQuestion()
ManualGuiado -> ManualGuiado: normalizeQuestion()
ManualGuiado -> TemaAyuda: buscarPorPalabrasClave()
alt [tema encontrado]
TemaAyuda --> ManualGuiado: answer
end
alt [tema no encontrado]
ManualGuiado --> AsistenteCASE: respuestaFallback()
end
ManualGuiado --> AsistenteCASE: answer
AsistenteCASE -> MensajeAsistente: agregarMensajeUsuario()
AsistenteCASE -> MensajeAsistente: agregarMensajeAsistente()
AsistenteCASE --> Usuario: mostrarRespuesta()
```

## Diagrama de comunicacion v2

Objetos:
```text
usuario:Usuario
layout:AppLayout
asistente:AsistenteCASE
manual:ManualGuiado
tema:TemaAyuda
mensaje:MensajeAsistente
```

### Flujo principal
```text
1 usuario -> layout: accederSistema()
1.1 layout -> asistente: renderAssistant()
2 usuario -> asistente: abrirAsistente()
2.1 asistente -> asistente: setIsOpen(true)
3 usuario -> asistente: enviarConsulta()
3.1 asistente -> manual: answerQuestion()
3.2 manual -> manual: normalizeQuestion()
3.3 manual -> tema: buscarPorPalabrasClave()
3.4 asistente -> mensaje: agregarMensajeUsuario()
3.5 asistente -> mensaje: agregarMensajeAsistente()
3.6 asistente -> usuario: mostrarRespuesta()
```

### Condiciones alternativas
```text
4 [consultaVacia] asistente -> usuario: noRegistrarMensaje()
5 [temaNoEncontrado] manual -> asistente: respuestaFallback()
6 [cerrar] usuario -> asistente: cerrarAsistente()
6.1 [cerrar] asistente -> usuario: mostrarBurbuja()
7 [ampliarReducir] usuario -> asistente: alternarTamano()
```

## Diagrama de estado

Marco: `stm CU07 Consultar manual guiado`

Estados:
```text
[*] -> AsistenteCerrado
AsistenteCerrado -> AsistenteAbierto : abrirAsistente()
AsistenteAbierto -> ConsultaIngresada : enviarConsulta()
ConsultaIngresada -> DecisionConsulta
DecisionConsulta <<choice>> : Consulta valida?
DecisionConsulta -> AsistenteAbierto : [consulta vacia]
DecisionConsulta -> ConsultaNormalizada : [consulta valida]
ConsultaNormalizada -> TemasEvaluados : buscarCoincidencias()
TemasEvaluados -> DecisionTema
DecisionTema <<choice>> : Tema encontrado?
DecisionTema -> RespuestaEncontrada : [score > 0]
DecisionTema -> RespuestaFallback : [score = 0]
RespuestaEncontrada -> HistorialActualizado : agregarMensajes()
RespuestaFallback -> HistorialActualizado : agregarMensajes()
HistorialActualizado -> RespuestaMostrada
RespuestaMostrada -> AsistenteAbierto : nuevaConsulta()
AsistenteAbierto -> AsistenteCerrado : cerrarAsistente()
AsistenteCerrado -> [*] : salirDelSistema()
```
