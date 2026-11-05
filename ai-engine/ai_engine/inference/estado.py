from ai_engine.models import obtener_perfil_modelo


def comprobar_estado() -> dict[str, str | bool]:
    profile = obtener_perfil_modelo()
    return {
        "status": "ok",
        "component": "ai-engine",
        "mode": "local-offline",
        "selected_model": profile.selected_model,
        "offline": profile.offline,
    }


if __name__ == "__main__":
    print(comprobar_estado())
