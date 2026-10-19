# Fase 8 - Reglas UML a Java

## Clases

Cada clase UML se transforma en:

- Entidad JPA.
- DTO request.
- DTO response.
- Repository.
- Service.
- Controller REST.

## Atributos

Reglas de tipo:

| UML | Java |
| --- | --- |
| String | String |
| Integer | Integer |
| Long | Long |
| UUID | UUID |
| Double | Double |
| Boolean | Boolean |
| Date | LocalDate |
| DateTime | LocalDateTime |

## Validaciones

- Campo requerido: `@NotNull`.
- Campo correo/email: `@Email`.

## Relaciones

- Asociacion: `@ManyToOne`.
- Agregacion/composicion: `@OneToMany`.
- Herencia: identificada para extension.
- Implementacion/dependencia: registrada como relacion no persistente base.

## CRUD

Cada entidad genera:

- `POST /api/{entidad}s`
- `GET /api/{entidad}s`
- `GET /api/{entidad}s/{id}`
- `PUT /api/{entidad}s/{id}`
- `DELETE /api/{entidad}s/{id}`
