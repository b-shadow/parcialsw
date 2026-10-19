# Seguridad y rendimiento

## Seguridad verificada

- CORS autoriza los dos dominios Vercel configurados y rechaza origen desconocido.
- Headers `nosniff`, `DENY`, referrer policy, permissions policy y request ID tienen regresion.
- `/ready` responde `503` ante fallo de base de datos; `/health` no mezcla readiness.
- Los ZIP se construyen con rutas relativas al directorio generado.
- Git no contiene coincidencias para claves AWS, claves privadas ni la credencial AWS revocada conocida.
- `.env`, almacenamiento generado, claves y certificados permanecen ignorados.
- CI ejecuta Gitleaks sobre el historial disponible.

## Rendimiento

| Medicion | Antes | Despues |
|---|---:|---:|
| Chunk inicial JS | 979.20 kB | 346.62 kB |
| Chunk editor UML lazy | incluido al inicio | 509.43 kB bajo demanda |
| Backend completo | n/a | 97 pruebas aprobadas; 2 toolchains condicionados |
| AI Engine | n/a | 43 pruebas en 6.24 s |
| Flutter generado | n/a | toolchain completo en 84.97 s |

La imagen de login pesa 1.47 MB y queda registrada como mejora no bloqueante de optimizacion de activo. No afecta correccion ni carga de JointJS.

## Operacion

El workflow separa Python, PostgreSQL, frontend, mobile, Spring generado, Flutter generado, secretos y Docker. Los jobs lentos no bloquean entre si innecesariamente y los reportes Playwright se conservan solo ante fallo.

El smoke productivo se ejecuto con imagenes Docker reales y puertos aislados `18000` y `18080` para no interrumpir el backend local existente. PostgreSQL 16, backend y frontend alcanzaron estado `healthy`; `/health`, `/ready`, `/openapi.json` y `/` respondieron correctamente. Posteriormente, el esquema local aplico y verifico el endurecimiento de roles hasta `c9d3e4f5a6b7 (head)`. Finalizada la prueba, los contenedores, red y volumenes temporales del proyecto `casephase9` fueron retirados.

