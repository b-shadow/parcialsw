from app.modules.generacion_software.backend_generator.analyzer.model_analyzer import (
    JavaEntity,
    JavaRelationship,
    SpringBootProject,
    to_camel_case,
)


def package_path(base_package: str) -> str:
    return base_package.replace(".", "/")


def render_pom(project: SpringBootProject) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.3.5</version>
    <relativePath/>
  </parent>
  <groupId>{project.group_id}</groupId>
  <artifactId>{project.artifact_id}</artifactId>
  <version>0.1.0</version>
  <name>{project.name}</name>
  <properties>
    <java.version>17</java.version>
  </properties>
  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-data-jpa</artifactId>
    </dependency>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-validation</artifactId>
    </dependency>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-security</artifactId>
    </dependency>
    <dependency>
      <groupId>org.postgresql</groupId>
      <artifactId>postgresql</artifactId>
      <scope>runtime</scope>
    </dependency>
    <dependency>
      <groupId>org.projectlombok</groupId>
      <artifactId>lombok</artifactId>
      <optional>true</optional>
    </dependency>
    <dependency>
      <groupId>org.springdoc</groupId>
      <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
      <version>2.6.0</version>
    </dependency>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-test</artifactId>
      <scope>test</scope>
    </dependency>
  </dependencies>
  <build>
    <plugins>
      <plugin>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-maven-plugin</artifactId>
      </plugin>
    </plugins>
  </build>
</project>
"""


def render_application(project: SpringBootProject) -> str:
    return f"""package {project.base_package};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class {project.name}Application {{
    public static void main(String[] args) {{
        SpringApplication.run({project.name}Application.class, args);
    }}
}}
"""


def render_application_properties(project: SpringBootProject) -> str:
    database_name = project.artifact_id.replace("-", "_")
    return f"""spring.application.name={project.artifact_id}
server.port=8080

