"""El JSON público en español conserva el contrato interno de los servicios."""

import ast
import json
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.api.intermediario import NombresContratoMiddleware
from app.core.api.nombres_contratos import CLAVES, TRADUCCIONES, traducir_json
from app.main import app


def test_catalogo_publico_es_biunivoco_y_cubre_campos_clave() -> None:
    assert len(set(TRADUCCIONES.values())) == len(TRADUCCIONES)
    assert TRADUCCIONES["model_name"] == "nombre_modelo"
    assert TRADUCCIONES["project_id"] == "proyecto_id"
    assert TRADUCCIONES["classes"] == "clases"
    assert TRADUCCIONES["ai"] == "ia"
    ruta_frontend = Path(__file__).resolve().parents[2] / "frontend/src/core/api/nombresContrato.json"
    assert json.loads(ruta_frontend.read_text(encoding="utf-8")) == TRADUCCIONES
    raiz_frontend = ruta_frontend.parents[2]
    archivos = [
        *raiz_frontend.glob("core/contracts/*.ts"),
        *raiz_frontend.glob("modules/*/types/*.ts"),
    ]
    nombres_ts = {
        nombre
        for archivo in archivos
        for nombre in re.findall(r"^\s*([a-z][a-z0-9_]*)\??\s*:", archivo.read_text(encoding="utf-8"), re.MULTILINE)
        if "_" in nombre
    }
    assert nombres_ts <= TRADUCCIONES.keys()
    raiz_backend = Path(__file__).resolve().parents[1] / "app/modules"
    campos_backend = {
        atributo.target.id
        for archivo in raiz_backend.rglob("schemas/*.py")
        for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8")))
        if isinstance(nodo, ast.ClassDef)
        for atributo in nodo.body
        if isinstance(atributo, ast.AnnAssign) and isinstance(atributo.target, ast.Name)
    }
    assert campos_backend <= set(CLAVES)
    original = {"model_name": "qwen", "classes": [{"name": "Curso"}]}
    assert traducir_json(traducir_json(original, al_espanol=True), al_espanol=False) == original


def test_peticion_y_respuesta_json_se_traducen_solo_con_encabezado_es() -> None:
    servicio = FastAPI()
    servicio.add_middleware(NombresContratoMiddleware)

    @servicio.post("/eco")
    def eco(payload: dict) -> dict:
        return payload

    client = TestClient(servicio)
    enviado = {"nombre_modelo": "qwen", "clases": [{"nombre": "Curso"}]}
    assert client.post("/eco", json=enviado, headers={"X-Contrato-Idioma": "es"}).json() == enviado
    anterior = {"model_name": "qwen", "classes": [{"name": "Curso"}]}
    assert client.post("/eco", json=anterior).json() == anterior
    invalido = client.post(
        "/eco", content="{", headers={"X-Contrato-Idioma": "es", "Content-Type": "application/json"}
    )
    assert invalido.status_code == 422


def test_app_real_publica_respuesta_espanola_y_mantiene_compatibilidad() -> None:
    client = TestClient(app)
    assert client.get("/health", headers={"X-Contrato-Idioma": "es"}).json() == {
        "estado": "ok", "componente": "backend",
    }
    assert client.get("/health").json() == {"status": "ok", "component": "backend"}
