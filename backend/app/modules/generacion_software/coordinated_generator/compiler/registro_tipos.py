import re

from app.modules.generacion_software.coordinated_generator.contracts import PlanTipoLogico

TYPE_REGISTRY = {
    "string": ("text", "String", "String", "string", None),
    "str": ("text", "String", "String", "string", None),
    "char": ("text", "String", "String", "string", None),
    "character": ("text", "String", "String", "string", None),
    "text": ("text", "String", "String", "string", None),
    "integer": ("integer", "Integer", "int", "integer", "int32"),
    "int": ("integer", "Integer", "int", "integer", "int32"),
    "long": ("long", "Long", "int", "integer", "int64"),
    "double": ("decimal", "Double", "double", "number", "double"),
    "float": ("decimal", "Double", "double", "number", "double"),
    "decimal": ("decimal", "BigDecimal", "double", "number", "decimal"),
    "bigdecimal": ("decimal", "BigDecimal", "double", "number", "decimal"),
    "boolean": ("boolean", "Boolean", "bool", "boolean", None),
    "bool": ("boolean", "Boolean", "bool", "boolean", None),
    "date": ("date", "LocalDate", "DateTime", "string", "date"),
    "localdate": ("date", "LocalDate", "DateTime", "string", "date"),
    "datetime": ("datetime", "LocalDateTime", "DateTime", "string", "date-time"),
    "localdatetime": ("datetime", "LocalDateTime", "DateTime", "string", "date-time"),
    "timestamp": ("datetime", "LocalDateTime", "DateTime", "string", "date-time"),
    "uuid": ("uuid", "UUID", "String", "string", "uuid"),
    "void": ("void", "void", "void", "null", None),
}


def normalizar_nombre_tipo(value: str | None) -> str:
    return re.sub(r"\s+", "", str(value or "String")).casefold()


def resolver_tipo_logico(
    source: str | None,
    *,
    entity_by_name: dict[str, tuple[str, str]] | None = None,
    nullable: bool = True,
) -> PlanTipoLogico | None:
    raw = str(source or "String").strip()
    normalized = normalizar_nombre_tipo(raw)
    if normalized in TYPE_REGISTRY:
        logical, java, dart, json_type, json_format = TYPE_REGISTRY[normalized]
        return PlanTipoLogico(
            logical=logical,
            source=raw,
            java=java,
            dart=dart,
            json_type=json_type,
            json_format=json_format,
            nullable=nullable,
        )
    entities = entity_by_name or {}
    entity = entities.get(normalized)
    if entity:
        entity_id, entity_name = entity
        return PlanTipoLogico(
            logical="entity_reference",
            source=raw,
            java=f"{entity_name}Response",
            dart=entity_name,
            json_type="object",
            nullable=nullable,
            entity_id=entity_id,
        )
    list_match = re.fullmatch(r"(?:list|set|collection)<(.+)>", normalized)
    if list_match:
        item = resolver_tipo_logico(
            list_match.group(1), entity_by_name=entities, nullable=False
        )
        if item:
            return PlanTipoLogico(
                logical="list",
                source=raw,
                java=f"List<{item.java}>",
                dart=f"List<{item.dart}>",
                json_type="array",
                nullable=nullable,
                entity_id=item.entity_id,
            )
    return None
