from ai_engine.services.contratos import PerfilModelo


def obtener_perfil_modelo() -> PerfilModelo:
    return PerfilModelo(
        selected_model="CASE-UML-Local-RuleModel-v1",
        runtime="python-rule-engine + local-rag + qwen-coder-profile",
        offline=True,
        memory_profile="low-memory-cpu",
        license_policy="sin dependencia de APIs externas en ejecucion",
        supported_tasks=[
            "text_to_uml",
            "voice_to_text_to_uml",
            "image_description_to_uml",
            "uml_validation",
            "spring_boot_plan",
            "flutter_plan",
            "uml_modification",
            "knowledge_search",
            "offline_evaluation",
            "code_generation_guidance",
        ],
    )