spring.datasource.url=${{SPRING_DATASOURCE_URL:jdbc:postgresql://127.0.0.1:${{POSTGRES_PORT:55432}}/{database_name}}}
spring.datasource.username=${{SPRING_DATASOURCE_USERNAME:postgres}}
spring.datasource.password=${{SPRING_DATASOURCE_PASSWORD:postgres}}

spring.jpa.hibernate.ddl-auto=update
spring.jpa.open-in-view=false
spring.jpa.properties.hibernate.format_sql=true

springdoc.swagger-ui.path=/swagger-ui.html
"""


def render_env_example(project: SpringBootProject) -> str:
    database_name = project.artifact_id.replace("-", "_")
    return f"""POSTGRES_DB={database_name}
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=55432
SPRING_DATASOURCE_URL=jdbc:postgresql://127.0.0.1:55432/{database_name}
SPRING_DATASOURCE_USERNAME=postgres
SPRING_DATASOURCE_PASSWORD=postgres
"""


def render_docker_compose(project: SpringBootProject) -> str:
    database_name = project.artifact_id.replace("-", "_")
    return f"""services:
  postgres:
    image: postgres:16
    container_name: {project.artifact_id}-postgres
    environment:
      POSTGRES_DB: ${{POSTGRES_DB:-{database_name}}}
      POSTGRES_USER: ${{POSTGRES_USER:-postgres}}
      POSTGRES_PASSWORD: ${{POSTGRES_PASSWORD:-postgres}}
    ports:
      - "${{POSTGRES_PORT:-55432}}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/001-init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${{POSTGRES_USER:-postgres}} -d $${{POSTGRES_DB:-{database_name}}}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
"""


def render_database_init(project: SpringBootProject) -> str:
    database_name = project.artifact_id.replace("-", "_")
    return f"""-- Inicializacion PostgreSQL para {project.name}.
-- El contenedor oficial crea POSTGRES_DB automaticamente; este bloque ayuda si se ejecuta manualmente en pgAdmin.
SELECT 'CREATE DATABASE {database_name}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '{database_name}')\\gexec
"""


def render_run_script_sh(project: SpringBootProject) -> str:
    return """#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

if command -v docker >/dev/null 2>&1; then
  docker compose up -d postgres
fi

if [ -x "./mvnw" ]; then
  ./mvnw spring-boot:run
  exit 0
fi

if command -v mvn >/dev/null 2>&1; then
  mvn spring-boot:run
  exit 0
fi

MAVEN_VERSION="3.9.11"
TOOLS_DIR=".tools"
MAVEN_DIR="$TOOLS_DIR/apache-maven-$MAVEN_VERSION"
ARCHIVE="$TOOLS_DIR/apache-maven-$MAVEN_VERSION-bin.tar.gz"
URL="https://archive.apache.org/dist/maven/maven-3/$MAVEN_VERSION/binaries/apache-maven-$MAVEN_VERSION-bin.tar.gz"

mkdir -p "$TOOLS_DIR"
if [ ! -x "$MAVEN_DIR/bin/mvn" ]; then
  if [ ! -f "$ARCHIVE" ]; then
    if command -v curl >/dev/null 2>&1; then
      curl -L "$URL" -o "$ARCHIVE"
    elif command -v wget >/dev/null 2>&1; then
      wget "$URL" -O "$ARCHIVE"
    else
      echo "curl o wget es necesario para descargar Maven." >&2
      exit 1
    fi
  fi
  tar -xzf "$ARCHIVE" -C "$TOOLS_DIR"
fi

"$MAVEN_DIR/bin/mvn" spring-boot:run
"""


def render_run_script_ps1(project: SpringBootProject) -> str:
    return """$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $projectRoot

if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker compose up -d postgres
}

if (Test-Path ".\\mvnw.cmd") {
    .\\mvnw.cmd spring-boot:run
    exit $LASTEXITCODE
}

if (Get-Command mvn -ErrorAction SilentlyContinue) {
    mvn spring-boot:run
    exit $LASTEXITCODE
}

$mavenVersion = "3.9.11"
$toolsDir = Join-Path $PSScriptRoot "..\\.tools"
$mavenDir = Join-Path $toolsDir "apache-maven-$mavenVersion"
$archive = Join-Path $toolsDir "apache-maven-$mavenVersion-bin.zip"
$url = "https://archive.apache.org/dist/maven/maven-3/$mavenVersion/binaries/apache-maven-$mavenVersion-bin.zip"

New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null

if (-not (Test-Path (Join-Path $mavenDir "bin\\mvn.cmd"))) {
    if (-not (Test-Path $archive)) {
        Invoke-WebRequest -Uri $url -OutFile $archive
    }
    Expand-Archive -Path $archive -DestinationPath $toolsDir -Force
}

& (Join-Path $mavenDir "bin\\mvn.cmd") spring-boot:run
exit $LASTEXITCODE
"""


def render_entity(project: SpringBootProject, entity: JavaEntity) -> str:
    fields = "\n".join(_render_field(field.name, field.java_type, field.required, field.email) for field in entity.fields)
    relation_fields = "\n".join(_render_relation_field(project, entity) for entity in [entity])
    imports = _entity_imports(project, entity)
    return f"""package {project.base_package}.entity;

{imports}
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Entity
@Table(name = "{to_camel_case(entity.name)}s")
public class {entity.name} {{
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

{fields}
{relation_fields}
}}
"""


def render_dto_request(project: SpringBootProject, entity: JavaEntity) -> str:
    fields = "\n".join(_render_dto_field(field.name, field.java_type, field.required, field.email) for field in entity.fields)
    relation_fields = "\n".join(_render_relation_dto_field(relationship) for relationship in _owning_relationships(project, entity))
    imports = _dto_imports(entity)
    if relation_fields:
        imports += "import java.util.UUID;\n"
    return f"""package {project.base_package}.dto;

{imports}import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class {entity.name}Request {{
{fields}
{relation_fields}
}}
"""


def render_dto_response(project: SpringBootProject, entity: JavaEntity) -> str:
    fields = "\n".join(f"    private {field.java_type} {field.name};" for field in entity.fields)
    relation_fields = "\n".join(_render_relation_dto_field(relationship) for relationship in _owning_relationships(project, entity))
    imports = _dto_imports(entity)
    return f"""package {project.base_package}.dto;

{imports}import java.util.UUID;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class {entity.name}Response {{
    private UUID id;
{fields}
{relation_fields}
}}
"""


def render_repository(project: SpringBootProject, entity: JavaEntity) -> str:
    return f"""package {project.base_package}.repository;

import {project.base_package}.entity.{entity.name};
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface {entity.name}Repository extends JpaRepository<{entity.name}, UUID> {{
}}
"""


def render_service(project: SpringBootProject, entity: JavaEntity) -> str:
    assignments = "\n".join(f"        entity.set{field.name[:1].upper() + field.name[1:]}(request.get{field.name[:1].upper() + field.name[1:]}());" for field in entity.fields)
    relation_assignments = "\n".join(_render_relation_assignment(relationship) for relationship in _owning_relationships(project, entity))
    response = "\n".join(f"        response.set{field.name[:1].upper() + field.name[1:]}(entity.get{field.name[:1].upper() + field.name[1:]}());" for field in entity.fields)
    relation_response = "\n".join(_render_relation_response(relationship) for relationship in _owning_relationships(project, entity))
    repository_imports = "".join(
        f"import {project.base_package}.repository.{relationship.target}Repository;\n"
        for relationship in _owning_relationships(project, entity)
    )
    constructor_params = _service_constructor_params(entity, _owning_relationships(project, entity))
    constructor_assignments = _service_constructor_assignments(_owning_relationships(project, entity))
    repository_fields = "".join(
        f"    private final {relationship.target}Repository {to_camel_case(relationship.target)}Repository;\n"
        for relationship in _owning_relationships(project, entity)
    )
    return f"""package {project.base_package}.service;

import {project.base_package}.dto.{entity.name}Request;
import {project.base_package}.dto.{entity.name}Response;
import {project.base_package}.entity.{entity.name};
import {project.base_package}.exception.ResourceNotFoundException;
import {project.base_package}.repository.{entity.name}Repository;
{repository_imports}import jakarta.persistence.EntityNotFoundException;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class {entity.name}Service {{
    private final {entity.name}Repository repository;
{repository_fields}

    public {entity.name}Service({constructor_params}) {{
        this.repository = repository;
{constructor_assignments}
    }}

    @Transactional
    public {entity.name}Response create({entity.name}Request request) {{
        {entity.name} entity = new {entity.name}();
{assignments}
{relation_assignments}
        return toResponse(repository.save(entity));
    }}

    @Transactional(readOnly = true)
    public List<{entity.name}Response> findAll() {{
        return repository.findAll().stream().map(this::toResponse).toList();
    }}

    @Transactional(readOnly = true)
    public {entity.name}Response findById(UUID id) {{
        return toResponse(findEntity(id));
    }}

    @Transactional
    public {entity.name}Response update(UUID id, {entity.name}Request request) {{
        {entity.name} entity = findEntity(id);
{assignments}
{relation_assignments}
        return toResponse(repository.save(entity));
    }}

    @Transactional
    public void delete(UUID id) {{
        repository.delete(findEntity(id));
    }}

    private {entity.name} findEntity(UUID id) {{
        return repository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("{entity.name} no encontrado: " + id));
    }}

    private {entity.name}Response toResponse({entity.name} entity) {{
        {entity.name}Response response = new {entity.name}Response();
        response.setId(entity.getId());
{response}
{relation_response}
        return response;
    }}
}}
"""


def render_controller(project: SpringBootProject, entity: JavaEntity) -> str:
    base_path = to_camel_case(entity.name).lower() + "s"
    return f"""package {project.base_package}.controller;

