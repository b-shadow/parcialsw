from app.core.nosql.nombres_mongo import ColeccionTraducida


def test_find_one_ordena_auditorias_por_fecha_fisica() -> None:
    class Coleccion:
        def find_one(self, filtro, proyeccion, *, sort):
            assert filtro == {}
            assert proyeccion == {"estado": 1, "fecha_creacion": 1}
            assert sort == [("fecha_creacion", -1)]
            return {"estado": "healthy", "fecha_creacion": 123}

    auditoria = ColeccionTraducida(Coleccion()).find_one(
        {}, {"status": 1, "created_at": 1}, sort=[("created_at", -1)]
    )
    assert auditoria == {"status": "healthy", "created_at": 123}
