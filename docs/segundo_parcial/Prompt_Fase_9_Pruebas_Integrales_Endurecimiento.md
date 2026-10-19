# PROMPT FASE 9: PRUEBAS INTEGRALES Y ENDURECIMIENTO

## 0. Instruccion maestra

Implementar la Fase 9 de la segunda parte de CASE Inteligente: verificar, endurecer y cerrar el producto completo mediante pruebas automatizadas y manuales reproducibles, correccion de defectos, validacion de artefactos generados y evidencia trazable.

Esta fase no consiste en escribir un informe afirmando que el sistema funciona. Debe ejecutar el sistema real, encontrar fallos, corregirlos, volver a ejecutar las suites y demostrar que las capacidades del primer y segundo parcial funcionan juntas.

El cierre abarca:

- autenticacion, usuarios, roles y perfil;
- proyectos, miembros y permisos;
- UML manual, importacion, exportacion y validacion;
- deteccion UML desde imagen;
- IA unica con Ollama/Qwen y fallback;
- conversacion colaborativa y solicitudes compuestas;
- especificacion funcional de metodos;
- generacion coordinada Spring Boot y Flutter;
- editor de estilos y fidelidad de preview;
- versiones, restauracion y bitacora;
- notificaciones persistentes y Web Push;
- PWA movil reducida y lectura offline;
- migraciones, contenedores, seguridad y operacion.

No sustituir pruebas por mocks en los limites que precisamente deben verificarse. No declarar aprobado un comando que no se ejecuto. No ocultar fallos intermitentes mediante reintentos ilimitados. No cambiar expectativas correctas solo para que una prueba pase.

---

## 1. Resultado funcional buscado

Al finalizar:

1. Existe una matriz que relaciona requisitos, casos de uso, fases, pruebas y evidencia.
2. Los 18 casos de uso del sistema tienen al menos un flujo satisfactorio automatizado o manual verificable.
3. Los flujos criticos tienen escenarios alternos, permisos y errores.
4. Backend y AI Engine pasan Ruff y Pytest.
5. Frontend pasa ESLint, Vitest y build de produccion.
6. Las migraciones funcionan desde base vacia y desde datos anteriores.
7. PostgreSQL real valida UUID, JSONB, locks y concurrencia.
8. WebSocket conserva orden, aislamiento e idempotencia.
9. Ollama disponible, no disponible, lento e invalido tienen comportamiento definido.
10. Solicitudes naturales con una o varias acciones producen planes correctos.
11. Imagenes variadas se procesan sin clases precargadas ni resultados fabricados.
12. Metodos UML alimentan contratos coherentes de Spring Boot y Flutter.
13. Cada backend generado compila, inicia y ejecuta operaciones representativas.
14. Cada Flutter generado supera formato, analyze, test y build soportado.
15. Multiplicidades y association classes producen IDs y selectores coherentes.
16. El preview y el Flutter generado consumen la misma configuracion normalizada.
17. Una restauracion recupera UML, metodos y estilo sin borrar trazabilidad.
18. Notificaciones no se duplican y abren el destino correcto.
19. La PWA funciona en viewports moviles y degrada correctamente offline.
20. No se filtran secretos, credenciales ni archivos locales.
21. Docker productivo construye e inicia con health/readiness correctos.
22. CI reproduce los gates principales sin depender de estado local oculto.
23. Todos los defectos bloqueantes quedan corregidos y con prueba de regresion.
24. Las limitaciones restantes quedan documentadas con impacto y plan, no ocultas.

---

## 2. Alineacion obligatoria con las fases 1 a 8

### 2.1. Fase 1

Verificar contratos Pydantic/TypeScript, restricciones SQL, snapshot V2, migraciones, aislamiento por proyecto y compatibilidad V1.

### 2.2. Fase 2

Verificar proveedor Ollama/Qwen, fallback, esquemas de salida, timeouts, cancelacion, diagnosticos y ausencia de respuestas falsas.

### 2.3. Fase 3

Verificar conversacion unica, memoria compartida, secuencias, idempotencia, multiples colaboradores, confirmaciones y reconexion.

### 2.4. Fase 4

Verificar especificaciones funcionales de metodos, referencias, reglas, contratos backend/Flutter y compatibilidad de metodos antiguos.

### 2.5. Fase 5

Verificar `GenerationPlan`, modelo intermedio, generacion coordinada, compilacion real y ejecucion con comandos documentados.

### 2.6. Fase 6

Verificar persistencia de tema, editor, preview, accesibilidad, fidelidad y aplicacion exacta en el ZIP Flutter.

### 2.7. Fase 7

Verificar snapshots, restauracion atomica, respaldos, actividad, auditoria, outbox, preferencias, Web Push y deep links.

### 2.8. Fase 8

Verificar manifiesto, service worker, instalacion, responsive, visor readonly, IndexedDB, offline, suspension y retorno.

No considerar aprobada una fase por sus pruebas aisladas si el flujo completo contradice el contrato de otra fase.

---

## 3. Principios de calidad

### 3.1. Evidencia sobre intuicion

Toda afirmacion importante debe enlazar a un comando, prueba, captura, reporte o inspeccion reproducible.

### 3.2. Piramide equilibrada

- Muchas pruebas unitarias rapidas.
- Pruebas de integracion sobre limites reales.
- Pruebas API/contrato.
- Un conjunto menor de E2E criticos.
- Verificaciones manuales solo donde el navegador/dispositivo lo requiera.

### 3.3. Determinismo

Las suites obligatorias no dependen de respuestas variables de un LLM. El comportamiento de Ollama real se evalua en una suite separada con criterios semanticos y artefactos registrados.

### 3.4. PostgreSQL real

No usar SQLite para concluir que JSONB, locks, constraints, migraciones o concurrencia funcionan.

### 3.5. Fallo visible

Un test omitido por falta de herramienta debe aparecer como `SKIPPED` justificado y no como aprobado.

### 3.6. Correccion antes de cierre

Cada defecto critico o alto descubierto se corrige en esta fase y recibe prueba de regresion.

---

## 4. Herramientas obligatorias y recomendadas

### Backend y AI Engine

- Python 3.12 conforme a `pyproject.toml`.
- Pytest.
- Ruff.
- HTTPX/TestClient para HTTP.
- PostgreSQL 16 mediante Docker.
- Alembic.
- SQLAlchemy 2.

Agregar solo cuando sea necesario:

