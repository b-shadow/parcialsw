__all__ = ["ServicioIALocal"]


def __getattr__(name: str):
    if name == "ServicioIALocal":
        from ai_engine.services.servicio_ia_local import ServicioIALocal

        return ServicioIALocal
    raise AttributeError(name)
