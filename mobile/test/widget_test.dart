import 'package:case_inteligente_mobile/core/models/uml_models.dart';
import 'package:case_inteligente_mobile/features/uml/widgets/uml_readonly_canvas.dart';
import 'package:case_inteligente_mobile/shared/widgets/content_states.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('el estado vacio usa una accion reutilizable', (tester) async {
    var retried = false;
    await tester.pumpWidget(
      MaterialApp(
        home: EmptyState(
          icon: Icons.folder_off_outlined,
          title: 'Sin datos',
          message: 'No existen elementos.',
          onRetry: () => retried = true,
        ),
      ),
    );

    expect(find.text('Sin datos'), findsOneWidget);
    await tester.tap(find.text('Reintentar'));
    expect(retried, isTrue);
  });

  testWidgets('el lienzo UML muestra clases pero no controles de edicion', (
    tester,
  ) async {
    const diagram = DiagramDetail(
      id: 'diagram-1',
      name: 'Ventas',
      logicalVersion: 2,
      canEdit: false,
      classes: [
        UmlClassNode(
          id: 'class-1',
          name: 'Cliente',
          x: 20,
          y: 20,
          width: 230,
          height: 130,
          attributes: [UmlAttribute('id', 'UUID', 'private', null)],
          methods: [],
        ),
      ],
      relationships: [],
    );
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: UmlReadonlyCanvas(diagram: diagram)),
      ),
    );

    expect(find.text('Cliente'), findsOneWidget);
    expect(find.byIcon(Icons.add), findsOneWidget);
    expect(find.text('Guardar'), findsNothing);
    expect(find.text('Eliminar'), findsNothing);
  });
}
