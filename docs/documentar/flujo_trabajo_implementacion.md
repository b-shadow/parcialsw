# 2.4. Flujo de Trabajo: Implementacion

## 2.4.1. Eleccion De Plataforma De Desarrollo Del Software

La plataforma CASE Inteligente se implementa como una aplicacion web modular con backend API, motor de IA local offline, persistencia relacional en PostgreSQL y generacion automatica de artefactos Spring Boot y Flutter desde modelos UML. El desarrollo se apoya en Git, GitHub, Docker, Postman y herramientas de validacion automatizada.

### 2.4.1.1. Lenguajes de programacion

#### Frontend Web

- Stack:
  - React 19.
  - TypeScript 5.6.
  - Vite 6.
  - React Router 7.
  - Zustand.
  - Axios.
  - Tailwind CSS.
  - JointJS mediante `@joint/core`.
  - Lucide React para iconografia.

- Motivos:
  - React permite construir una interfaz modular basada en componentes reutilizables.
  - TypeScript aporta tipado estatico para reducir errores en componentes, servicios, stores y contratos de API.
  - Vite agiliza el servidor de desarrollo, el build y la experiencia de trabajo local.
  - Zustand permite manejar estado global de forma liviana para sesion, proyectos y modelado UML.
  - Axios centraliza el consumo de la API REST del backend FastAPI.
  - Tailwind CSS permite construir una interfaz responsiva y consistente con bajo acoplamiento a componentes visuales externos.
  - JointJS se utiliza para el lienzo UML, permitiendo dibujar clases, relaciones, movimiento, zoom, paneo e interaccion visual.
  - Lucide React mantiene iconografia coherente en botones, menus y herramientas del editor.

- Librerias / convenciones:
  - React Router para navegacion entre Login, Registro, Gestion de Proyectos, Colaborativo, Editor UML, Generacion, Reportes, Manual y Perfil.
  - Axios para comunicacion con endpoints `/api/v1`.
  - Stores con Zustand para sesion, proyecto y estado del editor.
  - Componentes funcionales con hooks.
  - Tailwind CSS para layout, modo claro/oscuro y estilos reutilizables.
  - JointJS para representacion grafica del modelo UML en el canvas.
  - JWT almacenado y enviado al backend para rutas protegidas.
  - Vitest, Testing Library y jsdom para pruebas del frontend.
  - ESLint y TypeScript como controles de calidad.

- Compatibilidad web:
  - La aplicacion se ejecuta en navegadores modernos como Chrome, Edge y Firefox.
  - El despliegue productivo previsto sirve el frontend React compilado como contenido estatico.
  - En AWS, el frontend se publica en S3 privado y se distribuye mediante CloudFront.
  - El funcionamiento principal requiere conexion al backend para autenticacion, proyectos, diagramas, IA y generacion.
  - Puede evolucionar a PWA, pero actualmente el repositorio no incluye Service Worker ni configuracion PWA activa.

#### Frontend Movil Generado

- Stack generado:
  - Flutter.
  - Dart.
  - Estructura generada desde modelos UML internos.

- Motivos:
  - El sistema no mantiene una app movil manual como modulo principal; genera proyectos Flutter a partir del modelo UML.
  - Flutter permite producir una aplicacion movil multiplataforma con una sola base de codigo.
  - Dart facilita la generacion de modelos, servicios, pantallas, formularios y navegacion desde una estructura intermedia.
  - La generacion movil complementa la transformacion de UML a software funcional.

- Componentes generados:
  - Modelos Dart por entidad UML.
  - Servicios API.
  - Pantallas y formularios basicos.
  - Navegacion interna.
  - Estructura de proyecto exportable.

- Enfoque UX movil:
  - Interfaces simples derivadas de clases, atributos y relaciones UML.
  - Formularios generados desde atributos.
  - Servicios preparados para integrarse con el backend generado o configurado.
  - El alcance movil es generacion automatica, no una aplicacion movil administrativa desarrollada manualmente.

#### Backend Principal