- `pytest-cov` para cobertura.
- `pytest-xdist` solo despues de probar aislamiento.
- `testcontainers` si simplifica PostgreSQL en CI, sin duplicar Docker Compose.
- `hypothesis` para propiedades criticas bien definidas.

### Frontend

- TypeScript compiler.
- ESLint.
- Vitest.
- React Testing Library.
- `@playwright/test` para E2E, responsive y PWA.
- Axe integrado con Playwright o Testing Library para accesibilidad automatica.

### Artefactos generados

- JDK y Maven Wrapper/Maven segun salida del generador.
- Docker y Docker Compose para PostgreSQL generado.
- Flutter SDK estable fijado/documentado.
- `dart format`.
- `flutter analyze`.
- `flutter test`.
- `flutter build web` como build portable minimo.

### Seguridad y operacion

- Busqueda de secretos local y en CI.
- `pip-audit` y `npm audit` como reportes controlados, sin actualizaciones ciegas.
- Trivy u otra herramienta disponible para imagenes Docker, si se incorpora.
- Lighthouse para PWA/performance/accessibility.

No introducir cinco herramientas equivalentes. Cada herramienta debe tener un proposito y comando documentado.

---

## 5. Capas de prueba

### Nivel 1: unitarias

Funciones puras, normalizadores, validadores, parsers, reducers, stores y componentes pequenos.

### Nivel 2: integracion

Repositorio-servicio-base, migraciones, locks, filesystem generado, IndexedDB y WebSocket manager.

### Nivel 3: contratos

OpenAPI, Pydantic/TypeScript, eventos WebSocket, snapshots, `GenerationPlan`, manifiestos y deep links.

### Nivel 4: funcional API

Flujos autenticados y permisos mediante HTTP real o cliente ASGI con PostgreSQL dedicado.

### Nivel 5: E2E navegador

React + backend + PostgreSQL + AI controlada, usando Playwright.

### Nivel 6: compilacion externa

Generar, extraer, compilar y ejecutar Spring Boot/Flutter.

### Nivel 7: manual critico

Dispositivos, Push real, instalacion PWA, Ollama real, fotos fisicas y experiencia tactil.

---

## 6. Clasificacion de suites

Definir marcadores o proyectos:

```text
unit
integration
postgres
api
websocket
ai_contract
ollama_real
generator
generated_compile
e2e
pwa
security
slow
manual
```

La suite por defecto de CI incluye todas salvo `ollama_real`, `manual` y pruebas que exijan Flutter si el runner no lo instala. Crear un job especifico para Flutter en vez de omitirlo indefinidamente.

---

## 7. Ambientes reproducibles

### 7.1. Unitario

- Sin red.
- Sin Ollama real.
- Filesystem temporal.
- Reloj/UUID controlables donde sea necesario.

### 7.2. Integracion local

- PostgreSQL 16 en puerto aislado.
- Base exclusiva de prueba.
- Backend con secretos ficticios fuertes.
- Directorio temporal para artefactos.

### 7.3. E2E

- Docker Compose dedicado o stack local controlado.
- Frontend build/preview de produccion.
- Backend con migracion aplicada.
- AI provider stub compatible o rule engine determinista.

### 7.4. Ollama real

- Perfil separado.
- Modelo y tag documentados.
- Temperatura baja/configuracion determinista cuando sea posible.
- Timeout amplio pero finito.
- Resultados evaluados semanticamente.

### 7.5. Artefactos generados

- Carpeta temporal nueva por caso.
- PostgreSQL generado con nombre/puertos aislados.
- Sin editar archivos generados antes de compilar.

---

## 8. Configuracion de pruebas

Crear archivos de ejemplo sin secretos:

```text
.env.test.example
backend/.env.test.example
frontend/.env.test.example
```

Variables minimas:

```dotenv
APP_ENV=test
DATABASE_URL=postgresql+psycopg://case_test:case_test@127.0.0.1:55433/case_test
JWT_SECRET_KEY=test-only-secret-with-safe-length
CORS_ORIGINS=["http://127.0.0.1:4173"]
AI_PROVIDER=rule_engine
GENERATED_STORAGE_ROOT=./.test-artifacts
```

No usar la base de desarrollo. El entorno debe rechazar nombres de base que no parezcan de prueba cuando se ejecuten fixtures destructivos.

---

## 9. Datos y fixtures canonicos

Crear builders/fixtures reutilizables:

- administrador;
- organizador;
- editor;
- visualizador;
- usuario sin membresia;
- proyecto A y proyecto B;
- diagrama simple Cliente-Pedido;
- diagrama Academico Estudiante-Curso-Inscripcion;
- diagrama Biblioteca con 1:1, 1:N y N:M;
- metodos CRUD;
- metodo de negocio `inscribirEstudiante`;
- tema claro/oscuro;
- conversacion con secuencias;
- version V1 y V2;
- notificaciones y suscripciones.

Los ids pueden ser fijos en fixtures para snapshots legibles. No compartir filas mutables entre tests.

---

## 10. Aislamiento de datos

- Transaccion por prueba cuando no se pruebe commit real.
- Truncado controlado entre suites que requieren varios commits.
- Base distinta para migraciones.
- Directorio temporal por generacion.
- Puerto distinto por backend generado.
- Usuario de navegador nuevo por escenario E2E.
- IndexedDB y service worker limpiados por contexto Playwright.

No depender del orden de pruebas.

---

## 11. Tiempo, UUID y aleatoriedad

- Centralizar reloj UTC cuando afecte expiraciones.
- Inyectar UUID/idempotency keys en pruebas.
- Fijar seed de ruido de imagen.
- Registrar seed al fallar propiedad aleatoria.
- No comparar timestamps exactos generados por DB salvo tolerancia.
- No congelar el tiempo de forma que oculte locks o expiraciones reales.

---

## 12. Matriz de los 18 casos de uso

Mantener los identificadores existentes:

