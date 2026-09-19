from app.modules.generacion_software.flutter_generator.uml_analyzer.model_analyzer import (
    DartEntity,
    to_camel_case,
)


def endpoint_for_entity(entity: DartEntity) -> str:
    return f"/api/{to_camel_case(entity.name).lower()}s"
