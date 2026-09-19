from app.main import app


def test_phase7_ai_openapi_contracts_are_registered() -> None:
    paths = app.openapi()["paths"]
    expected_paths = {
        "/api/v1/ai/profile",
        "/api/v1/ai/uml/text",
        "/api/v1/ai/uml/voice",
        "/api/v1/ai/uml/image",
        "/api/v1/ai/uml/validate",
        "/api/v1/ai/software/plan",
    }
    assert expected_paths.issubset(paths.keys())
