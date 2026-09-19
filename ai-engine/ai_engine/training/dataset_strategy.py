def get_dataset_strategy() -> dict[str, object]:
    return {
        "datasets": [
            "descripciones_textuales_uml",
            "diagramas_xmi",
            "plantillas_spring_boot",
            "plantillas_flutter",
        ],
        "fine_tuning": ["LoRA", "QLoRA"],
        "metrics": [
            "exactitud_clases",
            "exactitud_relaciones",
            "compilacion_codigo",
            "calidad_reconstruccion_imagen",
        ],
        "offline_policy": "El entrenamiento puede usar recursos controlados; la inferencia de producto es local.",
    }
