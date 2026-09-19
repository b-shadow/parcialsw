# Fase 2 - Analisis del sistema

## Proposito

Formalizar el problema, alcance y comportamiento esperado de la plataforma CASE inteligente antes de iniciar fases de diseno de datos e implementacion funcional.

## Problema identificado

El desarrollo tradicional obliga a trasladar manualmente requerimientos hacia modelos UML, arquitectura, codigo fuente y aplicaciones ejecutables. Ese traslado manual produce:

- Tiempo elevado de desarrollo.
- Errores de interpretacion entre analisis, diseno e implementacion.
- Diferencias entre diagramas y codigo final.
- Dificultad para mantener trazabilidad de cambios.
- Necesidad de conocimiento especializado en varias tecnologias.
- Baja automatizacion entre la etapa de modelado y la construccion de software.

La plataforma resuelve este problema usando UML como fuente estructurada de diseno, colaboracion en tiempo real, IA local offline y generadores deterministas de software.

## Alcance funcional

Dentro del alcance:

- Registro, autenticacion y administracion de usuarios.
- Roles globales e internos de proyecto.
- Creacion y administracion de proyectos colaborativos.
- Gestion de integrantes y permisos internos.
- Versionamiento de modelos y cambios.
- Editor de diagramas de clases UML.
- Persistencia de diagramas, clases, atributos, metodos y relaciones.
- Colaboracion en tiempo real mediante WebSockets.
- Generacion UML desde texto, voz e imagen.
- Validacion UML asistida por IA local offline.
- Importacion y exportacion XMI.
- Transformacion de UML hacia estructura intermedia.
- Generacion de backend Spring Boot.
- Generacion de frontend movil Flutter.
- Registro de bitacora, auditoria, procesos IA y generaciones.

Fuera del alcance inicial:

- Soporte completo para todos los tipos de diagramas UML.
- Edicion nativa de codigo fuente generado dentro de la plataforma.
- Marketplace de plantillas de terceros.
- Despliegue automatico del software generado en ambientes externos.
- Entrenamiento final de modelos propios en Fase 2.
- Alta disponibilidad productiva completa antes de Fase 11.

## Flujo general

1. Usuario se registra o inicia sesion.
2. Crea un proyecto o ingresa a uno existente.
3. Si crea el proyecto, queda como Organizador interno.
4. Invita integrantes y asigna permisos.
5. Crea o importa un diagrama UML.
6. Edita el modelo manualmente, por texto, voz o imagen.
7. Los cambios se sincronizan por WebSocket.
8. El backend valida permisos y registra eventos.
9. El modelo se guarda y versiona.
10. La IA local valida o propone mejoras.
11. El motor de transformacion interpreta el UML.
12. Se genera backend Spring Boot.
13. Se genera frontend Flutter.
14. Se registra la generacion y queda disponible para exportacion.

## Dependencias tecnologicas

- Frontend React + TypeScript + Vite + Tailwind.
- Backend FastAPI + SQLAlchemy + Pydantic.
- PostgreSQL.
- WebSockets.
- Motor UML interno desacoplado del canvas.
- Motor IA local offline.
- Generadores Spring Boot y Flutter.
- Docker para servicios locales.
- AWS para despliegue final.

## Restricciones principales

- La IA final no debe depender de APIs externas.
- La generacion base debe ser determinista.
- La arquitectura debe organizarse por los cuatro paquetes funcionales.
- El backend FastAPI administra la plataforma; Spring Boot es objetivo generado.
- El modelo UML persistido debe permitir reconstruccion, versionamiento y trazabilidad.
- Los permisos internos de proyecto deben diferenciarse de roles globales.

