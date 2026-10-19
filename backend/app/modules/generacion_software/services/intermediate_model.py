from copy import deepcopy


def adapt_intermediate_model_v1_to_v2(source: dict) -> dict:
    model = deepcopy(source)
    version = model.get("schema_version", 1)
    if version == 2:
        return model
    if version != 1:
        raise ValueError(f"Version de modelo intermedio no soportada: {version}")
    model["schema_version"] = 2
    for uml_class in model.get("classes", []):
        for method in uml_class.get("methods", []):
            method.setdefault("parameters", [])
            method.setdefault("specification", None)
            method.setdefault(
                "readiness",
                {
                    "status": "legacy",
                    "ready_for_generation": False,
                    "diagnostics": [],
                },
            )
    return model


def require_supported_intermediate_model(source: dict) -> dict:
    return adapt_intermediate_model_v1_to_v2(source)