| CU | Caso de uso | Nivel minimo |
| --- | --- | --- |
| CU-01 | Registrar cuenta de usuario | API + E2E |
| CU-02 | Gestionar autenticacion | API + seguridad + E2E |
| CU-03 | Gestionar perfil propio | API + componente |
| CU-04 | Gestionar usuarios y roles globales | API permisos + E2E admin |
| CU-05 | Consultar reportes | API agregacion + responsive |
| CU-06 | Consultar bitacora | API permisos + paginacion |
| CU-07 | Consultar manual guiado mediante asistente | contrato IA + E2E |
| CU-08 | Gestionar proyectos de desarrollo | API + E2E |
| CU-09 | Gestionar integrantes y permisos | API permisos + notificacion |
| CU-10 | Gestionar versiones y cambios | PostgreSQL + E2E concurrencia |
| CU-11 | Crear y editar diagramas de clases UML | servicio + WebSocket + E2E |
| CU-12 | Generar diagramas UML desde imagenes | corpus imagen + API |
| CU-13 | Importar y exportar modelos UML | round-trip XMI |
| CU-14 | Validar diagramas UML | reglas + propiedad |
| CU-15 | Transformar modelo UML | contrato intermedio |
| CU-16 | Generar backend Spring Boot | generacion + compile + smoke |
| CU-17 | Generar frontend movil Flutter | generacion + analyze/test/build |
| CU-18 | Ejecutar generacion mediante IA local | provider matrix + E2E |

Agregar casos de aceptacion del segundo parcial como extensiones, no renumerar silenciosamente los CU originales.

---

## 13. Matriz de trazabilidad

Crear un archivo fuente, por ejemplo:

```text
docs/segundo_parcial/fase9/matriz_trazabilidad.md
```

Columnas:

- requisito/caso de uso;
- fase de origen;
- riesgo;
- prueba automatizada;
- prueba manual;
- datos usados;
- ambiente;
- resultado;
- evidencia;
- defecto relacionado.

Ningun requisito critico queda solo con `revision visual`.

---

## 14. Calidad de pruebas existentes

Auditar las pruebas actuales antes de ampliar:

- Detectar asserts de existencia sin comportamiento.
- Detectar mocks que impiden probar integracion.
- Detectar nombres heredados `phase8/phase9` que ya no reflejan segunda parte.
- Detectar fixtures dependientes de archivos locales no versionados.
- Detectar pruebas que pasan sin ejecutar el codigo objetivo.
- Detectar `except` demasiado amplios.
- Detectar tests que solo verifican strings generados.

Conservar pruebas utiles. Mejorarlas sin borrar cobertura historica.

---

## 15. Pruebas unitarias backend

Cubrir por modulo:

- validadores de usuario;
- permisos globales y de proyecto;
- normalizacion UML;
- multiplicidades;
- association classes;
- especificaciones de metodos;
- snapshots V1/V2;
- temas Flutter;
- estados de acciones IA;
- deep links;
- politicas de notificacion;
- transformacion a modelo intermedio;
- nombres de archivos/paquetes generados.

Cada bug corregido recibe un caso minimo que fallaba antes.

---

## 16. Pruebas de modelos y restricciones SQL

Con PostgreSQL validar:

- UUID nativo.
- JSONB.
- `CHECK` de estados.
- `UNIQUE` por proyecto/secuencia.
- `UNIQUE` de idempotencia parcial.
- FKs y `ON DELETE`.
- timestamps timezone-aware.
- una conversacion por proyecto.
- una especificacion por metodo.
- un tema activo por proyecto.
- una version por numero.
- una notificacion por dedup key/destinatario.

No aceptar que solo Pydantic proteja restricciones persistentes.

---

## 17. Pruebas de migracion

### 17.1. Base vacia

```text
upgrade head
current
check
```

### 17.2. Base del primer parcial

1. Aplicar revision anterior.
2. Insertar usuarios, proyectos, UML, versiones y artefactos.
3. Aplicar todas las migraciones nuevas.
4. Verificar datos y relaciones.
5. Usar funcionalidades nuevas.

### 17.3. Downgrade controlado

En base desechable:

- `downgrade -1` por cada revision nueva cuando sea reversible;
- comprobar que tablas anteriores siguen;
- volver a `upgrade head`.

### 17.4. SQL offline

Generar SQL y revisar operaciones destructivas, defaults, locks y orden.

### 17.5. Heads

`alembic heads` debe devolver un solo head salvo estrategia de merge documentada.

---

## 18. Pruebas OpenAPI y contratos

- Generar `openapi.json` desde la app.
- Verificar rutas obligatorias.
- Verificar `response_model`.
- Verificar seguridad Bearer.
- Verificar enums, limites y formatos UUID/date-time.
- Verificar que ejemplos no contienen secretos.
- Comparar fixtures TypeScript con JSON real.
- Detectar breaking changes respecto del contrato versionado.

Si se incorpora generacion automatica de tipos, no mezclar tipos generados y manuales contradictorios.

---

## 19. Pruebas de autenticacion

- Registro valido.
- Correo duplicado.
- Email invalido.
- Password fuera de politica.
- Login correcto/incorrecto.
- Usuario inactivo.
- Token ausente, alterado, expirado.
- Acceso de admin/no admin.
- Logout/limpieza frontend.
- Rutas protegidas.
- CORS de origen permitido/no permitido.
- Rate limiting si existe.
- No revelar si un correo existe cuando la politica lo evite.

---

## 20. Pruebas de proyectos, miembros y roles

- Crear/actualizar/archivar proyecto.
- Propietario es organizador.
- Agregar editor.
- Cambiar rol.
- Remover miembro.
- No remover ultimo organizador/propietario.
- Usuario externo no lista proyecto.
- Editor no administra miembros.
- Invitacion idempotente.
- Notificacion al invitado.
- Revocacion invalida WebSocket/cache.

Crear tabla de permisos efectiva por endpoint y probar cada rol.

---

## 21. Pruebas UML manuales

- Crear diagrama.
- Clase vacia sin metodo visual fantasma.
- Agregar/editar/eliminar atributo.
- Agregar/editar/eliminar metodo y parametros.
- Agregar relaciones soportadas.
- Multiplicidades validas/invalidas.
- Association class.
- Movimiento y persistencia visual.
- Version logica/optimistic concurrency.
- Eliminaciones en cascada correctas.
- Nombres largos y Unicode permitido por dominio.
- Referencia a clase de otro diagrama rechazada.

---

## 22. Pruebas XMI

Corpus:

- exportacion propia;
- Enterprise Architect representativo;
- clases y atributos;
- metodos/parametros;
- herencia;
- asociaciones y multiplicidades;
- association class si el formato lo soporta;
- namespaces variados;
- XMI invalido;
- XML malicioso/XXE.

Prueba round-trip:

```text
modelo interno -> XMI -> importar -> modelo normalizado
```

Comparar semantica, no ids o formato textual exacto.

