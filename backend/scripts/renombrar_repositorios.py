"""Renombra los métodos internos del repositorio del asistente en el backend."""

import io
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOMBRES = {
    "RepositorioAsistente": "RepositorioAsistente",
    "get_settings": "obtener_configuracion",
    "get_conversation": "obtener_conversacion",
    "list_conversations": "listar_conversaciones",
    "get_message_by_client_id": "obtener_mensaje_por_id_cliente",
    "get_assistant_message_by_correlation": "obtener_mensaje_asistente_por_correlacion",
    "list_messages": "listar_mensajes",
    "message_exists_before": "existe_mensaje_anterior",
    "message_exists_after": "existe_mensaje_posterior",
    "save_message": "guardar_mensaje",
    "user_display_names": "nombres_visibles_usuarios",
    "list_actions": "listar_acciones",
    "get_action": "obtener_accion",
    "get_action_by_idempotency": "obtener_accion_por_idempotencia",
    "list_actions_for_message": "listar_acciones_por_mensaje",
    "list_recommendations_for_message": "listar_recomendaciones_por_mensaje",
    "list_recommendations": "listar_recomendaciones",
    "get_recommendation": "obtener_recomendacion",
}


def transformar(path: Path) -> bool:
    original = path.read_text(encoding="utf-8-sig")
    tokens = []
    changed = False
    for token in tokenize.generate_tokens(io.StringIO(original).readline):
        if token.type == tokenize.NAME and token.string in NOMBRES:
            token = tokenize.TokenInfo(token.type, NOMBRES[token.string], token.start, token.end, token.line)
            changed = True
        tokens.append(token)
    if changed:
        path.write_text(tokenize.untokenize(tokens), encoding="utf-8")
    return changed


if __name__ == "__main__":
    for base in (ROOT / "app", ROOT / "tests", ROOT / "scripts"):
        for path in base.rglob("*.py"):
            if transformar(path):
                print(path.relative_to(ROOT))
