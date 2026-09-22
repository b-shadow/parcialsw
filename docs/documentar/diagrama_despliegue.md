# Guia para diagrama de despliegue

Arquitectura objetivo: frontend en Vercel, backend en AWS EC2, base de datos PostgreSQL en AWS y artefactos generados en almacenamiento AWS. El diagrama debe mostrar nodos, artefactos desplegados y rutas de comunicacion.

## Marco del diagrama

Nombre: `deployment Plataforma CASE Inteligente`

Tipo: diagrama de despliegue UML.

## Nodos principales

```text
<<device>> Cliente Web
  <<executionEnvironment>> Navegador Web
    <<artifact>> App React

<<node>> Vercel
  <<executionEnvironment>> Vercel Hosting
    <<artifact>> Frontend React + Vite

<<cloud>> AWS
  <<node>> VPC CASE Inteligente
    <<device>> EC2 Backend
      <<executionEnvironment>> Ubuntu Server
      <<executionEnvironment>> Python 3.12
      <<artifact>> Backend FastAPI
      <<artifact>> Motor IA local offline
      <<artifact>> Generador Spring Boot
      <<artifact>> Generador Flutter

    <<database>> PostgreSQL
      <<artifact>> Base case_inteligente

    <<node>> S3 Artefactos
      <<artifact>> ZIP Backend generado
      <<artifact>> ZIP App movil Flutter generada

    <<node>> CloudWatch
      <<artifact>> Logs backend

<<node>> GitHub
  <<artifact>> Repositorio Git
  <<artifact>> GitHub Actions

<<device>> Desarrollador
  <<executionEnvironment>> VS Code
  <<executionEnvironment>> Postman
  <<executionEnvironment>> Enterprise Architect
```

## Conexiones

```text
Cliente Web -> Vercel : HTTPS
Vercel -> EC2 Backend : HTTPS / REST API
Vercel -> EC2 Backend : WSS / WebSocket colaborativo
EC2 Backend -> PostgreSQL : TCP 5432
EC2 Backend -> S3 Artefactos : HTTPS / AWS SDK
EC2 Backend -> CloudWatch : Logs
GitHub Actions -> Vercel : deploy frontend
GitHub Actions -> EC2 Backend : SSH / deploy backend
Desarrollador -> GitHub : Git push / pull request
Desarrollador -> EC2 Backend : Postman HTTPS
Desarrollador -> Enterprise Architect : importar/exportar XML
```

## Artefactos por nodo

### Cliente Web

```text
Navegador Web
- Ejecuta la SPA React.
- Consume la API REST del backend.
- Abre WebSocket para el modo colaborativo.
```

### Vercel

```text
Frontend React + Vite
- Build estatico generado con npm run build.
- Variables:
  - VITE_API_BASE_URL=https://api.dominio.com/api/v1
  - VITE_WS_BASE_URL=wss://api.dominio.com
- Sirve las rutas del frontend.
```

### AWS EC2 Backend

```text
Ubuntu Server
- Nginx como proxy HTTPS.
- Backend FastAPI ejecutado con Uvicorn/Gunicorn o systemd.
- Motor IA local offline usado por generacion UML.
- Generador Spring Boot para backend descargable.
- Generador Flutter para app movil descargable.
- Conexion a PostgreSQL.
- Conexion a S3 para guardar artefactos ZIP.
```

### PostgreSQL

```text
PostgreSQL
- users, roles, user_roles, user_sessions.
- projects, project_members, project_permissions, project_versions.
- uml_diagrams, uml_classes, uml_attributes, uml_methods, uml_relationships.
- uml_transformations, generated_backends, generated_frontends, generated_artifacts.
- audit_logs, ai_processes, xmi_exchanges.
```

### S3 Artefactos

```text
Almacenamiento de archivos generados
- ZIP backend Spring Boot.
- ZIP app movil Flutter.
- Manifiestos de generacion.
- Archivos descargados desde la interfaz.
```

### CloudWatch

```text
Observabilidad
- Logs del backend.
- Errores de ejecucion.
- Trazabilidad operativa.
```

## Seguridad a representar

```text
Cliente Web -> Vercel : HTTPS
Vercel -> Backend : HTTPS
Backend -> PostgreSQL : red privada / security group
Backend -> S3 : credenciales IAM
Backend -> CloudWatch : IAM role
```

Notas:

- No exponer PostgreSQL directamente a internet.
- EC2 debe aceptar trafico publico solo por 80/443.
- SSH debe quedar restringido al administrador.
- JWT se maneja entre frontend y backend.
- CORS debe permitir el dominio de Vercel.

## Distribucion visual sugerida

```text
[Cliente Web] ---> [Vercel Frontend] ---> [AWS / EC2 Backend]
                                            |
                                            v
                                      [PostgreSQL]
                                            |
                                            v
                                      [S3 Artefactos]

[Desarrollador] ---> [GitHub / GitHub Actions] ---> [Vercel y EC2]
```

Ubicacion recomendada:

- Izquierda: `Cliente Web`.
- Centro: `Vercel`.
- Derecha: contenedor grande `AWS`.
- Dentro de AWS:
  - Arriba: `EC2 Backend`.
  - Abajo izquierda: `PostgreSQL`.
  - Abajo derecha: `S3 Artefactos`.
  - Lateral: `CloudWatch`.
- Abajo: `GitHub` y `Desarrollador` como nodos externos.

## Estereotipos UML recomendados

```text
Cliente Web: <<device>>
Navegador Web: <<executionEnvironment>>
Vercel: <<node>>
AWS: <<cloud>>
VPC CASE Inteligente: <<node>>
EC2 Backend: <<device>>
Ubuntu Server: <<executionEnvironment>>
Python 3.12: <<executionEnvironment>>
PostgreSQL: <<database>>
S3 Artefactos: <<node>>
CloudWatch: <<node>>
GitHub: <<node>>
Artefactos desplegados: <<artifact>>
```

## Checklist para dibujar en Enterprise Architect

```text
1. Crear diagrama Deployment.
2. Crear nodo Cliente Web con Navegador Web y App React.
3. Crear nodo Vercel con Frontend React + Vite.
4. Crear contenedor AWS.
5. Dentro de AWS crear VPC CASE Inteligente.
6. Dentro de VPC crear EC2 Backend, PostgreSQL, S3 Artefactos y CloudWatch.
7. Agregar artefactos dentro de EC2: Backend FastAPI, Motor IA local, Generador Spring Boot, Generador Flutter.
8. Conectar Cliente Web con Vercel por HTTPS.
9. Conectar Vercel con EC2 por HTTPS/REST y WSS.
10. Conectar EC2 con PostgreSQL por TCP 5432.
11. Conectar EC2 con S3 por HTTPS/AWS SDK.
12. Conectar EC2 con CloudWatch por Logs.
13. Agregar GitHub/GitHub Actions como nodo externo de despliegue.
14. Agregar Desarrollador con VS Code, Postman y Enterprise Architect.
```