---

## 23. Pruebas del validador UML

- Clase sin nombre.
- Duplicados.
- Tipo desconocido.
- Relacion huerfana.
- Multiplicidad mal formada.
- Ciclo de herencia.
- Association class incompleta.
- Metodo con parametro duplicado.
- Contrato funcional con referencia externa.
- Warnings vs errors.
- Orden determinista de diagnosticos.

Propiedades:

- validar no muta el modelo;
- validar dos veces produce igual resultado;
- todo error referencia recurso existente o ruta comprensible.

---

## 24. Matriz de proveedor IA

| Escenario | Resultado esperado |
| --- | --- |
| Ollama saludable + Qwen disponible | Usa Ollama |
| Ollama detenido | Fallback o error explicito |
| Modelo ausente | Diagnostico de modelo, no 500 generico |
| Timeout | Cancela, no corrompe conversacion |
| JSON invalido | Repara/reintenta acotado o rechaza |
| Respuesta vacia | Estado failed coherente |
| Respuesta con accion no permitida | Validador rechaza |
| Rule engine | Resultado determinista |
| Usuario cancela | Mensaje/action queda cancelled |

Separar tests contractuales con fake HTTP de evaluacion real de Qwen.

---

## 25. Corpus de lenguaje natural

Crear dataset versionado con:

- imperativos formales;
- lenguaje coloquial;
- dictado con muletillas;
- sinonimos `campo/atributo`, `tabla/clase`;
- singular/plural;
- errores ortograficos comunes;
- referencias por nombre;
- una accion;
- varias acciones;
- dependencias entre acciones;
- negaciones;
- ambiguedad;
- solicitudes fuera de alcance.

Ejemplos obligatorios:

```text
generar una clase con atributos id que es UUID y nombre que es string
agrega atributo fecha Date a la clase Estudiante
conecta Perfil de 1 a 1 con Usuario
entre Estudiante y Curso crea association class Inscripcion
crea Perfil, conectala con Usuario y agrega activo a Usuario
elimina la relacion pero conserva las clases
explica el diagrama sin modificarlo
```

Cada caso define intents, acciones, entidades y diagnosticos esperados.

---

## 26. Evaluacion semantica de IA

No comparar texto libre exacto. Medir:

- precision de intent;
- recall de acciones solicitadas;
- exactitud de nombres/tipos;
- exactitud de multiplicidades;
- referencias resueltas;
- acciones extra no solicitadas;
- validez del esquema;
- necesidad de confirmacion;
- conservacion de elementos existentes.

Definir umbrales por categoria y registrar modelo/tag/configuracion.

Una respuesta elegante con accion incorrecta debe fallar.

---

## 27. Pruebas de solicitudes compuestas

Verificar:

1. Orden de acciones.
2. Creacion antes de relacionar.
3. Referencias a recursos creados en la misma solicitud.
4. Transaccion/rollback si una accion falla.
5. Vista previa completa.
6. Confirmacion unica o por riesgo.
7. Idempotencia al reintentar.
8. Evento colaborativo agrupado.
9. Explicacion que coincide con acciones.
10. No generar un diagrama nuevo al pedir editar el actual.

---

## 28. Pruebas de memoria colaborativa IA

- Una conversacion por proyecto.
- Usuarios A y B ven la misma secuencia.
- Mensajes de proyectos no se mezclan.
- Resumen respeta `summary_until_sequence`.
- Referencias sobreviven a paginacion.
- Restauracion no borra conversacion.
- Mensaje duplicado no se inserta.
- Respuesta fallida conserva solicitud.
- Reconectar obtiene backlog.
- Contexto usa modelo UML actual.

---

## 29. Pruebas de imagen UML

Construir corpus legalmente utilizable con:

- captura digital limpia;
- foto frontal;
- perspectiva;
- rotacion;
- poca luz;
- alto brillo;
- ruido;
- fondo cuadriculado;
- escritura manual;
- tipografias variadas;
- dos, tres y muchas clases;
- relaciones cruzadas;
- multiplicidades;
- association class;
- imagen no UML;
- imagen corrupta;
- archivo sobredimensionado.

Etiquetar ground truth separado de nombres precargados. El detector no puede reconocer solo una imagen conocida.

Metricas:

- cajas detectadas;
- IoU orientativo;
- precision de nombres;
- precision de atributos/metodos;
- tipos normalizados;
- relaciones y extremos;
- association class;
- tiempo/memoria.

---

## 30. Pruebas de voz

- Transcripcion limpia.
- Muletillas.
- Pausas.
- Sinonimos.
- Puntuacion ausente.
- Nombres tecnicos.
- UUID/String/Date pronunciados.
- Permisos de microfono denegados en frontend.
- Cancelacion.

El motor recibe transcripcion verificable; la calidad speech-to-text externa se separa de interpretacion UML.

---

## 31. Especificaciones funcionales de metodos

Casos:

- metodo antiguo sin especificacion;
- CRUD;
- calculo puro;
- business action;
- API sin UI;
- user action con formulario;
- selector de entidad;
- validaciones y permisos;
- confirmacion;
- side effects;
- campos referenciando parametro inexistente;
- entidad de otro diagrama.

Round-trip ORM -> Pydantic -> JSON -> generadores sin perdida semantica.

---

## 32. Transformacion al modelo intermedio

Usar golden JSON pequenos y revisables.

Verificar:

- tipos UML a Java/Dart;
- nullable/required;
- ids;
- nombres reservados;
- multiplicidades;
- owner side;
- join entity;
- association class explicita;
- metodos y endpoints;
- contratos de UI;
- orden determinista;
- diagnosticos.

La misma entrada debe producir el mismo modelo canonico.

---

## 33. Matriz de multiplicidades

Probar al menos:

| Origen | Destino | Persistencia esperada | Flutter esperado |
| --- | --- | --- | --- |
| `1` | `1` | FK en lado propietario determinista | selector unico |
| `1` | `*` | FK en lado muchos | selector del lado uno |
| `0..1` | `*` | FK nullable/coleccion | selector opcional |
| `*` | `*` | join entity/table | selectores de ambos lados |
| `*` | `*` + association class | entidad asociativa con dos FKs | formulario con dos selectores |

Verificar create/update/read/delete y serializacion, no solo strings generados.

---

## 34. Backend Spring Boot generado

Para cada fixture representativo:

