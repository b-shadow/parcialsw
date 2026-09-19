# Fase 8 - Estructura del backend generado

## Proyecto generado

```text
proyecto/
  pom.xml
  README.md
  src/main/java/{base_package}/
    Application.java
    config/
      SecurityConfig.java
    controller/
    dto/
    entity/
    exception/
      ResourceNotFoundException.java
      GlobalExceptionHandler.java
    repository/
    service/
  src/main/resources/
    application.properties
```

## Dependencias Maven

- Spring Web.
- Spring Data JPA.
- Spring Validation.
- Spring Security.
- PostgreSQL Driver.
- Lombok.
- SpringDoc OpenAPI.
- Spring Boot Test.

## Configuracion

El `application.properties` generado incluye:

- Nombre de aplicacion.
- Puerto 8080.
- URL PostgreSQL parametrizable.
- Usuario y password por variables.
- Hibernate `ddl-auto=update`.
- Swagger UI.

## Seguridad

Se genera `SecurityConfig` con estructura Spring Security lista para endurecer JWT/roles en fases posteriores.
