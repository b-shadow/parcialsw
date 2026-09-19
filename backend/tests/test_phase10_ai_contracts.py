from app.main import app


def test_phase10_ai_openapi_contracts_are_registered() -> None:
    paths = app.openapi()["paths"]
    expected_paths = {
        "/api/v1/ai/generate-uml",
        "/api/v1/ai/analyze-image",
        "/api/v1/ai/validate-model",
        "/api/v1/ai/uml/modify",
        "/api/v1/ai/generate-code",
        "/api/v1/ai/knowledge/search",
        "/api/v1/ai/dataset/summary",
        "/api/v1/ai/training/plan",
        "/api/v1/ai/evaluation/offline",
    }
    assert expected_paths.issubset(paths.keys())
