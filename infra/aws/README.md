# Preparacion de despliegue en AWS

La configuracion prepara React en S3/CloudFront o Vercel, FastAPI y trabajadores NoSQL en una EC2, PostgreSQL en RDS y artefactos/respaldos en S3. MongoDB, Ollama y Redis son servicios externos conectados mediante endpoints privados; Terraform **no los crea**. No se ha ejecutado `terraform apply` ni una prueba integral en AWS.

## Requisitos

1. Elegir region, dominios y zona Route53. Crear ECR y publicar una imagen backend etiquetada con el SHA del commit.
2. Aprovisionar MongoDB compatible con el driver actual, TLS, backups y acceso desde la VPC `10.20.0.0/16`. Guardar la URI completa como texto en Secrets Manager.
3. Para alojar Ollama en AWS, activar `enable_aws_ollama=true` y definir `ollama_base_url=null`. Terraform crea una EC2 GPU separada con AMI de NVIDIA, 100 GiB cifrados y acceso al puerto 11434 solo desde el security group del backend; el backend toma su IP privada. Verificar cuota y disponibilidad de `g6.xlarge` en la region antes de aplicar. La instancia descarga los tres modelos configurados durante el arranque. Tambien se puede dejar `enable_aws_ollama=false` y proporcionar una URL privada de un Ollama ya operado. No exponer Ollama a Internet.
4. Crear un secreto JWT aleatorio en Secrets Manager. Para presencia colaborativa distribuida, provisionar Redis privado y guardar su URL como texto en Secrets Manager. Sin Redis, usar una sola instancia backend.
5. Confirmar CloudFront si se usara. Si el frontend sigue en Vercel, configurar `frontend_external_url`.

## Estado y plan

Terraform requiere version 1.10 o posterior. El estado remoto debe estar en un bucket separado, versionado y cifrado. **Si ya hay estado local, respaldarlo y revisar su contenido antes de migrarlo**; iniciar un backend remoto vacio sin migrar puede recrear recursos.

```powershell
cd infra/aws
.\bootstrap-state.ps1 -Bucket NOMBRE_UNICO_ESTADO -Region us-east-1
cd terraform
terraform init -migrate-state -backend-config="bucket=NOMBRE_UNICO_ESTADO" -backend-config="key=case-inteligente/staging/terraform.tfstate" -backend-config="region=us-east-1"
terraform fmt -check
terraform validate
terraform plan -out=staging.tfplan
```

Para una cuenta nueva sin estado local, usar `terraform init` con los mismos `-backend-config` sin `-migrate-state`. Usar claves de estado independientes para staging y produccion. `terraform.tfvars.example` solo muestra entradas; no contiene secretos funcionales. Revisar el plan antes de aplicar: RDS protegido puede cambiar recursos existentes y la EC2 se reemplaza al cambiar `user_data`.

## Comprobacion de staging

Tras aprobar el plan, ejecutar `terraform apply staging.tfplan` y verificar:

1. RDS privado y cifrado, secreto administrado y al menos siete dias de backups.
2. EC2 sin errores de cloud-init, contenedores backend/outbox/conciliacion activos y logs en CloudWatch.
3. Target ALB sano, `/health` y `/ready` por HTTPS con HTTP 200. `/ready` comprueba PostgreSQL, MongoDB y migracion/conciliacion.
4. Login, proyecto, importacion XMI, generacion por imagen, chat, propuestas aprobadas, WebSocket, generacion Spring Boot/Flutter, descarga y exportacion con datos de prueba.
5. Frontend HTTPS con `VITE_API_BASE_URL=https://api.DOMINIO/api/v1` y `VITE_WS_BASE_URL=wss://api.DOMINIO`; revisar CORS y consola del navegador. Para S3/CloudFront, construir `frontend` con esas variables, sincronizar `frontend/dist` al bucket y crear una invalidacion de CloudFront.
6. Ejecutar una copia y verificar el ZIP en `s3://BUCKET/backups/`, artefactos en `generated/` y restauracion en entorno aislado.
7. Confirmar suscripcion SNS si hay `alarm_email` y comprobar una alarma controlada.

