from app.modules.generacion_software.coordinated_generator.contracts import GenerationPlan


class GenerationPreflightError(ValueError):
    def __init__(self, plan: GenerationPlan) -> None:
        self.plan = plan
        detail = "; ".join(f"{item.code}: {item.message}" for item in plan.errors)
        super().__init__(detail or "El plan de generacion no es ejecutable.")


def ensure_plan_ready(plan: GenerationPlan) -> GenerationPlan:
    if not plan.ready:
        raise GenerationPreflightError(plan)
    return plan