- Stack:
  - Python 3.12.
  - FastAPI.
  - Uvicorn.
  - Pydantic y Pydantic Settings.
  - SQLAlchemy 2.
  - Alembic.
  - PostgreSQL con `psycopg`.
  - JWT con `python-jose`.
  - Passlib y bcrypt para hashing de contrasenas.
  - Python Multipart para carga de archivos.
  - NumPy, OpenCV headless, Pillow y Pytesseract para soporte de procesamiento de imagen UML.

- Motivos:
  - FastAPI permite construir una API REST modular, tipada y validada con Pydantic.
  - Python facilita integrar IA local, procesamiento de imagen, validadores UML y generadores de codigo.
  - SQLAlchemy separa el modelo relacional del motor de base de datos.
  - Alembic controla migraciones de esquema.
  - PostgreSQL ofrece consistencia transaccional para usuarios, proyectos, diagramas, relaciones, versiones, auditoria y artefactos generados.
  - JWT permite autenticacion stateless entre frontend y backend.
  - La modularizacion por paquetes mantiene separados acceso de usuarios, proyectos, modelado UML y generacion de software.

- Componentes:
  - API REST para el frontend web.
  - Autenticacion: registro, login y consulta del usuario actual.
  - Gestion de usuarios y roles.
  - Gestion de proyectos, miembros, permisos y versiones.
  - Editor UML con diagramas, clases, atributos, metodos, relaciones y elementos visuales.
  - Importacion/exportacion XML compatible con Enterprise Architect.
  - Validacion de modelos UML.
  - Transformacion de UML a modelo intermedio.
  - Generacion de backend Spring Boot.
  - Generacion de frontend Flutter.
  - IA local para texto, voz, imagen, validacion y apoyo a generacion.
  - Auditoria y bitacora mediante registros persistentes.

#### Motor de IA Local Offline

- Stack:
  - Python 3.12.
  - Paquete local `ai-engine`.
  - Motor actual: `CASE-UML-Local-RuleModel-v1`.
  - Perfil principal planificado/documentado: Qwen2.5-Coder-7B-Instruct cuantizado.
  - Perfil reducido planificado/documentado: Qwen2.5-Coder-1.5B-Instruct cuantizado.
  - Runtime previsto para modelos cuantizados: llama.cpp u Ollama local.
  - Fallback operativo: motor determinista Python/rule-engine.
  - Pydantic para contratos de entrada y salida.
  - NumPy, OpenCV, Pillow y Pytesseract para analisis de imagen.
  - RAG local con vector store simple y similitud coseno.

- Motivos:
  - El objetivo del proyecto es operar la IA sin depender de APIs externas.
  - La inferencia local protege la disponibilidad del sistema cuando no hay conexion a servicios de terceros.
  - El motor se puede reemplazar progresivamente por un modelo cuantizado mas fuerte sin cambiar los contratos del backend.
  - El fallback determinista permite mantener respuestas utiles mientras se especializa el modelo local.
  - OpenCV, Pillow y Pytesseract permiten extraer informacion de diagramas UML en imagen.

- Capacidades:
  - Texto a UML.
  - Voz a UML mediante normalizacion/procesamiento local preparado.
  - Imagen a UML.
  - Validacion UML.
  - Plan de software desde modelo UML.
  - Apoyo a generacion Spring Boot y Flutter.
  - Evaluacion offline.
  - Dataset semilla con dominios biblioteca, ventas, academico e inventario.

- Pipeline operativo:
  - Recepcion del prompt, audio, imagen o modelo UML.
  - Normalizacion del contenido de entrada.
  - Recuperacion de conocimiento local cuando aplica.
  - Ejecucion del motor local offline.
  - Construccion de respuesta estructurada.
  - Retorno al backend FastAPI.
  - Persistencia del proceso IA en PostgreSQL cuando corresponde.

- Serving de inferencia:
  - La IA se integra dentro del backend mediante `LocalAIService`.
  - Endpoints principales:
    - `GET /api/v1/ai/profile`
    - `POST /api/v1/ai/uml/text`
    - `POST /api/v1/ai/uml/voice`
    - `POST /api/v1/ai/uml/image`
    - `POST /api/v1/ai/uml/validate`
    - `POST /api/v1/ai/software/plan`
  - El contenedor `ai-engine` existe como componente verificable, pero la integracion funcional del producto se realiza desde el backend.
  - La politica del proyecto es no depender de Groq, OpenAI u otra API externa para la inferencia de producto.

