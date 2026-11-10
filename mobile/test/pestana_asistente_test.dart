import 'package:case_inteligente_mobile/core/models/modelos_comunicacion.dart';
import 'package:case_inteligente_mobile/features/projects/widgets/pestana_asistente.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('la pregunta precede a la respuesta y los avisos quedan aparte', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(440, 900));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final now = DateTime.now();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PestanaAsistente(
            messages: [
              MensajeIA(
                id: 'notice',
                role: 'assistant',
                content: 'Aviso proactivo',
                sequence: 1,
                createdAt: now,
                proactive: true,
              ),
              MensajeIA(
                id: 'question',
                role: 'user',
                content: '¿Qué recomiendas?',
                sequence: 2,
                createdAt: now,
              ),
              MensajeIA(
                id: 'answer',
                role: 'assistant',
                content: 'Añade atributos a Pago.',
                sequence: 3,
                createdAt: now,
              ),
            ],
            actions: const [],
            diagrams: const [],
            sending: false,
            onSend: (content, {diagramId}) async {},
          ),
        ),
      ),
    );

    expect(find.text('Aviso proactivo'), findsNothing);
    expect(find.text('¿Qué recomiendas?'), findsOneWidget);
    expect(find.text('Añade atributos a Pago.'), findsOneWidget);
    expect(
      tester.getTopLeft(find.text('¿Qué recomiendas?')).dy,
      lessThan(tester.getTopLeft(find.text('Añade atributos a Pago.')).dy),
    );
    await tester.tap(find.text('Avisos automáticos de la IA (1)'));
    await tester.pumpAndSettle();
    expect(find.text('Aviso proactivo'), findsOneWidget);
  });

  testWidgets(
    'muestra el atributo aplicado bajo la respuesta sin exponer el ID',
    (tester) async {
      await tester.binding.setSurfaceSize(const Size(440, 900));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final now = DateTime.now();
      const id = '919aeb29-687b-484d-9c0d-8566156a8192';
      final action = AccionIA.fromJson({
        'id': 'action-1',
        'source_message_id': 'answer-1',
        'action_type': 'create_attribute',
        'status': 'applied',
        'risk_level': 'low',
        'payload': {
          'name': 'cantidad',
          'data_type': 'Integer',
          '_plan': {
            'order': 1,
            'explanation': 'Agregar cantidad: Integer a Pedido.',
          },
        },
      });
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PestanaAsistente(
              messages: [
                MensajeIA(
                  id: 'question-1',
                  role: 'user',
                  content:
                      'Corrige el diagrama\nID de recomendación: $id\nMi criterio: añade cantidad',
                  sequence: 1,
                  createdAt: now,
                ),
                MensajeIA(
                  id: 'answer-1',
                  role: 'assistant',
                  content: 'Preparé 1 corrección.',
                  sequence: 2,
                  createdAt: now,
                ),
              ],
              actions: [action],
              diagrams: const [],
              sending: false,
              onSend: (content, {diagramId}) async {},
            ),
          ),
        ),
      );

      expect(find.textContaining('ID de recomendación'), findsNothing);
      expect(find.text('Agregar cantidad: Integer a Pedido.'), findsOneWidget);
      expect(find.text('Aplicado al diagrama'), findsOneWidget);
      expect(
        tester.getTopLeft(find.text('Preparé 1 corrección.')).dy,
        lessThan(
          tester
              .getTopLeft(find.text('Agregar cantidad: Integer a Pedido.'))
              .dy,
        ),
      );
    },
  );
}
