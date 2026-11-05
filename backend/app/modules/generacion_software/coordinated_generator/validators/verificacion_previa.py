from app.modules.generacion_software.coordinated_generator.contracts import PlanGeneracion


class ErrorVerificacionPreviaGeneracion(ValueError):
    def __init__(self, plan: PlanGeneracion) -> None:
        self.plan = plan
        detail = "; ".join(f"{item.code}: {item.message}" for item in plan.errors)
        super().__init__(detail or "El plan de generacion no es ejecutable.")


def asegurar_plan_listo(plan: PlanGeneracion) -> PlanGeneracion:
    if not plan.ready:
        raise ErrorVerificacionPreviaGeneracion(plan)
    return plan
