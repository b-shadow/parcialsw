# IA local desde el backend de AWS

El navegador usa el backend de `api.bshadow.xyz`. Para seleccionar **Local** en un proyecto, el backend debe llegar al Ollama de esta computadora; el navegador no conecta directamente con el puerto 11434.

La EC2 usa un usuario SSH restringido (`case-ia-tunnel`) y AWS Systems Manager para recibir un túnel inverso. El puerto 11435 no está abierto en el security group público (solo 80 y 443). El contenedor backend resuelve `host.docker.internal:host-gateway` y usa `OLLAMA_LOCAL_BASE_URL=http://host.docker.internal:11435`. El puerto de Ollama en la computadora queda limitado a `127.0.0.1:11434`.

Para iniciar o reconectar en esta computadora, con Docker Desktop y la sesión AWS CLI `case-inteligente` disponibles:

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\aws\start-local-ai.ps1
```

El script usa la clave SSH privada de `%LOCALAPPDATA%\case-ia-tunnel\id_ed25519`, inicia el contenedor `case-ollama-local` y reintenta el túnel si se corta. El modelo instalado es `qwen2.5-coder:1.5b`. Si se apaga la computadora, el backend o el túnel, el selector de IA debe mostrar **Local** como no disponible. **AWS** continúa usando el Ollama propio de la EC2.

Para comprobar el motor local:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

El sitio publicado en Vercel requiere Internet para ambos orígenes de IA.

## Usar otra computadora por turnos

No se cambia AWS. La segunda computadora usa el mismo puerto de tunel `11435`, el mismo usuario SSH restringido y el mismo script. Primero se cierra el proceso del tunel en la computadora anterior; apagar solo Ollama no libera el puerto.

En la segunda computadora Windows se necesitan Docker Desktop, AWS CLI v2, el plugin de Session Manager, OpenSSH y acceso autorizado al perfil `case-inteligente`. El script detecta el plugin tanto en su instalacion estandar como en la ruta local usada durante el primer despliegue. Autenticarse en esa computadora con `aws login --profile case-inteligente --region us-east-1`; no copiar archivos de credenciales de AWS. La clave privada SSH existente debe transferirse de forma privada a `%LOCALAPPDATA%\case-ia-tunnel\id_ed25519`. Sin esa clave, habria que autorizar una nueva en AWS.

Crear el contenedor en esa computadora (sin GPU; si Docker admite NVIDIA, agregar `--gpus all`):

```powershell
docker run -d --name case-ollama-local -p 127.0.0.1:11434:11434 -v case_ollama_local:/root/.ollama --restart unless-stopped ollama/ollama:latest
docker exec case-ollama-local ollama pull qwen2.5-coder:1.5b
Invoke-RestMethod http://127.0.0.1:11434/api/tags
powershell -ExecutionPolicy Bypass -File .\infra\aws\start-local-ai.ps1
```

Mantener abierta la ultima sesion de PowerShell. Si aparece `remote port forwarding failed for listen port 11435`, el tunel de la primera computadora sigue conectado. Una vez conectado, la opcion **Local** del proyecto usa Ollama de la segunda computadora; no hay deteccion directa desde el navegador.
