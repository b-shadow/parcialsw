# Fase 2 - Matriz de trazabilidad

| Requisito | Caso de uso | Modulo | Componente |
| --- | --- | --- | --- |
| RF-01 | CU-01 | Acceso, usuarios y seguimiento | Registro usuario |
| RF-02 | CU-02 | Acceso, usuarios y seguimiento | Autenticacion |
| RF-03 | CU-02 | Acceso, usuarios y seguimiento | JWT |
| RF-04 | CU-02 | Acceso, usuarios y seguimiento | Sesiones |
| RF-05 | CU-03 | Acceso, usuarios y seguimiento | Perfil |
| RF-06 | CU-04 | Acceso, usuarios y seguimiento | Administracion usuarios |
| RF-07 | CU-04 | Acceso, usuarios y seguimiento | Estados usuario |
| RF-08 | CU-04 | Acceso, usuarios y seguimiento | Roles globales |
| RF-09 | CU-06 | Acceso, usuarios y seguimiento | Bitacora |
| RF-10 | CU-05 | Acceso, usuarios y seguimiento | Reportes |
| RF-11 | CU-07 | Acceso, usuarios y seguimiento | Manual guiado |
| RF-12 | CU-08 | Proyectos y colaboracion | Gestion proyectos |
| RF-13 | CU-08 | Proyectos y colaboracion | Roles internos |
| RF-14 | CU-08 | Proyectos y colaboracion | Consulta proyectos |
| RF-15 | CU-08 | Proyectos y colaboracion | Edicion proyecto |
| RF-16 | CU-08 | Proyectos y colaboracion | Archivo/eliminacion |
| RF-17 | CU-09 | Proyectos y colaboracion | Invitaciones |
| RF-18 | CU-09 | Proyectos y colaboracion | Invitaciones |
| RF-19 | CU-09 | Proyectos y colaboracion | Permisos internos |
| RF-20 | CU-09 | Proyectos y colaboracion | Integrantes |
| RF-21 | CU-10 | Proyectos y colaboracion | Versiones |
| RF-22 | CU-10 | Proyectos y colaboracion | Historial |
| RF-23 | CU-10 | Proyectos y colaboracion | Restauracion |
| RF-24 | CU-11 | Proyectos y colaboracion | WebSocket |
| RF-25 | CU-11 | Proyectos y colaboracion | Sincronizacion |
| RF-26 | CU-11 | Modelado UML inteligente | Diagramas |
| RF-27 | CU-11 | Modelado UML inteligente | Clases UML |
| RF-28 | CU-11 | Modelado UML inteligente | Atributos UML |
| RF-29 | CU-11 | Modelado UML inteligente | Metodos UML |
| RF-30 | CU-11 | Modelado UML inteligente | Relaciones UML |
| RF-31 | CU-11 | Modelado UML inteligente | Tipos de relacion |
| RF-32 | CU-11 | Modelado UML inteligente | Posicion visual |
| RF-33 | CU-14 | Modelado UML inteligente | Validacion |
| RF-34 | CU-14 | Modelado UML inteligente | Recomendaciones IA |
| RF-35 | CU-18 | Modelado UML inteligente | Texto a UML |
| RF-36 | CU-18 | Modelado UML inteligente | Voz a UML |
| RF-37 | CU-12 | Modelado UML inteligente | Imagen a UML |
| RF-38 | CU-13 | Modelado UML inteligente | Importacion XMI |
| RF-39 | CU-13 | Modelado UML inteligente | Exportacion XMI |
| RF-40 | CU-15 | Transformacion y generacion | Transformador UML |
| RF-41 | CU-16 | Transformacion y generacion | Generador Spring Boot |
| RF-42 | CU-16 | Transformacion y generacion | Entidades JPA |
| RF-43 | CU-16 | Transformacion y generacion | CRUD REST |
| RF-44 | CU-16 | Transformacion y generacion | Validaciones/excepciones |
| RF-45 | CU-16 | Transformacion y generacion | Seguridad generada |
| RF-46 | CU-17 | Transformacion y generacion | Generador Flutter |
| RF-47 | CU-17 | Transformacion y generacion | Pantallas/servicios Flutter |
| RF-48 | CU-16/CU-17 | Transformacion y generacion | Registro procesos |
| RF-49 | CU-16/CU-17 | Transformacion y generacion | Exportacion artefactos |
| RF-50 | CU-16/CU-17 | Transformacion y generacion | Versiones generadas |

## Trazabilidad no funcional

| RNF | Modulo impactado | Mecanismo |
| --- | --- | --- |
| RNF-01 | Modelado UML | Canvas optimizado |
| RNF-02 | Proyectos y colaboracion | WebSocket por sala |
| RNF-03 | Modelado UML / IA | Procesamiento asincrono |
| RNF-04 | Generacion | Estados de proceso |
| RNF-05 | Acceso | Hash seguro |
| RNF-06 | Acceso | JWT |
| RNF-07 | Proyectos | Permisos internos |
| RNF-08 | Todos | Bitacora |
| RNF-09 | Todos | Validacion Pydantic/frontend |
| RNF-10 | Todos | PostgreSQL |
| RNF-11 | Proyectos/UML | Versionamiento |
| RNF-12 | Generacion | Separacion modelo/artefacto |
| RNF-13 | Proyectos | Modelo multi-proyecto |
| RNF-14 | Colaboracion | Salas WebSocket |
| RNF-15 | IA/Generacion | Servicios desacoplados |
| RNF-16 | Frontend | React web moderno |
| RNF-17 | UML | XMI |
| RNF-18 | Generacion backend | Spring Boot |
| RNF-19 | Generacion frontend | Flutter |
| RNF-20 | IA | Inferencia local |
| RNF-21 | IA | Proveedor local configurable |
| RNF-22 | IA | Pruebas offline |

