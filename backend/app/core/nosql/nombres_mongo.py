"""Traducción de nombres físicos MongoDB sin alterar los modelos de dominio."""

from __future__ import annotations

from inspect import isawaitable
from typing import Any

from app.core.database.nombres_fisicos import COLUMNAS

COLECCIONES = {
    "uml_diagrams": "diagramas_uml",
    "uml_diagram_versions": "versiones_diagrama_uml",
    "ai_messages": "mensajes_ia",
    "ai_context_snapshots": "instantaneas_contexto_ia",
    "migration_checkpoints": "puntos_control_migracion",
    "nosql_processed_events": "eventos_nosql_procesados",
    "nosql_operational_audits": "auditorias_operativas_nosql",
}

CAMPOS = {
    **COLUMNAS,
    "author_user_id": "usuario_autor_id",
    "client_message_id": "mensaje_cliente_id",
    "collection": "coleccion",
    "collection_reports": "informes_colecciones",
    "content": "contenido",
    "content_hash": "hash_contenido",
    "context": "contexto",
    "cursor": "cursor",
    "details": "detalles",
    "detected_intents": "intenciones_detectadas",
    "duration_ms": "duracion_ms",
    "event_id": "evento_id",
    "failed_count": "numero_fallidos",
    "findings": "hallazgos",
    "metrics": "metricas",
    "migration_name": "nombre_migracion",
    "operation": "operacion",
    "processed_count": "numero_procesados",
    "role": "rol",
    "until_sequence": "hasta_secuencia",
    "classes": "clases",
    "diagrams": "diagramas",
    "relationships": "relaciones",
    "attributes": "atributos",
    "methods": "metodos",
    "parameters": "parametros",
    "visual": "visual",
    "style": "estilo",
    "width": "ancho",
    "height": "alto",
    "specification": "especificacion",
    "steps": "pasos",
    "readiness": "preparacion",
    "constraints": "restricciones",
    "default_value": "valor_predeterminado",
    "initial_value": "valor_inicial",
    "is_required": "es_obligatorio",
    "return_type": "tipo_retorno",
    "source_class_id": "clase_origen_id",
    "target_class_id": "clase_destino_id",
    "relationship_type": "tipo_relacion",
    "source_cardinality": "cardinalidad_origen",
    "target_cardinality": "cardinalidad_destino",
    "label": "etiqueta",
    "order_index": "indice_orden",
}
INVERSOS = {valor: clave for clave, valor in CAMPOS.items()}
if len(INVERSOS) != len(CAMPOS):
    raise RuntimeError("La traducción MongoDB tiene nombres físicos duplicados")


def traducir_clave(clave: str, *, al_espanol: bool) -> str:
    mapa = CAMPOS if al_espanol else INVERSOS
    return ".".join(
        segmento if segmento.startswith("$") else mapa.get(segmento, segmento)
        for segmento in clave.split(".")
    )


def traducir_documento(valor: Any, *, al_espanol: bool) -> Any:
    if isinstance(valor, list):
        return [traducir_documento(item, al_espanol=al_espanol) for item in valor]
    if not isinstance(valor, dict):
        return valor
    resultado = {}
    for clave, item in valor.items():
        nueva = traducir_clave(clave, al_espanol=al_espanol)
        if nueva in resultado and nueva != clave:
            raise ValueError(f"Claves MongoDB incompatibles: {clave} / {nueva}")
        if clave in {"collection", "coleccion"} and isinstance(item, str):
            nombres = COLECCIONES if al_espanol else {v: k for k, v in COLECCIONES.items()}
            item = nombres.get(item, item)
        resultado[nueva] = traducir_documento(item, al_espanol=al_espanol)
    return resultado


class CursorTraducido:
    def __init__(self, cursor: Any) -> None:
        self.cursor = cursor

    def sort(self, clave: Any, direccion: Any = None):
        if isinstance(clave, str):
            clave = traducir_clave(clave, al_espanol=True)
        elif isinstance(clave, list):
            clave = [(traducir_clave(campo, al_espanol=True), orden) for campo, orden in clave]
        self.cursor = self.cursor.sort(clave, direccion) if direccion is not None else self.cursor.sort(clave)
        return self

    def limit(self, cantidad: int):
        self.cursor = self.cursor.limit(cantidad)
        return self

    def skip(self, cantidad: int):
        self.cursor = self.cursor.skip(cantidad)
        return self

    def __iter__(self):
        for item in self.cursor:
            yield traducir_documento(item, al_espanol=False)

    async def __aiter__(self):
        async for item in self.cursor:
            yield traducir_documento(item, al_espanol=False)

    def __getattr__(self, nombre: str):
        return getattr(self.cursor, nombre)