import {project.base_package}.dto.{entity.name}Request;
import {project.base_package}.dto.{entity.name}Response;
import {project.base_package}.service.{entity.name}Service;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/{base_path}")
public class {entity.name}Controller {{
    private final {entity.name}Service service;

    public {entity.name}Controller({entity.name}Service service) {{
        this.service = service;
    }}

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public {entity.name}Response create(@Valid @RequestBody {entity.name}Request request) {{
        return service.create(request);
    }}

    @GetMapping
    public List<{entity.name}Response> findAll() {{
        return service.findAll();
    }}

    @GetMapping("/{{id}}")
    public {entity.name}Response findById(@PathVariable UUID id) {{
        return service.findById(id);
    }}

    @PutMapping("/{{id}}")
    public {entity.name}Response update(@PathVariable UUID id, @Valid @RequestBody {entity.name}Request request) {{
        return service.update(id, request);
    }}

    @DeleteMapping("/{{id}}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable UUID id) {{
        service.delete(id);
    }}
}}
"""


def render_security_config(project: SpringBootProject) -> str:
    return f"""package {project.base_package}.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfig {{
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {{
        return http
            .csrf(csrf -> csrf.disable())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/swagger-ui.html", "/swagger-ui/**", "/v3/api-docs/**").permitAll()
                .anyRequest().permitAll())
            .build();
    }}
}}
"""


def render_not_found_exception(project: SpringBootProject) -> str:
    return f"""package {project.base_package}.exception;

public class ResourceNotFoundException extends RuntimeException {{
    public ResourceNotFoundException(String message) {{
        super(message);
    }}
}}
"""


def render_exception_handler(project: SpringBootProject) -> str:
    return f"""package {project.base_package}.exception;

import java.time.Instant;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {{
    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<Map<String, Object>> notFound(ResourceNotFoundException exception) {{
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of(
            "timestamp", Instant.now().toString(),
            "status", 404,
            "error", exception.getMessage()));
    }}

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> validation(MethodArgumentNotValidException exception) {{
        return ResponseEntity.badRequest().body(Map.of(
            "timestamp", Instant.now().toString(),
            "status", 400,
            "error", "Datos invalidos"));
    }}
}}
"""


def render_readme(project: SpringBootProject) -> str:
    database_name = project.artifact_id.replace("-", "_")
    endpoints = "\n".join(
        f"- `/api/{to_camel_case(entity.name).lower()}s`" for entity in project.entities
    )
    return f"""# {project.name}

Backend Spring Boot generado automaticamente desde un modelo UML de la plataforma CASE inteligente.

## Ejecucion

Con Docker/PostgreSQL:

```bash
./scripts/run.sh
```

En Windows:

```powershell
.\\scripts\\run.ps1
```

El script levanta PostgreSQL con Docker y usa Maven Wrapper, Maven instalado o descarga Maven localmente en `.tools`.

En Linux/macOS, si el script no tiene permisos:

```bash
chmod +x scripts/run.sh
./scripts/run.sh
```

La base por defecto es `{database_name}` en `127.0.0.1:55432`. Si usa pgAdmin, puede ejecutar `database/init.sql` manualmente antes de iniciar la API.

Variables utiles si necesita cambiar conexion:

```text
POSTGRES_PORT=55432
SPRING_DATASOURCE_URL=jdbc:postgresql://127.0.0.1:55432/{database_name}
SPRING_DATASOURCE_USERNAME=postgres
SPRING_DATASOURCE_PASSWORD=postgres
```

## Validacion

Cuando Maven este disponible, ejecute `mvn test`.

## API

Swagger UI:

```text
http://localhost:8080/swagger-ui.html
```

Endpoints generados:

{endpoints}
"""


def _render_field(name: str, java_type: str, required: bool, email: bool) -> str:
    validations = []
    if required:
        validations.append("    @NotNull")
    if email:
        validations.append("    @Email")
    body = "\n".join(validations)
    if body:
        body += "\n"
    return f"{body}    private {java_type} {name};\n"


def _render_dto_field(name: str, java_type: str, required: bool, email: bool) -> str:
    validations = []
    if required:
        validations.append("    @NotNull")
    if email:
        validations.append("    @Email")
    body = "\n".join(validations)
    if body:
        body += "\n"
    return f"{body}    private {java_type} {name};\n"


def _entity_imports(project: SpringBootProject, entity: JavaEntity) -> str:
    imports = ["import java.util.UUID;"]
    if any(field.java_type == "LocalDate" for field in entity.fields):
        imports.append("import java.time.LocalDate;")
    if any(field.java_type == "LocalDateTime" for field in entity.fields):
        imports.append("import java.time.LocalDateTime;")
    if any(field.required for field in entity.fields):
        imports.append("import jakarta.validation.constraints.NotNull;")
    if any(field.email for field in entity.fields):
        imports.append("import jakarta.validation.constraints.Email;")
    entity_relationships = _owning_relationships(project, entity)
    if any(relationship.annotation == "ManyToOne" for relationship in entity_relationships):
        imports.append("import jakarta.persistence.ManyToOne;")
    return "\n".join(sorted(imports))


def _render_relation_field(project: SpringBootProject, entity: JavaEntity) -> str:
    lines: list[str] = []
    for relationship in _owning_relationships(project, entity):
        target_field = to_camel_case(relationship.target)
        if relationship.annotation == "ManyToOne":
            lines.append(f"    @ManyToOne\n    private {relationship.target} {target_field};\n")
    return "\n".join(lines)


def _owning_relationships(project: SpringBootProject, entity: JavaEntity) -> list[JavaRelationship]:
    return [relationship for relationship in project.relationships if relationship.owner == entity.name and relationship.annotation == "ManyToOne"]


def _relation_id_field(relationship: JavaRelationship) -> str:
    return f"{to_camel_case(relationship.target)}Id"


def _render_relation_dto_field(relationship: JavaRelationship) -> str:
    return f"    private UUID {_relation_id_field(relationship)};\n"


def _render_relation_assignment(relationship: JavaRelationship) -> str:
    target_field = to_camel_case(relationship.target)
    repository = f"{target_field}Repository"
    getter = _relation_id_field(relationship)[:1].upper() + _relation_id_field(relationship)[1:]
    setter = target_field[:1].upper() + target_field[1:]
    return f"""        if (request.get{getter}() != null) {{
            entity.set{setter}({repository}.findById(request.get{getter}())
                .orElseThrow(() -> new EntityNotFoundException("{relationship.target} no encontrado: " + request.get{getter}())));
        }} else {{
            entity.set{setter}(null);
        }}"""


def _render_relation_response(relationship: JavaRelationship) -> str:
    target_field = to_camel_case(relationship.target)
    getter = target_field[:1].upper() + target_field[1:]
    setter = _relation_id_field(relationship)[:1].upper() + _relation_id_field(relationship)[1:]
    return f"        response.set{setter}(entity.get{getter}() != null ? entity.get{getter}().getId() : null);"


def _service_constructor_params(entity: JavaEntity, relationships: list[JavaRelationship]) -> str:
    params = [f"{entity.name}Repository repository"]
    params.extend(f"{relationship.target}Repository {to_camel_case(relationship.target)}Repository" for relationship in relationships)
    return ", ".join(params)


def _service_constructor_assignments(relationships: list[JavaRelationship]) -> str:
    return "\n".join(
        f"        this.{to_camel_case(relationship.target)}Repository = {to_camel_case(relationship.target)}Repository;"
        for relationship in relationships
    )


def _dto_imports(entity: JavaEntity) -> str:
    imports = []
    if any(field.required for field in entity.fields):
        imports.append("import jakarta.validation.constraints.NotNull;")
    if any(field.email for field in entity.fields):
        imports.append("import jakarta.validation.constraints.Email;")
    if any(field.java_type == "LocalDate" for field in entity.fields):
        imports.append("import java.time.LocalDate;")
    if any(field.java_type == "LocalDateTime" for field in entity.fields):
        imports.append("import java.time.LocalDateTime;")
    return "".join(f"{line}\n" for line in sorted(imports))