1. Generar ZIP por API/servicio.
2. Extraer en directorio nuevo.
3. Verificar que no hay path traversal.
4. Ejecutar wrapper o Maven documentado.
5. `test`.
6. `package`.
7. Iniciar PostgreSQL generado.
8. Ejecutar migracion/bootstrap.
9. Iniciar Spring Boot.
10. Esperar health/readiness.
11. Ejecutar CRUD.
12. Ejecutar metodo de negocio.
13. Verificar relaciones.
14. Detener limpiamente.

No modificar `pom.xml`, Java ni variables salvo copiar/configurar `.env` segun README generado.

---

## 35. Casos Spring Boot obligatorios

- Entidad simple.
- Date/DateTime.
- Boolean/Double/Integer/UUID.
- Required/optional.
- 1:1.
- 1:N.
- N:M sintetica.
- Association class explicita.
- Nombre con espacios/acentos normalizado.
- Metodo `calculate`.
- Metodo `business_action`.
- Validacion y error code.
- Autorizacion declarada si esta soportada.

Compilar evita aceptar plantillas sintacticamente invalidas.

---

## 36. Smoke API del backend generado

Usar cliente automatizado:

```text
POST entidad principal
GET lista
GET por id
PUT/PATCH
DELETE
POST entidad relacionada usando id real
POST association class usando ambos ids
```

Verificar:

- status codes;
- JSON;
- UUID;
- errores por id inexistente;
- constraint required;
- fechas;
- no N+1 grave en caso representativo;
- OpenAPI inicia.

---

## 37. Flutter generado

Para cada fixture:

1. Generar ZIP sin Flutter preexistente dentro.
2. Extraer limpio.
3. `flutter pub get`.
4. `dart format --set-exit-if-changed lib test`.
5. `flutter analyze`.
6. `flutter test`.
7. `flutter build web`.
8. Verificar assets/manifiesto.

Cuando se pruebe Android y exista SDK:

- build debug APK como job separado.

No editar codigo generado antes de estos comandos.

---

## 38. Formularios Flutter generados

Widget tests para:

- String -> text input.
- Integer/Double -> teclado/parseo numerico.
- Boolean -> switch/checkbox.
- Date -> date picker y formato API.
- DateTime -> date/time.
- Enum -> dropdown.
- FK -> selector cargado desde servicio.
- required -> validacion.
- optional -> valor nulo.
- texto largo -> overflow controlado.
- loading/error/empty de selectores.

Association class debe mostrar Estudiante y Curso mediante labels compactos y enviar sus ids.

---

## 39. Integracion Spring Boot-Flutter generados

Levantar backend generado y ejecutar Flutter tests/integration contra el API real.

Verificar:

- rutas iguales;
- metodos HTTP;
- nombres JSON;
- nullability;
- fechas;
- respuestas de error;
- paginacion si existe;
- create/update/delete;
- selectores de relaciones;
- metodo de negocio;
- refresh targets.

El contrato compartido es la fuente de verdad. No agregar adaptadores manuales post-generacion.

---

## 40. Editor de estilos y fidelidad

Crear una matriz token -> preview React -> Flutter:

- colores;
- tipografia;
- densidad;
- border radius;
- botones;
- campos;
- cards;
- navegacion;
- claro/oscuro.

Pruebas:

- normalizacion igual;
- configuracion persistida;
- snapshot incluye tema;
- generador usa tema;
- preview cambia propiedad correcta;
- valores invalidos caen a default con diagnostico.

---

## 41. Comparacion visual preview-Flutter

Para pantallas representativas:

- lista;
- detalle;
- formulario;
- selector de entidad;
- accion de negocio;
- loading/error/empty.

Capturar React y Flutter con viewport equivalente. Comparar:

- jerarquia;
- componentes presentes;
- colores/tokens;
- labels;
- spacing aproximado;
- overflow;
- contraste.

No exigir pixel-perfect entre motores distintos, pero fallar divergencias funcionales o tematicas claras. Definir umbral y revision humana para cambios intencionales.

---

## 42. Pruebas de versiones

- Snapshot V2 completo.
- Adaptacion V1.
- Version futura rechazada.
- Hash determinista.
- Creacion concurrente.
- Idempotency key.
- Solo owner/organizador.
- Lista sin snapshot pesado.
- Version inmutable.
- Respaldo pre-restore.
- Restore completo.
- Rollback ante fallo.
- Revision monotona.
- Cliente WebSocket invalidado.
- Conversacion intacta.
- Bitacora intacta.
- Artefactos intactos.

---

## 43. Pruebas de actividad y auditoria

- Secuencia monotona.
- Cursor estable.
- Actor correcto.
- Agrupacion sin perdida.
- Evento IA referenciado.
- Evento de tema.
- Evento de generacion.
- Evento de restauracion.
- Acceso de miembro vs admin.
- Metadata saneada.
- Token/secret nunca persistido.

---

## 44. Pruebas de notificaciones

- Politica de destinatarios.
- Exclusiones de actor.
- Dedup key.
- Preferencias.
- In-app aunque Push falle.
- Outbox atomico.
- Reintentos/backoff.
- 404/410 elimina suscripcion.
- `SKIP LOCKED` con dos workers.
- Deep link interno.
- Marcar leida/clicked idempotente.
- Conteo sincronizado.
- No Push por `MOVE_ELEMENT`.

---

## 45. WebSocket colaborativo

Probar con clientes simultaneos reales o TestClient adecuado:

- autenticacion valida/invalida;
- membresia;
- aislamiento por proyecto;
- broadcast excluye emisor cuando corresponde;
- secuencia;
- ACK;
- duplicado;
- evento fuera de orden;
- base version antigua;
- reconexion con backlog;
- `resync_required`;
- limite de conexiones;
- payload grande;
- cliente lento;
- restauracion;
- remocion de miembro.

No probar solo `ConnectionManager` aislado; incluir router y persistencia.

---

## 46. Concurrencia

Ejecutar contra PostgreSQL con barreras/hilos/procesos controlados:

- dos mensajes IA;
- dos eventos colaborativos;
- dos versiones;
- restore + edit;
- restore + theme;
- confirmar misma accion dos veces;
- dos workers outbox;
- dos actualizaciones con misma revision;
- get-or-create conversation;
- get-or-create settings.

Resultado permitido: serializacion, un ganador con conflicto 409, o idempotencia. Nunca duplicados/corrupcion/500 opaco.

---