class ColeccionTraducida:
    def __init__(self, coleccion: Any) -> None:
        self.coleccion = coleccion

    @staticmethod
    def _resultado(resultado):
        if isawaitable(resultado):
            async def resolver():
                return traducir_documento(await resultado, al_espanol=False)
            return resolver()
        return traducir_documento(resultado, al_espanol=False)

    def find_one(self, filtro, proyeccion=None, *args, **kwargs):
        filtro = traducir_documento(filtro, al_espanol=True)
        proyeccion = traducir_documento(proyeccion, al_espanol=True) if proyeccion is not None else None
        parametros = (filtro, proyeccion) if proyeccion is not None else (filtro,)
        return self._resultado(self.coleccion.find_one(*parametros, *args, **kwargs))

    def find(self, filtro=None, proyeccion=None, *args, **kwargs):
        filtro = traducir_documento(filtro or {}, al_espanol=True)
        proyeccion = traducir_documento(proyeccion, al_espanol=True) if proyeccion is not None else None
        parametros = (filtro, proyeccion) if proyeccion is not None else (filtro,)
        return CursorTraducido(self.coleccion.find(*parametros, *args, **kwargs))

    def aggregate(self, etapas, *args, **kwargs):
        resultado = self.coleccion.aggregate(traducir_documento(etapas, al_espanol=True), *args, **kwargs)
        if isawaitable(resultado):
            async def resolver():
                return CursorTraducido(await resultado)
            return resolver()
        return CursorTraducido(resultado)

    def count_documents(self, filtro, *args, **kwargs):
        return self.coleccion.count_documents(traducir_documento(filtro, al_espanol=True), *args, **kwargs)

    def insert_one(self, documento, *args, **kwargs):
        return self.coleccion.insert_one(traducir_documento(documento, al_espanol=True), *args, **kwargs)

    def insert_many(self, documentos, *args, **kwargs):
        return self.coleccion.insert_many(
            [traducir_documento(item, al_espanol=True) for item in documentos],
            *args, **kwargs,
        )

    def replace_one(self, filtro, documento, *args, **kwargs):
        return self.coleccion.replace_one(
            traducir_documento(filtro, al_espanol=True),
            traducir_documento(documento, al_espanol=True), *args, **kwargs,
        )

    def find_one_and_replace(self, filtro, documento, *args, **kwargs):
        return self._resultado(self.coleccion.find_one_and_replace(
            traducir_documento(filtro, al_espanol=True),
            traducir_documento(documento, al_espanol=True), *args, **kwargs,
        ))

    def update_one(self, filtro, cambio, *args, **kwargs):
        if "array_filters" in kwargs:
            kwargs["array_filters"] = traducir_documento(kwargs["array_filters"], al_espanol=True)
        return self.coleccion.update_one(
            traducir_documento(filtro, al_espanol=True),
            traducir_documento(cambio, al_espanol=True), *args, **kwargs,
        )

    def delete_one(self, filtro, *args, **kwargs):
        return self.coleccion.delete_one(traducir_documento(filtro, al_espanol=True), *args, **kwargs)

    def delete_many(self, filtro, *args, **kwargs):
        return self.coleccion.delete_many(traducir_documento(filtro, al_espanol=True), *args, **kwargs)

    def __getattr__(self, nombre: str):
        return getattr(self.coleccion, nombre)


class BaseMongoTraducida:
    def __init__(self, database: Any) -> None:
        self.database = database

    def __getitem__(self, coleccion: str) -> ColeccionTraducida:
        return ColeccionTraducida(self.database[coleccion])

    def __getattr__(self, nombre: str):
        return getattr(self.database, nombre)


def adaptar_mongo(database: Any) -> BaseMongoTraducida:
    return database if isinstance(database, BaseMongoTraducida) else BaseMongoTraducida(database)
