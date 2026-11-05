"""Actualiza los mapeos físicos ORM sin modificar nombres de contratos HTTP.

Idempotente: no vuelve a insertar el nombre de una columna ya traducida.
"""

import ast
import json
import re
from pathlib import Path

from app.core.database.nombres_fisicos import COLUMNAS, TABLAS

ROOT = Path(__file__).resolve().parents[1] / "app"


def traducir_referencia(value: str) -> str:
    if "." not in value:
        return value
    table, column = value.split(".", 1)
    if table in TABLAS:
        return f"{TABLAS[table]}.{COLUMNAS.get(column, column)}"
    return value


def transformar(path: Path) -> bool:
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    starts = [0]
    for line in source.splitlines(keepends=True):
        starts.append(starts[-1] + len(line.encode("utf-8")))
    changes: list[tuple[int, int, bytes]] = []

    def span(node: ast.AST) -> tuple[int, int]:
        return starts[node.lineno - 1] + node.col_offset, starts[node.end_lineno - 1] + node.end_col_offset

    def replace(node: ast.AST, value: str) -> None:
        a, b = span(node)
        changes.append((a, b, json.dumps(value, ensure_ascii=False).encode("utf-8")))

    for cls in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        table = None
        for stmt in cls.body:
            if isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__tablename__" for t in stmt.targets):
                if isinstance(stmt.value, ast.Constant) and stmt.value.value in TABLAS:
                    table = stmt.value.value
                    replace(stmt.value, TABLAS[table])
                elif isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                    table = stmt.value.value
        if table is None and cls.name != "ComponenteMarcasTiempo":
            continue
        for stmt in cls.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                column = stmt.target.id
                call = stmt.value
                if (column in COLUMNAS and COLUMNAS[column] != column and isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Name) and call.func.id == "mapped_column"
                    and not (call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str))):
                    pos = starts[call.func.end_lineno - 1] + call.func.end_col_offset + 1
                    changes.append((pos, pos, (json.dumps(COLUMNAS[column]) + ", ").encode("utf-8")))
            if isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__table_args__" for t in stmt.targets):
                for node in ast.walk(stmt.value):
                    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                        continue
                    value = node.value
                    if value in COLUMNAS and COLUMNAS[value] != value:
                        replace(node, COLUMNAS[value])
                    elif any(isinstance(parent, ast.Call) and isinstance(parent.func, ast.Name) and parent.func.id in {"CheckConstraint", "text"} for parent in ast.walk(stmt.value)):
                        if value.startswith(("ix_", "uq_", "ck_", "fk_")):
                            continue
                        translated = re.sub(r"\b[A-Za-z_][A-Za-z0-9_]*\b", lambda m: COLUMNAS.get(m.group(), m.group()), value)
                        if translated != value:
                            replace(node, translated)
    # Todas las referencias FK, incluso las de modelos SQL retirados, deben apuntar al nombre vigente.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "ForeignKey":
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                old = node.args[0].value
                new = traducir_referencia(old)
                if old != new:
                    replace(node.args[0], new)
    if not changes:
        return False
    result = source.encode("utf-8")
    for a, b, new in sorted(changes, key=lambda item: item[0], reverse=True):
        result = result[:a] + new + result[b:]
    path.write_bytes(result)
    return True


if __name__ == "__main__":
    paths = [*ROOT.rglob("models/*.py"), ROOT / "core/nosql/outbox_model.py", ROOT / "core/database/mixins.py"]
    for path in paths:
        if transformar(path):
            print(path.relative_to(ROOT))
