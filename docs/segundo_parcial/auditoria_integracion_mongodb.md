# Auditoría de la integración MongoDB — 29 de octubre de 2026

## Alcance

Se revisaron los flujos de creación y edición UML, generación de código, conversaciones, memoria del asistente, versiones, respaldo y reconciliación entre PostgreSQL y MongoDB. PostgreSQL conserva identidad, permisos y registros operativos; MongoDB conserva el contenido UML, mensajes y versiones.

## Fallos corregidos

| Flujo | Causa | Corrección |
| --- | --- | --- |
| Crear proyecto | El control de documento ausente rechazaba un diagrama que aún se estaba inicializando. | La creación registra el diagrama en el repositorio Mongo antes de confirmar la transacción. |
| Crear clase desde imagen | El estilo visual transitorio era `None` y el modelo documental exigía un objeto. | Se normaliza a `{}` al construir el documento. |
| Generar Spring Boot | La transformación consultaba el repositorio SQL de contenido retirado. | La generación usa el mismo repositorio UML que el editor; los diagramas sin clases se rechazan antes de registrar una generación fallida. |
| Chat y memoria | Tres métodos asíncronos de lectura segura quedaron en la clase síncrona. | Se movieron al almacén asíncrono y se añadieron pruebas de contexto y paginación. |
| Historial faltante | Un chat con secuencia SQL positiva y cero mensajes Mongo podía parecer vacío. | La lectura devuelve un error explícito y la reconciliación detecta la discrepancia. |
| Respaldo coordinado | Recorría modelos de tablas SQL eliminadas físicamente. | Respaldar y restaurar usa las tablas existentes; se rechazan respaldos con tablas ausentes en el esquema actual. |
| Auditoría NoSQL | Un diagrama nuevo vacío se consideraba inválido; las estadísticas de índices no esperaban el cursor asíncrono. | Se distingue un diagrama vacío válido y se espera el cursor correctamente. |
| Errores 500 | El navegador mostraba un falso diagnóstico de CORS al recibir una excepción no controlada. | La API devuelve un error JSON con cabecera CORS para orígenes autorizados. |
| Importación de servicios | Las importaciones inmediatas del paquete del asistente creaban un ciclo según el orden de carga. | Los servicios públicos del paquete se cargan de forma diferida. |
| Avisos repetidos de Redis | La lectura bloqueante del registro de cambios duraba lo mismo que el tiempo de espera del socket (dos segundos). | El tiempo de espera del socket aumenta a cinco segundos para permitir la respuesta normal de la lectura. |
| Historial parcial | Una conversación con el mismo número de documentos que mensajes registrados podía ocultar huecos en la secuencia; la pantalla también podía mostrar una página incompleta. | La auditoría comprueba las secuencias esperadas y la lectura rechaza páginas con huecos o sin el último mensaje registrado. |
| MongoDB fuera de servicio al leer UML | La lectura directa del documento podía propagar un error de conexión como 500 genérico. | Se devuelve 503 con código `UML_DOCUMENT_UNAVAILABLE`; un documento con formato inválido devuelve `UML_DOCUMENT_INVALID`. |
| Interacción con el asistente | El orquestador entregaba objetos `DetectedIntent`, mientras que el contrato del mensaje exige nombres de intención; la respuesta fallaba al persistirse con un 500 después de guardar la pregunta. | Se guardan los nombres, se filtran referencias inválidas y se marca como fallido el mensaje pendiente si la persistencia de la respuesta falla. El mensaje pendiente de la incidencia se cerró como fallido. |

## Limpieza de datos antiguos

La reconciliación encontró cinco diagramas y una versión registrados en SQL sin documento Mongo, más un chat antiguo con 16 mensajes registrados y ningún mensaje Mongo. Se retiraron los cuatro proyectos antiguos asociados y sus registros dependientes. Se conservó `prueba 1`, su diagrama y la cuenta de acceso.

Antes de la limpieza se creó `storage/backups/case_before_old_cleanup_20261029.dump`. Después se verificó el respaldo coordinado en `storage/backups/case_after_cleanup_20261029.zip`. La auditoría operativa final devolvió `healthy` con cero hallazgos.

## Verificación

