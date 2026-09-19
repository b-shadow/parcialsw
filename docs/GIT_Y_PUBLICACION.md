# Git y publicacion

El repositorio remoto oficial es `https://github.com/b-shadow/parcialsw.git` y la rama
principal es `main`.

## Archivos que si se versionan

- Codigo fuente de `frontend/`, `backend/` y `ai-engine/`.
- Migraciones, configuracion de Docker, infraestructura declarativa y scripts.
- Documentacion del proyecto dentro de `docs/`.
- Plantillas de configuracion como `.env.example` y `.env.production.example`.
- Archivos de bloqueo de dependencias, cuando existan.

## Archivos que no deben publicarse

`.gitignore` excluye los secretos y artefactos locales, incluyendo:

- Archivos `.env` reales, claves, certificados y keystores.
- Entornos virtuales de Python, `node_modules/`, caches y resultados de build.
- Bases de datos locales, logs, almacenamiento generado y archivos comprimidos.
- Estado, planes y directorios de trabajo de Terraform.
- Configuracion personal de editores y del sistema operativo.

Las plantillas `*.example` no contienen secretos y permanecen versionadas para documentar
la configuracion necesaria.

## Comprobaciones antes de publicar

```powershell
git status --short
git diff --cached --check
git ls-files | Select-String -Pattern '(^|/)\.env($|\.)|\.pem$|\.key$|\.p12$|\.pfx$'
```

La ultima comprobacion debe mostrar solo plantillas de ejemplo autorizadas. Si un secreto
ya fue confirmado en Git, eliminarlo del archivo no basta: hay que revocarlo y rotarlo.

## Publicacion normal

```powershell
git add .
git diff --cached --stat
git diff --cached --check
git commit -m "Actualiza la plataforma CASE Inteligente"
git push origin main
```