from pydantic import BaseModel

from ai_engine.datasets import get_seed_dataset


class TrainingPlan(BaseModel):
    base_models: list[str]
    selected_primary_model: str
    selected_small_model: str
    runtime: str
    techniques: list[str]
    dataset_records: int
    stages: list[str]
    metrics: list[str]
    offline_policy: str


def build_training_plan() -> TrainingPlan:
    dataset = get_seed_dataset()
    return TrainingPlan(
        base_models=["Llama", "Mistral", "Qwen", "DeepSeek Coder"],
        selected_primary_model="Qwen2.5-Coder-7B-Instruct cuantizado",
        selected_small_model="Qwen2.5-Coder-1.5B-Instruct cuantizado",
        runtime="llama.cpp/Ollama local con fallback python-rule-engine",
        techniques=["SFT", "LoRA", "QLoRA", "RAG local"],
        dataset_records=len(dataset),
        stages=[
            "normalizacion de requerimientos",
            "etiquetado UML",
            "pares UML a Spring Boot",
            "pares UML a Flutter",
            "evaluacion offline",
        ],
        metrics=[
            "precision_clases",
            "precision_relaciones",
            "compilacion_backend",
            "compilacion_flutter",
            "calidad_validacion_uml",
        ],
        offline_policy="La inferencia de producto funciona sin APIs externas ni llamadas de red.",
    )