- Suite del backend: 205 pruebas aprobadas; diez pruebas de integración se omiten sin bases aisladas. La prueba nueva del asistente pasó por separado con bases PostgreSQL y MongoDB aisladas.
- Integración real con PostgreSQL y MongoDB separados: conexión, versiones, respaldo y esquema retirado aprobados.
- Migraciones históricas de fases 11 y 13: aprobadas con el esquema previo al retiro de tablas y sus indicadores correspondientes.
- Flujo real en bases aisladas: crear proyecto, crear clase con atributo y método, leer el documento Mongo y transformar a Spring Boot.
- `ruff`, compilación del frontend, API `/ready`, frontend y preflight CORS aprobados.

## Revisión del asistente del proyecto

Se probó el recorrido completo en bases PostgreSQL y MongoDB aisladas: crear proyecto y clase, preguntar por el diagrama, recibir y persistir la explicación, repetir la solicitud con el mismo identificador sin duplicar mensajes, pedir mejoras, proponer una clase, confirmarla, resumir la conversación y recuperar ese contexto desde otro chat. El resultado fue correcto y la reconciliación de ambas bases terminó `healthy` sin hallazgos. Las bases de prueba se eliminaron al terminar.

En el frontend se corrigió el cursor de sincronización para que solo avance con mensajes realmente cargados. La carga inicial conserva mensajes WebSocket que llegaron mientras se esperaba la respuesta REST y las cargas antiguas no sobrescriben otro chat. Si la respuesta se guardó pero falla la sincronización posterior, el texto no se presenta como fallido ni se vuelve a enviar. Si se pierde la respuesta HTTP, el cliente consulta el historial antes de permitir un reenvío. Los errores de persistencia emiten el fin del procesamiento y actualizan el estado visible del mensaje. El cierre de un WebSocket todavía en conexión espera a que se abra antes de cerrarlo, evitando avisos espurios del navegador.

La suite del frontend terminó con 68 pruebas aprobadas, compilación de producción y lint correctos.

El orquestador responde preguntas y revisiones UML con las reglas locales cuando reconoce el contexto, incluso si Ollama está configurado. Se comprobó que esta ruta entrega recomendaciones y propuestas aplicables. Ollama local seleccionó `qwen2.5-coder:1.5b`, pero una salida estructurada completa agotó el límite de 120 segundos en la máquina de prueba. Por ello se mantiene la respuesta rápida para esas solicitudes; el chat muestra ahora el motor que produjo cada respuesta para distinguirlo del proveedor configurado. La prueba de disponibilidad de Ollama se corrigió para abrir y cerrar el cliente HTTP en el mismo ciclo asíncrono.

## Aprobación de correcciones del asistente

Las sugerencias «Estados controlados», «Reglas para calificaciones» y «Unicidad de la clase asociativa» requieren valores, límites o referencias que no se pueden deducir con seguridad del dibujo. El botón ahora explica qué decisión falta y no envía una orden que terminaría sin acciones. «Identificadores ausentes» sí prepara propuestas tipadas de atributos UUID; cada propuesta se muestra antes de aprobarla y las acciones múltiples se encadenan para conservar el control de versión.

Al confirmar una acción UML, el backend ejecuta la mutación y publica un evento persistido `UML_EVENT` con el identificador del diagrama. El editor de todos los colaboradores recarga el modelo desde MongoDB. El chat muestra el estado aplicado o el error. Se comprobó el flujo de recomendación, confirmación de varias acciones y lectura de los atributos creados con bases PostgreSQL y MongoDB aisladas, eliminadas al terminar; también se probó el evento de actualización, la compilación y las pruebas del frontend.

## Límite arquitectónico pendiente

La escritura directa en MongoDB ocurre antes de confirmar ciertas transacciones SQL; una caída entre ambos pasos puede dejar deriva, aunque la reconciliación la detecta. La aplicación de un resultado de imagen también usa varias peticiones HTTP y puede quedar parcialmente aplicada si una petición posterior falla. Para garantizar atomicidad de esas operaciones se requiere una operación de aplicación de modelo en el backend con control de revisión e idempotencia, y un protocolo de compensación o publicación transaccional entre ambos almacenes.
