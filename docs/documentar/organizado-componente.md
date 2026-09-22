# Guia de diagrama organizado en capas y componentes

Esta guia sirve para dibujar dos vistas simples del sistema CASE Inteligente: una vista organizada en capas y una vista de componentes. La idea es representar la estructura real del sistema sin entrar al detalle interno de cada clase.

## 1. Diagrama organizado en capas

Nombre sugerido: `layered CASE Inteligente`

Tipo: diagrama de paquetes o componentes organizado por capas.

### Capas del sistema

```text
Capa Presentacion
- Frontend React + Vite
- Modulo gestion_acceso_usuarios
- Modulo gestion_proyectos_colaboracion
- Modulo modelado_uml_inteligente
- Modulo transformacion_generacion_software

Capa Aplicacion / API
- Backend FastAPI
- Router acceso_usuarios
- Router proyectos_colaboracion
- Router modelado_uml
- Router generacion_software

Capa Dominio / Servicios
- Servicios de autenticacion y usuarios
- Servicios de proyectos y colaboracion
- Servicios de modelado UML
- Servicios de importacion/exportacion XML
- Servicios de transformacion UML
- Servicios de generacion Spring Boot
- Servicios de generacion Flutter
- Motor IA local

Capa Persistencia
- Repositorios
- Modelos ORM
- PostgreSQL

Capa Infraestructura
- Vercel
- AWS EC2
- AWS S3
- CloudWatch
- GitHub Actions
```

### Relaciones entre capas

```text
Capa Presentacion -> Capa Aplicacion / API : HTTP REST / WebSocket
Capa Aplicacion / API -> Capa Dominio / Servicios : llamadas internas
Capa Dominio / Servicios -> Capa Persistencia : repositorios / consultas
Capa Dominio / Servicios -> Capa Infraestructura : archivos generados / logs / IA local
Capa Persistencia -> PostgreSQL : SQL
```

### Distribucion visual sugerida

```text
+----------------------------------------------+
| Capa Presentacion                            |
| React + modulos frontend                     |
+----------------------------------------------+
                    |
                    v
+----------------------------------------------+
| Capa Aplicacion / API                        |
| FastAPI + routers                            |
+----------------------------------------------+
                    |
                    v
+----------------------------------------------+
| Capa Dominio / Servicios                     |
| autenticacion, proyectos, UML, IA, generacion|
+----------------------------------------------+
                    |
                    v
+----------------------------------------------+
| Capa Persistencia                            |
| repositorios, modelos, PostgreSQL            |
+----------------------------------------------+
                    |
                    v
+----------------------------------------------+
| Capa Infraestructura                         |
| Vercel, EC2, S3, CloudWatch, GitHub Actions  |
+----------------------------------------------+
```

## 2. Diagrama de componentes del sistema

Nombre sugerido: `component CASE Inteligente`

Tipo: diagrama de componentes UML.

### Componentes principales

```text
<<component>> Frontend Web
  - Gestion de acceso, usuarios y seguimiento
  - Gestion de proyectos y colaboracion
  - Modelado UML inteligente
  - Transformacion y generacion de software

<<component>> API Backend FastAPI
  - Auth API
  - Projects API
  - UML Modeling API
  - Software Generation API

<<component>> Servicio de Acceso y Usuarios
  - Registro
  - Login
  - Roles
  - Sesiones

<<component>> Servicio de Proyectos y Colaboracion
  - Proyectos
  - Integrantes
  - Permisos
  - Versiones

<<component>> Servicio de Modelado UML
  - Diagramas de clases
  - Validacion UML
  - Importacion XML
  - Exportacion XML
  - Modo colaborativo

<<component>> Servicio IA Local
  - Generacion de modelos UML desde texto
  - Generacion desde imagen
  - Asistente guiado

<<component>> Servicio de Transformacion y Generacion
  - Transformacion UML a modelo intermedio
  - Generacion backend Spring Boot
  - Generacion app movil Flutter

<<database>> PostgreSQL
  - Usuarios, roles y sesiones
  - Proyectos y permisos
  - Diagramas UML
  - Transformaciones
  - Artefactos generados
  - Auditoria

<<component>> Almacenamiento de Artefactos
  - ZIP backend generado
  - ZIP app movil generada
  - Archivos XML importados/exportados
```

### Conexiones entre componentes

```text
Frontend Web -> API Backend FastAPI : REST / WebSocket
API Backend FastAPI -> Servicio de Acceso y Usuarios : usa
API Backend FastAPI -> Servicio de Proyectos y Colaboracion : usa
API Backend FastAPI -> Servicio de Modelado UML : usa
API Backend FastAPI -> Servicio IA Local : usa
API Backend FastAPI -> Servicio de Transformacion y Generacion : usa

Servicio de Acceso y Usuarios -> PostgreSQL : lee/escribe usuarios
Servicio de Proyectos y Colaboracion -> PostgreSQL : lee/escribe proyectos
Servicio de Modelado UML -> PostgreSQL : lee/escribe diagramas
Servicio de Transformacion y Generacion -> PostgreSQL : guarda transformaciones
Servicio de Transformacion y Generacion -> Almacenamiento de Artefactos : guarda ZIP
Servicio de Modelado UML -> Almacenamiento de Artefactos : guarda XML
```

### Distribucion visual sugerida

```text
[Frontend Web]
      |
      v
[API Backend FastAPI]
      |
      +--> [Servicio Acceso y Usuarios] --------+
      +--> [Servicio Proyectos y Colaboracion]  |
      +--> [Servicio Modelado UML]              +--> [PostgreSQL]
      +--> [Servicio IA Local]                  |
      +--> [Servicio Transformacion/Generacion]-+
                         |
                         v
              [Almacenamiento de Artefactos]
```

## Checklist para dibujar

```text
1. Crear primero la vista por capas con cinco bloques horizontales.
2. Usar flechas de arriba hacia abajo para indicar dependencia.
3. Crear luego el diagrama de componentes.
4. Poner Frontend Web arriba o a la izquierda.
5. Poner API Backend FastAPI al centro.
6. Poner los servicios de dominio alrededor del backend.
7. Poner PostgreSQL y Almacenamiento de Artefactos a la derecha o abajo.
8. Usar estereotipos <<component>> y <<database>>.
9. No detallar clases internas en este diagrama.
10. Mantener nombres similares a los modulos reales del sistema.
```
