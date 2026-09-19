from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetExample:
    intent: str
    prompt: str
    expected_classes: list[str]
    expected_relationships: list[tuple[str, str, str]]
    target_artifacts: list[str]


def get_seed_dataset() -> list[DatasetExample]:
    return [
        DatasetExample(
            intent="biblioteca",
            prompt="Crear sistema de biblioteca con usuarios, libros, prestamos y multas",
            expected_classes=["Usuario", "Libro", "Prestamo", "Multa"],
            expected_relationships=[
                ("Usuario", "Prestamo", "association"),
                ("Libro", "Prestamo", "association"),
                ("Prestamo", "Multa", "association"),
            ],
            target_artifacts=["Spring Boot CRUD", "Flutter CRUD", "validacion fechas"],
        ),
        DatasetExample(
            intent="ventas",
            prompt="Sistema de ventas con clientes, pedidos, productos, pagos y facturas",
            expected_classes=["Cliente", "Pedido", "Producto", "Pago", "Factura"],
            expected_relationships=[
                ("Cliente", "Pedido", "association"),
                ("Pedido", "Producto", "association"),
                ("Pedido", "Pago", "association"),
                ("Pedido", "Factura", "association"),
            ],
            target_artifacts=["Spring Boot REST", "Flutter formularios", "PostgreSQL"],
        ),
        DatasetExample(
            intent="academico",
            prompt="Sistema academico con estudiantes, docentes, cursos, inscripciones y evaluaciones",
            expected_classes=["Estudiante", "Docente", "Curso", "Inscripcion", "Evaluacion"],
            expected_relationships=[
                ("Estudiante", "Inscripcion", "association"),
                ("Curso", "Inscripcion", "association"),
                ("Docente", "Curso", "association"),
                ("Curso", "Evaluacion", "composition"),
            ],
            target_artifacts=["roles", "calificaciones", "reportes"],
        ),
        DatasetExample(
            intent="inventario",
            prompt="Gestion de inventario con almacenes, productos, movimientos y proveedores",
            expected_classes=["Almacen", "Producto", "Movimiento", "Proveedor"],
            expected_relationships=[
                ("Almacen", "Movimiento", "composition"),
                ("Producto", "Movimiento", "association"),
                ("Proveedor", "Producto", "association"),
            ],
            target_artifacts=["stock", "auditoria", "validacion cantidades"],
        ),
    ]