#### Generadores de Software

- Backend generado:
  - Spring Boot.
  - Java.
  - Proyecto construido desde el modelo UML intermedio.
  - Generacion de estructura, modelos, controladores, servicios y artefactos descargables.

- Frontend movil generado:
  - Flutter.
  - Dart.
  - Generacion de modelos, servicios, pantallas, formularios y estructura exportable.

- Motivos:
  - El objetivo central del sistema es pasar de modelos UML a artefactos funcionales.
  - Mantener generadores separados permite evolucionar cada plataforma sin afectar el editor UML.
  - El modelo intermedio reduce el acoplamiento entre persistencia, editor visual y codigo generado.

### 2.4.1.2. Bases de Datos y Almacenamiento

#### Motor utilizado: PostgreSQL 16

- Razones:
  - PostgreSQL ofrece integridad transaccional para datos criticos de usuarios, proyectos, permisos, diagramas, relaciones y artefactos.
  - El modelo del sistema tiene relaciones claras entre usuarios, roles, proyectos, miembros, permisos, diagramas UML, clases, atributos, metodos, relaciones, versiones e historial.
  - SQLAlchemy y Alembic se integran directamente con PostgreSQL.
  - En produccion se define RDS PostgreSQL 16 con cifrado, backups y subnets privadas.
  - Permite consultas consistentes para auditoria, reportes y trazabilidad.

- Esquema logico implementado:
  - Acceso de usuarios:
    - `users`
    - `roles`
    - `user_roles`
    - `user_sessions`
    - `audit_logs`
  - Proyectos y colaboracion:
    - `projects`
    - `project_members`
    - `project_permissions`
    - `project_versions`
    - `project_invitations`
    - `collaboration_events`
  - Modelado UML:
    - `uml_diagrams`
    - `uml_classes`
    - `uml_attributes`
    - `uml_methods`
    - `uml_parameters`
    - `uml_relationships`
    - `uml_visual_elements`
    - `xmi_exchanges`
  - Generacion de software:
    - `uml_transformations`
    - `generated_backends`
    - `generated_frontends`
    - `generated_artifacts`
    - `ai_processes`

- Buenas practicas:
  - Migraciones con Alembic.
  - Modelos SQLAlchemy separados por modulo funcional.
  - Uso de UUID como identificadores principales.
  - Fechas de creacion y actualizacion mediante mixins.
  - Indices en campos de busqueda frecuente como usuario, proyecto, estado y tipo.
  - Restricciones de unicidad en relaciones relevantes.
  - Variables de entorno para credenciales y cadena de conexion.
  - RDS privado en produccion, sin exposicion publica directa.

#### Almacenamiento de artefactos

- Local:
  - Directorio `storage/generated`.
  - Volumen Docker `generated_artifacts` en despliegue con Compose.
  - Uso para proyectos Spring Boot y Flutter generados.

- Produccion:
  - Bucket S3 de artefactos.
  - Versionado habilitado.
  - Cifrado server-side AES256.
  - Referencias y metadatos persistidos en PostgreSQL.

- Uso:
  - Artefactos backend Spring Boot generados.
  - Artefactos frontend Flutter generados.
  - Manifiestos de generacion.
  - Archivos comprimidos o rutas de descarga.

- Acceso:
  - El backend gestiona generacion, consulta y descarga.
  - La base de datos guarda metadatos como nombre, ruta, tipo, checksum y relacion con la transformacion.
  - En AWS, S3 se utiliza como almacenamiento durable para artefactos.

### 2.4.1.3. Sistemas operativos

#### Servidor de produccion - AWS

- Plataforma definida:
  - Frontend React: S3 privado + CloudFront.
  - Backend FastAPI: EC2 con Docker detras de Application Load Balancer HTTPS.
  - Base de datos: Amazon RDS PostgreSQL 16 en subnets privadas.
  - Artefactos: S3 versionado y cifrado.
  - Logs: CloudWatch Logs.
  - DNS y certificados: Route 53 y ACM.

