from ai_engine.models import get_model_profile


def check_health() -> dict[str, str | bool]:
    profile = get_model_profile()
    return {
        "status": "ok",
        "component": "ai-engine",
        "mode": "local-offline",
        "selected_model": profile.selected_model,
        "offline": profile.offline,
    }


if __name__ == "__main__":
    print(check_health())
