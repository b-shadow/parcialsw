# Fase 2 - Flujos principales

## Flujo de autenticacion

1. Usuario ingresa credenciales.
2. Frontend envia solicitud REST.
3. Backend valida credenciales.
4. Backend emite JWT.
5. Frontend almacena token.
6. Frontend habilita rutas segun rol.
7. Backend registra evento de acceso.

## Flujo de creacion de proyecto

1. Editor solicita crear proyecto.
2. Backend valida autenticacion.
3. Backend crea proyecto.
4. Backend registra al usuario como Organizador interno.
5. Backend crea configuracion inicial.
6. Backend registra bitacora.
7. Frontend redirige al entorno del proyecto.

## Flujo colaborativo UML

1. Usuario abre editor UML.
2. Frontend conecta WebSocket a sala del proyecto.
3. Usuario crea o modifica elemento.
4. Frontend envia evento.
5. Backend valida permisos y version base.
6. Backend persiste cambio.
7. Backend distribuye evento.
8. Frontend de cada usuario actualiza canvas.

## Flujo texto a UML

1. Usuario escribe descripcion.
2. Backend registra solicitud IA.
3. Motor IA local interpreta entidades, atributos y relaciones.
4. Motor IA devuelve JSON UML.
5. Backend valida estructura.
6. Frontend muestra propuesta editable.
7. Usuario confirma cambios.

## Flujo imagen a UML

1. Usuario carga imagen.
2. Sistema almacena archivo temporal/controlado.
3. Preprocesamiento mejora contraste y segmentacion.
4. OCR extrae texto.
5. Vision artificial detecta cajas y relaciones.
6. IA reconstruye modelo UML.
7. Backend valida y guarda propuesta.
8. Frontend muestra diagrama editable.

## Flujo importacion/exportacion XMI

Importacion:

1. Usuario sube archivo XMI.
2. Backend valida formato.
3. Servicio XMI parsea clases, atributos, metodos y relaciones.
4. Motor UML crea modelo interno.
5. Sistema registra importacion.

Exportacion:

1. Usuario solicita exportar.
2. Backend consulta modelo interno.
3. Servicio XMI genera archivo compatible.
4. Sistema registra exportacion.
5. Usuario descarga archivo.

## Flujo generacion Spring Boot

1. Usuario selecciona modelo/version.
2. Backend valida permisos.
3. Motor UML entrega estructura normalizada.
4. Generador analiza entidades y relaciones.
5. Generador aplica plantillas deterministas.
6. Generador crea proyecto Spring Boot.
7. Sistema valida estructura.
8. Sistema registra artefacto.

## Flujo generacion Flutter

1. Usuario selecciona modelo y backend objetivo.
2. Backend valida permisos.
3. Generador analiza entidades y endpoints.
4. Generador crea modelos, servicios, pantallas y rutas.
5. Sistema valida estructura.
6. Sistema registra artefacto.

