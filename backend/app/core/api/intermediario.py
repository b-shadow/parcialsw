"""Contrato JSON en español solicitado por clientes nuevos.

Las rutas y modelos internos conservan compatibilidad mientras los consumidores
adoptan el contrato nuevo. El encabezado evita cambiar respuestas de clientes
antiguos durante la transición.
"""

from __future__ import annotations

import json

from app.core.api.nombres_contratos import traducir_json


class NombresContratoMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        encabezados = dict(scope.get("headers", []))
        if encabezados.get(b"x-contrato-idioma", b"").lower() != b"es":
            await self.app(scope, receive, send)
            return

        if b"application/json" in encabezados.get(b"content-type", b""):
            cuerpo = bytearray()
            while True:
                mensaje = await receive()
                if mensaje["type"] != "http.request":
                    break
                cuerpo.extend(mensaje.get("body", b""))
                if not mensaje.get("more_body", False):
                    break
            if cuerpo:
                try:
                    traducido = traducir_json(json.loads(cuerpo), al_espanol=False)
                except json.JSONDecodeError:
                    pass  # FastAPI conserva su respuesta habitual para JSON inválido.
                else:
                    cuerpo = bytearray(json.dumps(traducido, ensure_ascii=False).encode("utf-8"))
            entregado = False

            async def recibir_traducido():
                nonlocal entregado
                if not entregado:
                    entregado = True
                    return {"type": "http.request", "body": bytes(cuerpo), "more_body": False}
                return await receive()

            receive = recibir_traducido
            scope = dict(scope)
            scope["headers"] = [
                (clave, str(len(cuerpo)).encode("ascii")) if clave == b"content-length" else (clave, valor)
                for clave, valor in scope["headers"]
            ]

        inicio = None
        fragmentos = []
        es_json = False

        async def enviar_traducido(mensaje):
            nonlocal inicio, es_json
            if mensaje["type"] == "http.response.start":
                es_json = b"application/json" in dict(mensaje.get("headers", [])).get(
                    b"content-type", b""
                )
                if es_json:
                    inicio = mensaje
                    return
            if mensaje["type"] == "http.response.body" and es_json:
                fragmentos.append(mensaje.get("body", b""))
                if mensaje.get("more_body", False):
                    return
                contenido = b"".join(fragmentos)
                if contenido:
                    contenido = json.dumps(
                        traducir_json(json.loads(contenido), al_espanol=True),
                        ensure_ascii=False,
                    ).encode("utf-8")
                assert inicio is not None
                inicio["headers"] = [
                    (clave, str(len(contenido)).encode("ascii"))
                    if clave == b"content-length" else (clave, valor)
                    for clave, valor in inicio.get("headers", [])
                ]
                await send(inicio)
                await send({"type": "http.response.body", "body": contenido, "more_body": False})
                return
            await send(mensaje)

        await self.app(scope, receive, enviar_traducido)
