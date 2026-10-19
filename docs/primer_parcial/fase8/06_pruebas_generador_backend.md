# Fase 8 - Pruebas del generador backend

## Pruebas automatizadas

Archivo:

- `backend/tests/test_phase8_spring_boot_generator.py`

Cobertura:

- Generacion de proyecto Spring Boot.
- Creacion de `pom.xml`.
- Creacion de `README.md`.
- Creacion de ZIP.
- Entidades JPA.
- Relacion `@ManyToOne`.
- Servicios CRUD.
- Controladores REST.
- Contrato OpenAPI de descarga.

## Validacion Maven

Proyecto de muestra:

```text
storage/generated/backend/phase8-sample/sistemaventas
```

Comando:

```powershell
mvn test
```

Resultado:

- `BUILD SUCCESS`
- Compilacion Java 17 correcta.

## Validacion general

- Backend `ruff check .`: correcto.
- Backend `pytest -q`: 10 pruebas correctas.
- AI Engine `pytest -q`: 3 pruebas correctas.
- Frontend `npm run lint`: correcto.
- Frontend `npm run test`: 1 prueba correcta.
- Frontend `npm run build`: correcto.