- Motivos:
  - EC2 permite un despliegue directo y controlado del backend Docker sin orquestador ECS.
  - RDS PostgreSQL permite operar la base de datos con backups, cifrado y administracion gestionada.
  - CloudFront mejora distribucion del frontend estatico.
  - S3 privado con CloudFront OAC evita exponer directamente el bucket frontend.
  - ALB centraliza HTTPS y balanceo hacia la instancia backend.
  - CloudWatch concentra logs del backend.

- Roles / servicios activos:
  - CloudFront para entrega del frontend.
  - S3 para frontend estatico.
  - S3 para artefactos generados.
  - Application Load Balancer para API.
  - EC2 con Docker para backend FastAPI.
  - RDS PostgreSQL para datos persistentes.
  - Route 53 para dominios.
  - ACM para certificados TLS.
  - CloudWatch para logs.

- Seguridad base:
  - RDS sin trafico publico.
  - Backend accesible solo desde ALB.
  - HTTP redirigido a HTTPS.
  - S3 frontend privado con acceso por CloudFront.
  - CORS configurado por variable de entorno.
  - JWT para autenticacion.
  - Variables de entorno para secretos.
  - S3 de artefactos cifrado y versionado.
  - Logs centralizados en CloudWatch.

- Dimensionamiento inicial referencial:
  - Backend EC2: `t3.small` inicial con Docker y volumen gp3 cifrado.
  - RDS: `db.t4g.micro`, 20 GB iniciales, cifrado y 7 dias de backup.
  - ALB publico para API.
  - CloudFront para frontend.
  - S3 para artefactos y frontend.

#### Clientes de desarrollo - Windows 10/11

- Entorno oficial de desarrollo:
  - Windows 10/11.
  - PowerShell.
  - Docker Desktop.
  - Python 3.12.
  - Node.js.
  - Git.
  - Postman.
  - Visual Studio Code.
  - Navegadores modernos.

- Herramientas instaladas:
  - Python 3.12 para backend y motor IA.
  - Node.js y npm para frontend React.
  - Docker Desktop para PostgreSQL local y builds de contenedores.
  - Git para control de versiones.
  - Postman para pruebas de API REST y JWT.
  - PostgreSQL local en contenedor Docker para desarrollo.
  - Terraform CLI para infraestructura AWS.
  - Enterprise Architect para validar/importar/exportar XML UML.

- Navegadores objetivo:
  - Google Chrome.
  - Microsoft Edge.
  - Mozilla Firefox.

### 2.4.1.4. Otros componentes y practicas

#### Despliegue y CI/CD

- Ambientes:
  - Desarrollo local.
  - Integracion mediante GitHub Actions.
  - Produccion en AWS.

- Infraestructura:
  - Terraform para AWS.
  - S3 + CloudFront para frontend.
  - EC2 + Docker + ALB para backend.
  - RDS PostgreSQL para base de datos.
  - S3 para artefactos generados.
  - Route 53 + ACM para dominios y HTTPS.

- Docker:
  - `docker-compose.yml` para PostgreSQL local.
  - `docker-compose.prod.yml` para backend, frontend, PostgreSQL y ai-engine.
  - Dockerfile de backend.
  - Dockerfile runtime de frontend.
  - Dockerfile de ai-engine.

- CI/CD:
  - GitHub Actions ejecuta validacion en cada push o pull request a `main`.
  - Backend:
    - Instalacion editable.
    - Instalacion de `ai-engine`.
    - Ruff.
    - Pytest.
  - AI engine:
    - Ruff.
    - Pytest.
  - Frontend:
    - `npm ci`.
    - `npm run lint`.
    - `npm test`.
    - `npm run build`.
  - Build de imagenes Docker:
    - Backend.
    - Frontend.
    - AI engine.

- Health checks:
  - Backend: `GET /health`.
  - Modulos:
    - `GET /api/v1/acceso-usuarios/health`
    - `GET /api/v1/proyectos-colaboracion/health`
    - `GET /api/v1/modelado-uml/health`
    - `GET /api/v1/generacion-software/health`
  - PostgreSQL local con `pg_isready`.
  - ALB health check hacia `/health`.

#### Control de versiones

- Plataforma:
  - Git.
  - GitHub.

- Estrategia:
  - Rama principal `main`.
  - Ramas cortas por funcionalidad, correccion o documentacion.
  - Pull requests antes de integrar cambios relevantes.
  - Validacion automatica por GitHub Actions.