## 47. Resiliencia y fault injection

Simular:

- PostgreSQL temporalmente caido.
- Ollama caido/lento.
- filesystem lleno o sin permiso.
- ZIP interrumpido.
- Flutter/Maven no encontrado.
- Web Push timeout.
- WebSocket cortado.
- respuesta HTTP truncada.
- proceso reiniciado con outbox pendiente.
- service worker antiguo.

Verificar rollback, diagnostico, recuperacion y ausencia de datos parciales.

---

## 48. PWA y offline

Con build de produccion:

- manifiesto valido;
- iconos presentes;
- worker registrado una vez;
- ruta profunda offline;
- shell precacheado;
- API privada no cacheada por Workbox;
- IndexedDB por usuario;
- cache stale indicada;
- logout purga;
- update prompt;
- sin loop de recarga;
- borrador IA no autoenviado;
- diagrama readonly offline;
- reconexion revalida.

---

## 49. Responsive y tactil

Playwright viewports:

```text
320x568
360x800
390x844
412x915
768x1024
1024x768
1440x900
```

Comprobar:

- sin overflow global;
- texto largo;
- zoom de texto;
- barras no tapan contenido;
- sheets exclusivas;
- targets 44x44;
- pan/pinch/fit UML;
- readonly no muta;
- teclado no tapa chat;
- landscape.

---

## 50. E2E principal de la segunda parte

Automatizar, en lo posible:

1. Registrar/login.
2. Crear proyecto.
3. Invitar editor.
4. Crear diagrama.
5. Pedir a IA crear/modificar multiples elementos.
6. Confirmar acciones.
7. Definir metodo de negocio.
8. Configurar tema.
9. Previsualizar.
10. Transformar modelo.
11. Generar Spring Boot y Flutter.
12. Descargar artefactos.
13. Guardar version.
14. Hacer cambios.
15. Restaurar.
16. Comprobar conversacion y actividad.
17. Recibir notificacion en colaborador.
18. Abrir PWA movil y consultar diagrama.

Dividir en escenarios mantenibles si un unico test fuera demasiado fragil, conservando un smoke completo.

---

## 51. E2E multiusuario

Usar dos contextos de navegador:

- Organizador A.
- Editor B.

Escenario:

1. Ambos abren proyecto.
2. A modifica UML.
3. B recibe evento.
4. B conversa con IA.
5. A ve mensaje.
6. A guarda version.
7. B ve actividad/notificacion.
8. A restaura.
9. B resincroniza.
10. Ninguno pierde conversacion.

---

## 52. Seguridad de aplicacion

Pruebas negativas:

- IDOR entre proyectos.
- Escalacion editor->organizador.
- Acceso admin oculto.
- Mass assignment.
- Campos actor/user enviados por cliente.
- XSS en nombres, chat, recomendaciones.
- SQL injection en filtros.
- Path traversal en ZIP/nombres.
- Zip Slip al extraer entradas.
- XXE en XMI.
- SSRF mediante URLs configurables.
- Open redirect en deep links.
- WebSocket token invalido.
- CORS host no permitido.
- payload excesivo.

Corregir cada hallazgo alto antes del cierre.

---

## 53. Secretos y repositorio

Escanear:

- archivos trackeados;
- historial reciente cuando corresponda;
- `.env*`;
- logs;
- fixtures;
- capturas/documentos;
- Docker Compose;
- workflows;
- codigo generado.

Patrones:

- AWS access/secret keys;
- JWT secrets;
- DB passwords reales;
- VAPID private key;
- tokens;
- endpoints Push.

Los ejemplos deben ser obviamente ficticios. Si una clave real fue expuesta, ignorarla ahora no basta: rotarla y limpiar segun politica.

---

## 54. Dependencias

### Python

- Instalar desde `pyproject.toml`.
- Ejecutar auditoria.
- Revisar versiones incompatibles.
- No actualizar major automaticamente.

### npm

- `npm ci`.
- `npm audit` como reporte.
- Revisar dependencias runtime vs dev.
- Verificar lockfile.

### Generados

- Maven dependency tree/audit disponible.
- Flutter `pub outdated` informativo, no gate automatico por novedad.

Clasificar vulnerabilidades por explotabilidad real y documentar excepciones temporales.

---

## 55. Headers, CORS y transporte

Verificar en HTTP real:

- security headers;
- allowed hosts;
- CORS preflight de origen permitido;
- origen Vercel configurado;
- origen no permitido rechazado;
- credenciales segun contrato;
- HTTPS/WSS documentado;
- no mixed content en produccion;
- health vs readiness.

No confundir un 400 del endpoint con un fallo CORS.

---

## 56. Rendimiento backend

Medir casos representativos:

- lista de proyectos;
- cargar diagrama 20/50/100 clases;
- actividad paginada;
- conversacion paginada;
- snapshot;
- generacion;
- imagen;
- outbox.

Registrar p50/p95, memoria y queries cuando sea viable.

No fijar objetivos irreales sin baseline. Definir umbrales que detecten regresiones significativas.

---

## 57. Rendimiento frontend

- bundle inicial;
- lazy chunks;
- tiempo a contenido util;
- render de diagrama grande;
- memoria al navegar repetidamente;
- eventos WebSocket en rafaga;
- lista larga de chat/actividad;
- layout shift;
- Lighthouse.

JointJS no debe estar en el chunk inicial de login si Fase 8 implemento lazy loading.

---

## 58. Carga y estabilidad

Escenarios moderados, acordes al proyecto:

- 20 clientes WebSocket en un proyecto.
- 10 proyectos con actividad simultanea.
- rafaga de eventos idempotentes.
- 1000 mensajes paginados.
- 100 versiones listadas sin snapshot.
- outbox con 1000 filas.
- varias generaciones encoladas/seriadas segun capacidad.

No realizar stress destructivo sobre produccion.

---

## 59. Accesibilidad

Automatica + manual:

- login;
- proyectos;
- editor UML y alternativa textual;
- asistente;
- preview;
- historial/versiones;
- notificaciones;
- PWA movil.

Verificar:

- teclado;
- focus;
- dialogos;
- labels;
- headings;
- contraste;
- estado no solo por color;
- `aria-live` no ruidoso;
- zoom 200%;
- reduced motion.

Los errores de axe se revisan; una puntuacion no sustituye prueba manual.

---

## 60. Compatibilidad de navegadores

Automatizar Chromium y, si es viable, Firefox/WebKit para flujos web principales.

