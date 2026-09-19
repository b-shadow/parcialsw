from app.modules.generacion_software.backend_generator.analyzer.model_analyzer import (
    SpringBootProject,
    analyze_model,
)


def parse_intermediate_model(intermediate_model: dict, name: str) -> SpringBootProject:
    return analyze_model(intermediate_model, name)