- Convenciones sugeridas:
  - `feat/` para funcionalidades.
  - `fix/` para correcciones.
  - `docs/` para documentacion.
  - `refactor/` para reestructuracion interna.
  - `chore/` para mantenimiento.

- Commits:
  - Mensajes claros y trazables.
  - Preferencia por Conventional Commits:
    - `feat: ...`
    - `fix: ...`
    - `docs: ...`
    - `refactor: ...`
    - `test: ...`
    - `chore: ...`

#### Entornos de Desarrollo

- Visual Studio Code:
  - Entorno principal para frontend, backend, IA y documentacion.
  - Extensiones recomendadas:
    - Python.
    - Pylance.
    - ESLint.
    - Tailwind CSS IntelliSense.
    - GitLens.
    - REST Client.
    - Docker.
    - Terraform.

- Postman:
  - Prueba de endpoints REST.
  - Login y manejo de JWT.
  - Validacion de modulos de usuarios, proyectos, UML, IA y generacion.
  - Colecciones por modulo funcional.

- Enterprise Architect:
  - Modelado UML.
  - Verificacion de importacion/exportacion XML.
  - Comparacion de diagramas de clases, secuencia, comunicacion, estado y paquetes.

- Base de datos:
  - PostgreSQL mediante Docker Desktop en desarrollo.
  - Herramientas compatibles como pgAdmin, DBeaver o DataGrip para inspeccion.

- Infraestructura:
  - Terraform para provisionamiento AWS.
  - AWS Console para verificacion operacional.

#### Observabilidad y operacion

- Logs:
  - Backend FastAPI/Uvicorn.
  - Frontend en navegador y build.
  - Docker logs en local.
  - CloudWatch Logs en produccion.

- Metricas:
  - Salud del backend mediante `/health`.
  - Estado de modulos por endpoints health.
  - CPU, memoria, red y errores en AWS.
  - RDS: conexiones, almacenamiento, CPU y backups.

- Bitacora:
  - Tabla `audit_logs`.
  - Registro de usuario, modulo, accion, resultado, detalle y metadatos.
  - Trazabilidad sobre acciones de usuarios, proyectos, modelado, generacion e IA.

- Errores:
  - Manejo de errores HTTP desde FastAPI.
  - Mensajes de importacion/exportacion UML hacia el frontend.
  - Posible integracion futura con Sentry u otra herramienta de tracking.

#### Seguridad y cumplimiento

- Variables por entorno:
  - `.env` local.
  - Variables del contenedor en Docker Compose.
  - Variables del contenedor backend en EC2.
  - GitHub Secrets para CI/CD cuando aplique.

- Secretos:
  - `DATABASE_URL`.
  - `JWT_SECRET_KEY`.
  - Credenciales PostgreSQL.
  - Variables AWS.
  - Nombres de buckets S3.

- Autenticacion:
  - JWT.
  - Login mediante `/api/v1/auth/login`.
  - Registro mediante `/api/v1/auth/register`.
  - Consulta de usuario actual mediante `/api/v1/auth/me`.

- Autorizacion:
  - Roles de usuario.
  - Membresias de proyecto.
  - Permisos por proyecto.
  - Validaciones de acceso antes de consultar o modificar recursos.

- CORS y HTTPS:
  - CORS configurado por variable `CORS_ORIGINS`.
  - HTTPS en produccion mediante ACM y ALB/CloudFront.
  - HTTP redirigido a HTTPS.

- Archivos:
  - Carga controlada mediante FastAPI y `python-multipart`.
  - Artefactos generados fuera de la base de datos.
  - Metadatos persistidos para trazabilidad.

- Auditoria:
  - Registro de acciones principales en `audit_logs`.
  - Registro de procesos IA en `ai_processes`.
  - Registro de importaciones/exportaciones XML en `xmi_exchanges`.

#### CDN, dominios y redes

- Frontend web:
  - Build React publicado en bucket S3 privado.
  - Distribucion mediante CloudFront.
  - Acceso al bucket mediante Origin Access Control.

