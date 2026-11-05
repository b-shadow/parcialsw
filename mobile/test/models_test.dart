import 'package:case_inteligente_mobile/core/models/modelos_cuenta.dart';
import 'package:case_inteligente_mobile/core/models/modelos_uml.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('ResumenProyecto conserva los datos necesarios para cache privado', () {
    final project = ResumenProyecto.fromJson({
      'id': 'project-1',
      'name': 'Ventas',
      'project_role': 'ORGANIZADOR',
      'status': 'active',
      'diagram_count': 3,
      'member_count': 2,
      'unread_notification_count': 4,
      'updated_at': '2026-10-17T12:00:00Z',
    });
    expect(project.unreadCount, 4);
    expect(ResumenProyecto.fromJson(project.toJson()).name, 'Ventas');
  });

  test(
    'DetalleDiagrama interpreta posicion visual y fuerza contrato explicito',
    () {
      final diagram = DetalleDiagrama.fromJson({
        'diagram': {'id': 'd1', 'name': 'Modelo'},
        'logical_version': 7,
        'can_edit': false,
        'classes': [
          {
            'id': 'c1',
            'name': 'Pedido',
            'attributes': [],
            'methods': [],
            'visual': {'position_x': 120, 'position_y': 80, 'width': 240},
          },
        ],
        'relationships': [],
      });
      expect(diagram.canEdit, isFalse);
      expect(diagram.classes.single.x, 120);
      expect(diagram.classes.single.width, 240);
    },
  );

  test('el visor conserva parametros y coordenadas del modelo UML', () {
    final diagrama = DetalleDiagrama.fromJson({
      'diagram': {'id': 'd2', 'name': 'Cursos'},
      'logical_version': 1,
      'can_edit': false,
      'classes': [
        {
          'id': 'c1',
          'name': 'Curso',
          'element_type': 'interface',
          'attributes': [],
          'methods': [
            {
              'name': 'inscribir',
              'return_type': 'void',
              'visibility': 'public',
              'parameters': [
                {'name': 'estudiante', 'data_type': 'UUID'},
              ],
            },
          ],
          'visual': {'x': 340, 'y': 175, 'width': 230, 'height': 150},
        },
      ],
      'relationships': [],
    });
    final clase = diagrama.classes.single;
    expect(clase.x, 340);
    expect(clase.y, 175);
    expect(clase.elementType, 'interface');
    expect(clase.methods.single.firma, 'inscribir(estudiante: UUID): void');
    expect(
      DetalleDiagrama.fromJson(
        diagrama.toJson(),
      ).classes.single.methods.single.parameters.single.name,
      'estudiante',
    );
  });
}
