# Arquitectura Integrada de Produccion

## Componentes

La arquitectura final integra:

- Frontend React + Tailwind.
- Backend FastAPI.
- PostgreSQL.
- WebSockets colaborativos.
- Motor UML.
- Motor IA local offline.
- Generador Spring Boot.
- Generador Flutter.
- Almacenamiento de artefactos.

## Paquetes funcionales

Se conserva la division original:

- Gestion de acceso, usuarios y seguimiento.
- Gestion de proyectos y colaboracion.
- Modelado UML inteligente.
- Transformacion y generacion automatica de software.

## Flujo integrado

1. El usuario accede al frontend por dominio propio.
2. El frontend consume FastAPI por HTTPS.
3. FastAPI valida JWT y autorizacion por proyecto.
4. El editor UML usa REST y WebSocket.
5. La IA local offline apoya generacion, validacion y modificacion UML.
6. Los generadores producen Spring Boot y Flutter.
7. PostgreSQL persiste usuarios, proyectos, UML, auditoria y generaciones.
8. S3 almacena artefactos generados y respaldos.