Probar manualmente capacidades particulares:

- Web Push.
- PWA install.
- service worker.
- microfono.
- IndexedDB.
- touch.

Documentar matriz navegador/version/capacidad. Degradar, no romper, cuando una API no exista.

---

## 61. Visual regression

Capturas baselines de pantallas estables:

- desktop claro/oscuro;
- movil claro/oscuro;
- UML;
- preview;
- dialogo restaurar;
- notificaciones.

Reglas:

- fonts y datos deterministas;
- animaciones deshabilitadas;
- viewport fijo;
- tolerancia pequena documentada;
- revisar diffs, no actualizar baselines automaticamente.

---

## 62. Docker y Compose

Verificar:

- build sin cache oculto;
- usuario no root cuando corresponda;
- contexto no incluye secretos/artefactos enormes;
- healthchecks;
- readiness DB;
- migracion al iniciar;
- volumen de artefactos;
- variables obligatorias;
- cierre/reinicio;
- logs utiles;
- `docker compose config` valido.

Probar `docker-compose.prod.yml` con `.env` de test, no credenciales reales.

---

## 63. Smoke de despliegue

Ampliar el smoke actual:

- `/health`.
- `/ready`.
- OpenAPI.
- frontend `/` y ruta profunda.
- login con fixture controlado si ambiente lo permite.
- proyectos.
- endpoint IA health/profile.
- WebSocket handshake.
- PWA manifest/service worker.
- generacion minima opcional.

El smoke debe fallar con exit code no cero y mensaje preciso.

---

## 64. CI por etapas

Pipeline sugerido:

### Job 1: lint-contracts

- Ruff AI/backend.
- ESLint.
- TypeScript/build.
- diff/check de OpenAPI/tipos si aplica.

### Job 2: unit

- Pytest unit AI/backend.
- Vitest.

### Job 3: postgres-integration

- Servicio PostgreSQL 16.
- Alembic.
- API/integracion/concurrencia.

### Job 4: e2e

- Stack de prueba.
- Playwright Chromium.
- artefactos de fallo.

### Job 5: generated-spring

- Generar fixtures.
- Maven test/package.
- smoke API.

### Job 6: generated-flutter

- Flutter SDK fijado.
- format/analyze/test/build.

### Job 7: docker-smoke

- Build imagenes.
- Compose.
- smoke.

### Job 8: security-report

- secretos.
- dependencias.
- imagenes si se habilita.

No ejecutar todos los jobs lentos en una sola maquina secuencial si pueden paralelizarse.

---

## 65. Gates de merge

Obligatorios:

- lint cero errores;
- unitarias cero fallos;
- integracion cero fallos;
- migracion desde base anterior;
- frontend build;
- Spring generado compila;
- Flutter generado analiza/test/build;
- E2E criticos;
- sin secreto nuevo;
- sin vulnerabilidad critica explotable sin excepcion aprobada.

Un test flaky sigue siendo fallo hasta encontrar causa o aislarlo con ticket, propietario y fecha.

---

## 66. Cobertura

Medir por modulo, no perseguir un numero vacio.

Objetivos orientativos:

- servicios/validadores criticos >= 85% de lineas;
- generadores y transformaciones >= 85%;
- frontend logica critica >= 80%;
- routers simples pueden cubrirse por funcionales.

Ademas exigir branch coverage en:

- permisos;
- estados IA;
- multiplicidades;
- restauracion;
- offline/deep links.

No excluir archivos dificiles solo para subir porcentaje.

---

## 67. Mutacion y calidad de asserts

Aplicar mutation testing selectivo si el tiempo/herramientas lo permiten sobre:

- multiplicidades;
- permisos;
- transiciones;
- normalizacion;
- snapshot.

Como minimo realizar revision manual de asserts:

- no solo `status_code == 200`;
- verificar efectos DB;
- verificar ausencia de efectos;
- verificar eventos/notificaciones;
- verificar contenido generado.

---

## 68. Gestion de defectos

Clasificacion:

- Critico: perdida/corrupcion de datos, secreto, acceso no autorizado, generados inutilizables.
- Alto: flujo principal roto, restore incorrecto, colaboracion inconsistente.
- Medio: comportamiento alterno roto con workaround.
- Bajo: detalle visual/textual sin impacto funcional.

Cada defecto registra:

- id;
- escenario;
- esperado/obtenido;
- severidad;
- causa raiz;
- commit/cambio;
- prueba de regresion;
- estado.

No cerrar como `no reproducible` sin ambiente y evidencia.

---

## 69. Flakiness

- Ejecutar suites sensibles repetidas localmente/CI temporal.
- Identificar dependencia de reloj, orden, puerto, red o animacion.
- Usar waits por condicion, no sleeps arbitrarios.
- Limpiar recursos.
- Guardar traces/video/screenshots solo al fallar.
- No agregar retries globales como primera solucion.

Un retry acotado de transporte pertenece al producto; un retry de test que oculta carrera no.

---

## 70. Comandos Windows PowerShell

### PostgreSQL

```powershell
docker compose up -d postgres
docker compose ps
```

### AI Engine

```powershell
cd ai-engine
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
```

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check app tests migrations
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

### Frontend

```powershell
cd frontend
npm ci --no-audit --no-fund
npm run lint
npm run test -- --run
npm run build
npx playwright test
```

### Docker productivo local

```powershell
docker compose --env-file .env.test -f docker-compose.prod.yml config
docker compose --env-file .env.test -f docker-compose.prod.yml build
docker compose --env-file .env.test -f docker-compose.prod.yml up -d
```

Usar rutas reales del entorno; no copiar resultados antiguos.

---

## 71. Comandos Linux/CI

```bash
cd ai-engine
python -m ruff check .
python -m pytest -q

cd ../backend
python -m ruff check app tests migrations
python -m pytest -q
python -m alembic upgrade head

cd ../frontend
npm ci --no-audit --no-fund
npm run lint
npm run test -- --run
npm run build
npx playwright test
```

Los scripts multiplataforma deben documentar diferencias, no asumir PowerShell dentro de Linux.

---

## 72. Evidencias y artefactos CI

Guardar solo cuando aporte:

- JUnit XML.
- coverage XML/HTML.
- OpenAPI.
- Alembic current/heads.
- Playwright report, traces y screenshots de fallos.
- logs de compilacion Spring/Flutter.
- manifiestos generados.
- reporte de seguridad saneado.
- Lighthouse.
- matriz de trazabilidad.

