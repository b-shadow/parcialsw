from app.modules.generacion_software.backend_generator.analyzer.analizador_modelo import (
    ProyectoSpringBoot,
    analizar_modelo,
)


def analizar_modelo_intermedio(intermediate_model: dict, name: str) -> ProyectoSpringBoot:
    return analizar_modelo(intermediate_model, name)
