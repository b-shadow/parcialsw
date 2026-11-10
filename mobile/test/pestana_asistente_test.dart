import 'package:case_inteligente_mobile/core/models/modelos_comunicacion.dart';
import 'package:case_inteligente_mobile/features/projects/widgets/pestana_asistente.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('la pregunta precede a la respuesta y los avisos quedan aparte', (tester) async {
    await tester.binding.setSurfaceSize(const Size(440, 900));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final now = DateTime.now();
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: PestanaAsistente(
      messages: [
        MensajeIA(id: 'notice', role: 'assistant', content: 'Aviso proactivo',
          sequence: 1, createdAt: now, proactive: true),
        MensajeIA(id: 'question', role: 'user', content: '¿Qué recomiendas?',
          sequence: 2, createdAt: now),
        MensajeIA(id: 'answer', role: 'assistant', content: 'Añade atributos a Pago.',
          sequence: 3, createdAt: now),
      ],
      actions: const [], diagrams: const [], sending: false,
      onSend: (content, {diagramId}) async {},
    ))));

    expect(find.text('Aviso proactivo'), findsNothing);
    expect(find.text('¿Qué recomiendas?'), findsOneWidget);
    expect(find.text('Añade atributos a Pago.'), findsOneWidget);
    expect(tester.getTopLeft(find.text('¿Qué recomiendas?')).dy,
      lessThan(tester.getTopLeft(find.text('Añade atributos a Pago.')).dy));
    await tester.tap(find.text('Avisos automáticos de la IA (1)'));
    await tester.pumpAndSettle();
    expect(find.text('Aviso proactivo'), findsOneWidget);
  });
}
