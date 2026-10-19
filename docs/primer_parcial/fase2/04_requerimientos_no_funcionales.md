# Fase 2 - Requerimientos no funcionales

## Rendimiento

| ID | Requerimiento | Criterio |
| --- | --- | --- |
| RNF-01 | El editor UML debe responder de forma fluida ante operaciones basicas. | Interaccion visual sin bloqueo perceptible en diagramas medianos. |
| RNF-02 | Los eventos colaborativos deben propagarse rapidamente. | Latencia objetivo menor a 500 ms en red local/controlada. |
| RNF-03 | La validacion UML debe ejecutarse sin bloquear la edicion. | Procesamiento asincrono o diferido. |
| RNF-04 | La generacion de codigo debe reportar progreso. | Estados: pendiente, en proceso, completado, fallido. |

## Seguridad

| ID | Requerimiento | Criterio |
| --- | --- | --- |
| RNF-05 | Las contrasenas deben almacenarse cifradas. | Hash seguro con sal. |
| RNF-06 | Los endpoints protegidos deben requerir JWT valido. | Rechazo de solicitudes no autenticadas. |
| RNF-07 | Las acciones de proyecto deben validar permisos internos. | Organizador/Editor segun accion. |
| RNF-08 | Toda accion sensible debe registrarse en bitacora. | Usuario, accion, fecha, modulo y resultado. |
| RNF-09 | Las entradas de usuario deben validarse. | Pydantic/backend y formularios/frontend. |

## Disponibilidad y recuperacion

| ID | Requerimiento | Criterio |
| --- | --- | --- |
| RNF-10 | Los datos de proyectos y diagramas deben persistirse. | PostgreSQL como fuente principal. |
| RNF-11 | El sistema debe permitir recuperar versiones anteriores. | Versiones y eventos persistidos. |
| RNF-12 | Fallos de generacion no deben corromper el modelo origen. | Separacion entre modelo y artefactos generados. |

## Escalabilidad

| ID | Requerimiento | Criterio |
| --- | --- | --- |
| RNF-13 | La arquitectura debe soportar multiples proyectos. | Separacion por proyecto y permisos. |
| RNF-14 | La colaboracion debe soportar multiples usuarios conectados. | Salas WebSocket por proyecto. |
| RNF-15 | Los motores IA/generacion deben poder ejecutarse como servicios separados. | Integracion por interfaces claras. |

## Compatibilidad

| ID | Requerimiento | Criterio |
| --- | --- | --- |
| RNF-16 | Frontend compatible con navegadores modernos. | Chrome, Edge, Firefox actuales. |
| RNF-17 | Intercambio UML mediante XMI. | Compatibilidad progresiva con Enterprise Architect. |
| RNF-18 | Backend generado debe usar Spring Boot y PostgreSQL. | Proyecto Maven/Gradle compilable. |
| RNF-19 | Frontend movil generado debe usar Flutter. | Proyecto analizable y construible. |

## Offline e IA local

| ID | Requerimiento | Criterio |
| --- | --- | --- |
| RNF-20 | La IA final debe ejecutarse sin APIs externas. | Inferencia local. |
| RNF-21 | El sistema debe permitir modelos locales reemplazables. | Configuracion por proveedor local. |
| RNF-22 | Las pruebas deben validar operacion offline. | Ejecucion sin llamadas externas obligatorias. |

