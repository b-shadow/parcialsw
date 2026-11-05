"""Renombra clases de modelos internos sin modificar las rutas públicas HTTP."""

import ast
import io
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLASES = {
    "AuditLog": "RegistroAuditoria", "Role": "Rol", "UserSession": "SesionUsuario",
    "User": "Usuario", "UserRole": "RolUsuario", "AiAction": "AccionIA",
    "AiConversation": "ConversacionIA", "AiMessage": "MensajeIA",
    "AiProjectSettings": "ConfiguracionIAProyecto", "AiRecommendation": "RecomendacionIA",
    "AiProcess": "ProcesoIA", "CoordinatedGeneration": "GeneracionCoordinada",
    "FlutterThemeSettings": "ConfiguracionTemaFlutter", "FlutterThemePreset": "TemaFlutterPredefinido",
    "GeneratedArtifact": "ArtefactoGenerado", "GeneratedBackend": "BackendGenerado",
    "GeneratedFrontend": "FrontendGenerado", "UmlTransformation": "TransformacionUML",
    "AtributoUMLMotor": "AtributoUML", "ClaseUMLMotor": "ClaseUML", "UmlDiagram": "DiagramaUML",
    "MetodoUMLMotor": "MetodoUML", "UmlMethodSpecification": "EspecificacionMetodoUML",
    "UmlParameter": "ParametroUML", "RelacionUMLMotor": "RelacionUML",
    "UmlVisualElement": "ElementoVisualUML", "XmiExchange": "IntercambioXMI",
    "Notification": "Notificacion", "NotificationOutbox": "BandejaSalidaNotificacion",
    "NotificationPreference": "PreferenciaNotificacion", "PushSubscription": "SuscripcionPush",
    "CollaborationEvent": "EventoColaboracion", "Project": "Proyecto",
    "ProjectInvitation": "InvitacionProyecto", "ProjectMember": "IntegranteProyecto",
    "ProjectRestoreOperation": "RestauracionProyecto", "ProjectVersion": "VersionProyecto",
}


def transformar(path: Path) -> bool:
    original = path.read_text(encoding="utf-8-sig")
    tokens = []
    changed = False
    for token in tokenize.generate_tokens(io.StringIO(original).readline):
        replacement = None
        if token.type == tokenize.NAME and token.string in CLASES:
            replacement = CLASES[token.string]
        elif token.type == tokenize.STRING and "models" in path.parts:
            try:
                literal = ast.literal_eval(token.string)
            except (ValueError, SyntaxError):
                literal = None
            if isinstance(literal, str) and literal in CLASES:
                replacement = repr(CLASES[literal])
        if replacement is not None and replacement != token.string:
            token = tokenize.TokenInfo(token.type, replacement, token.start, token.end, token.line)
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