## Operacion y limites

### IA del proyecto: computadora y AWS

La configuracion de IA se guarda en `projects.settings.ai` y se comparte entre todos los colaboradores del proyecto. Solo un integrante con permiso `ai.settings` puede cambiarla. Las conversaciones pueden ser multiples, pero usan la configuracion comun del proyecto. El backend invoca Ollama desde el servidor. Con el backend ejecutado en la computadora, `OLLAMA_BASE_URL=http://127.0.0.1:11434` usa el Ollama local. Con el backend en AWS, `ollama_base_url` apunta a la EC2 GPU privada. El lector de imagenes UML y el asistente comparten esa URL del despliegue. El validador acepta loopback, `host.docker.internal`, direcciones privadas RFC1918 y hosts internos declarados en `OLLAMA_ALLOWED_HOSTS`; rechaza destinos publicos no autorizados, credenciales en la URL, rutas y redirecciones.

El proyecto completo elige `local` o `aws` en `projects.settings.ai.settings_json.origen_ollama`. El backend configura los dos destinos con `OLLAMA_LOCAL_BASE_URL` y `OLLAMA_AWS_BASE_URL`; no acepta URL enviada por el navegador. El asistente y la lectura de imagenes de un proyecto existente usan el mismo origen. El proyecto nuevo usa `OLLAMA_DEFAULT_SOURCE` hasta que exista y pueda guardarse su configuracion. Si falta el destino elegido, el ajuste devuelve 422 en vez de guardar una seleccion que no funcionaria.

Una web publicada en AWS no puede alcanzar directamente `localhost` de una computadora del equipo desde su backend. Para que la opcion `local` funcione con backend en AWS, la maquina del equipo debe ofrecer un servicio compartido mediante un enlace seguro y disponible para el backend. En el despliegue AWS preparado aqui solo se configura Ollama AWS: la opcion local quedara no disponible hasta instalar ese enlace. Si se pierde Internet, la web alojada en AWS tampoco puede comunicarse con su backend; el funcionamiento totalmente offline requiere desplegar tambien el backend y los datos localmente.

- El timer `case-inteligente-backup.timer` crea diariamente un respaldo coordinado PostgreSQL/MongoDB y sincroniza artefactos. Falla si hay eventos Outbox pendientes; vigilar el servicio y el espacio. Restringir acceso al ZIP, que contiene datos sensibles. Probar restauracion periodicamente.
- CloudWatch recoge logs del backend y trabajadores; hay alarmas para target ALB, EC2 y espacio RDS. El proveedor de MongoDB y Ollama requieren monitoreo propio.
- La instancia GPU opcional genera costo mientras esta encendida y no tiene escalado ni alta disponibilidad. El estado de EC2 tiene alarma, pero las peticiones y modelos deben validarse con `/api/tags`, lectura de imagenes y una prueba de carga desde el backend.
- La topologia usa **una EC2 en una zona**. No ofrece alta disponibilidad ni despliegue sin corte. Antes de calidad de producto en produccion hacen falta replicas, workers desacoplados, Redis compartido, rotacion de secretos, simulacros de restauracion y pruebas de carga de vision/generacion.
- CI solo valida y construye. El `terraform apply` y publicacion de imagenes requieren credenciales y revision separada. No poner secretos en Git, `tfvars`, logs ni artefactos de CI.

## Compose local de produccion

`docker-compose.prod.yml` requiere `POSTGRES_PASSWORD`, `MONGO_ROOT_PASSWORD`, `JWT_SECRET_KEY`, `OLLAMA_BASE_URL`, `CORS_ORIGINS` y `ALLOWED_HOSTS`. La URL de Ollama debe ser alcanzable **desde el contenedor backend**, no solo desde el host. Usar credenciales compatibles con URL o codificar los caracteres especiales en las URI PostgreSQL/MongoDB. La interfaz se abre en el puerto 8080 y usa proxy del Nginx local para `/api` y `/ws`; comprobar login y WebSocket antes de usarla con datos reales.
