from app.modules.generacion_software.flutter_generator.uml_analyzer.analizador_modelo import (
    EntidadDart,
    a_camel_case,
)


def endpoint_para_entidad(entity: EntidadDart) -> str:
    return f"/api/{a_camel_case(entity.name).lower()}s"