No subir ZIP enormes, secretos, bases completas ni contenido privado de conversaciones.

---

## 73. Documentacion de la fase

Crear:

```text
docs/segundo_parcial/fase9/
  00_indice_fase9.md
  01_estrategia_pruebas.md
  02_matriz_trazabilidad.md
  03_pruebas_backend_ai.md
  04_pruebas_generadores.md
  05_pruebas_frontend_pwa.md
  06_seguridad_rendimiento.md
  07_resultados_defectos.md
  08_resumen_fase9.md
  09_acta_cierre_fase9.md
```

Documentar resultados reales con fecha, entorno, versiones y comandos.

---

## 74. Orden de trabajo

1. Inventariar requisitos y pruebas existentes.
2. Construir matriz CU/fases/riesgo.
3. Preparar ambientes y fixtures.
4. Corregir migraciones/contratos bloqueantes.
5. Completar unitarias.
6. Completar integracion PostgreSQL.
7. Completar API/permisos.
8. Endurecer IA y corpus.
9. Compilar generados.
10. Integrar Spring-Flutter.
11. Validar preview.
12. Probar versiones/notificaciones.
13. Configurar Playwright/PWA.
14. Ejecutar seguridad.
15. Ejecutar performance basica.
16. Ejecutar Docker smoke.
17. Corregir defectos y agregar regresiones.
18. Configurar gates CI.
19. Ejecutar suite limpia final.
20. Elaborar acta con evidencia.

---

## 75. Prohibiciones

- No usar la base del usuario para tests destructivos.
- No afirmar que SQLite prueba PostgreSQL.
- No mockear todo el flujo E2E.
- No comparar prosa LLM exacta.
- No aceptar acciones extra de IA.
- No editar proyectos generados antes de compilar.
- No saltar Flutter indefinidamente.
- No actualizar snapshots/goldens sin revisar.
- No desactivar pruebas fallidas.
- No aumentar sleeps para tapar carreras.
- No usar credenciales reales.
- No ejecutar stress en produccion.
- No confundir health con readiness.
- No considerar build frontend como prueba PWA completa.
- No declarar 100% por porcentaje de cobertura solamente.

---

## 76. Criterios de aceptacion

1. CU-01 a CU-18 tienen evidencia.
2. Flujos de fases 1 a 8 tienen trazabilidad.
3. Ruff/Pytest pasan en AI y backend.
4. ESLint/Vitest/build pasan en frontend.
5. Playwright critico pasa.
6. PostgreSQL real pasa migracion/concurrencia.
7. Ollama matrix tiene resultados controlados.
8. Corpus de lenguaje compuesto alcanza umbrales.
9. Corpus de imagen no depende de una sola foto.
10. Spring generado compila y ejecuta smoke.
11. Flutter generado analiza, prueba y compila.
12. Association class funciona extremo a extremo.
13. Preview/ZIP coinciden contractualmente.
14. Restore conserva trazabilidad.
15. Outbox no duplica.
16. PWA offline/read-only funciona.
17. Permisos/IDOR negativos pasan.
18. No hay secreto nuevo.
19. Docker productivo inicia.
20. CI impide merge con gate rojo.
21. Defectos criticos/altos estan cerrados.
22. Evidencia y limitaciones estan documentadas.

---

## 77. Checklist final

- [ ] Matriz de trazabilidad completa.
- [ ] 18 casos de uso cubiertos.
- [ ] Fixtures canonicos.
- [ ] Base de prueba aislada.
- [ ] Alembic empty/upgrade/downgrade/upgrade.
- [ ] OpenAPI validado.
- [ ] Backend lint/tests.
- [ ] AI Engine lint/tests.
- [ ] Frontend lint/tests/build.
- [ ] Playwright.
- [ ] WebSocket multiusuario.
- [ ] IA provider matrix.
- [ ] Lenguaje natural multiple.
- [ ] Imagenes variadas.
- [ ] Spring compile/smoke.
- [ ] Flutter format/analyze/test/build.
- [ ] Contrato cruzado.
- [ ] Preview fidelidad.
- [ ] Versiones/restore.
- [ ] Notificaciones/outbox/push.
- [ ] PWA/offline/mobile.
- [ ] Seguridad/secretos.
- [ ] Docker smoke.
- [ ] CI gates.
- [ ] Defectos corregidos.
- [ ] Acta de cierre real.

---

## 78. Informe final requerido

Reportar:

1. Commit/revision probada.
2. Sistema operativo y versiones de herramientas.
3. Servicios usados.
4. Comandos exactos.
5. Conteo passed/failed/skipped por suite.
6. Migraciones probadas.
7. Fixtures generados compilados.
8. Navegadores/dispositivos.
9. Cobertura.
10. Hallazgos de seguridad.
11. Metricas basicas.
12. Defectos encontrados/corregidos.
13. Limitaciones.
14. Gate final `APROBADO` o `NO APROBADO`.

No convertir skipped en passed ni omitir fallos del informe.

---

## 79. Definicion final de terminado

La Fase 9 y la segunda parte estan terminadas cuando un checkout limpio puede instalar dependencias, migrar PostgreSQL, ejecutar las suites, construir frontend y contenedores, generar proyectos Spring Boot/Flutter sin edicion manual, compilarlos, ejecutar sus flujos representativos y demostrar colaboracion, IA, estilos, versiones, notificaciones y PWA sin corrupcion ni vulneraciones conocidas bloqueantes.

El recorrido final demostrable es:

```text
checkout limpio
  -> instalar dependencias
  -> levantar PostgreSQL
  -> migrar base anterior
  -> ejecutar AI/backend/frontend tests
  -> crear proyecto y colaborar
  -> interpretar texto/voz/imagen
  -> editar el diagrama existente
  -> especificar metodos
  -> previsualizar estilo
  -> generar Spring Boot + Flutter
  -> compilar ambos sin cambios manuales
  -> ejecutar integracion por IDs y multiplicidades
  -> guardar/restaurar version
  -> conservar conversacion y bitacora
  -> entregar notificaciones
  -> consultar desde PWA movil
  -> perder/recuperar conectividad
  -> ejecutar seguridad y smoke Docker
  -> obtener todos los gates verdes
```

Si un paso critico no puede ejecutarse, el producto no se declara terminado al 100%; se documenta como bloqueo con evidencia concreta.