- API:
  - Backend FastAPI en EC2 con Docker.
  - Exposicion publica mediante Application Load Balancer HTTPS.
  - Target group HTTP hacia puerto 8000.

- TLS:
  - Certificados ACM.
  - Validacion DNS en Route 53.
  - Politica TLS moderna en CloudFront.

- DNS:
  - Route 53 para `frontend_domain` y `api_domain`.
  - Registros alias hacia CloudFront y ALB.

- Base de datos:
  - RDS PostgreSQL en subnets privadas.
  - Acceso restringido al security group del backend.

- Almacenamiento:
  - S3 frontend privado.
  - S3 artefactos con versionado y cifrado.

#### Compatibilidad y soporte

- Web:
  - Chrome reciente.
  - Edge reciente.
  - Firefox reciente.

- Backend:
  - Python 3.12.
  - Linux en contenedor/produccion.
  - Windows 10/11 para desarrollo local.

- Base de datos:
  - PostgreSQL 16.

- IA local:
  - Ejecucion Python local.
  - Preparado para modelos cuantizados con runtime local.
  - Inferencia de producto sin APIs externas.

- Generacion:
  - Spring Boot/Java como backend generado.
  - Flutter/Dart como frontend movil generado.

#### Gestion de configuracion

- Local:
  - `backend/.env`.
  - `frontend/.env.example`.
  - Variables de entorno para Vite:
    - `VITE_API_BASE_URL`
    - `VITE_WS_BASE_URL`

- Produccion:
  - Variables generadas en `/opt/case-inteligente/backend.env` dentro de EC2.
  - Terraform variables.
  - GitHub Secrets.
  - AWS Systems Manager o Secrets Manager como evolucion recomendada.

- Datos sensibles:
  - No deben quedar hardcodeados en el repositorio.
  - JWT, base de datos y credenciales AWS se manejan por variables.

- Feature flags:
  - Pueden incorporarse para activar gradualmente IA avanzada, exportacion XML, generacion Spring Boot, generacion Flutter y funciones colaborativas.

#### Licencias y componentes de terceros

- Auditoria OSS:
  - Revision periodica de dependencias npm y Python.
  - Uso de `npm audit` cuando aplique.
  - Revision de licencias y vulnerabilidades.

- Componentes externos registrados:
  - Frontend:
    - React.
    - TypeScript.
    - Vite.
    - Tailwind CSS.
    - Axios.
    - Zustand.
    - React Router.
    - JointJS.
    - Lucide React.
  - Backend:
    - FastAPI.
    - Uvicorn.
    - Pydantic.
    - SQLAlchemy.
    - Alembic.
    - Psycopg.
    - python-jose.
    - Passlib.
    - bcrypt.
  - IA local:
    - ai-engine.
    - NumPy.
    - OpenCV.
    - Pillow.
    - Pytesseract.
    - Runtime previsto: llama.cpp u Ollama local.
    - Perfil objetivo: Qwen2.5-Coder cuantizado.
  - Base de datos:
    - PostgreSQL.
    - Amazon RDS PostgreSQL.
  - Infraestructura:
    - Docker.
    - AWS EC2.
    - AWS ALB.
    - AWS S3.
    - AWS CloudFront.
    - AWS Route 53.
    - AWS ACM.
    - AWS CloudWatch.
    - Terraform.
    - GitHub Actions.
  - Herramientas:
    - Git.
    - GitHub.
    - Postman.
    - Enterprise Architect.

#### Pruebas y calidad

- Frontend:
  - ESLint.
  - TypeScript build.
  - Vitest.
  - Testing Library.
  - Build Vite.

- Backend:
  - Ruff.
  - Pytest.
  - Pruebas de endpoints con `httpx`.
  - Migraciones Alembic.

- IA local:
  - Ruff.
  - Pytest.
  - Evaluacion offline.
  - Health local del motor.

- Integracion:
  - Postman para validar endpoints REST.
  - Pruebas manuales del flujo login, proyectos, editor UML, importacion/exportacion XML, validacion y generacion.
  - Health checks despues del despliegue.

- Calidad operativa:
  - Pull requests.
  - Revision de codigo.
  - CI en GitHub Actions.
  - Builds Docker.
  - Validacion de dependencias.
  - Documentacion tecnica en `docs/`.
