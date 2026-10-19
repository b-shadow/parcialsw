import 'package:case_inteligente_mobile/core/models/account_models.dart';
import 'package:case_inteligente_mobile/core/models/uml_models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('ProjectSummary conserva los datos necesarios para cache privado', () {
    final project = ProjectSummary.fromJson({
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
    expect(ProjectSummary.fromJson(project.toJson()).name, 'Ventas');
  });

  test(
    'DiagramDetail interpreta posicion visual y fuerza contrato explicito',
    () {
      final diagram = DiagramDetail.fromJson({
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
}
