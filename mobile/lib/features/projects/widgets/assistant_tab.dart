import 'package:flutter/material.dart';

import '../../../core/models/communication_models.dart';
import '../../../core/models/uml_models.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/widgets/content_states.dart';

class AssistantTab extends StatefulWidget {
  final List<AiMessage> messages;
  final List<AiAction> actions;
  final List<DiagramSummary> diagrams;
  final bool sending;
  final Future<void> Function(String content, {String? diagramId}) onSend;
  const AssistantTab({
    super.key,
    required this.messages,
    required this.actions,
    required this.diagrams,
    required this.sending,
    required this.onSend,
  });

  @override
  State<AssistantTab> createState() => _AssistantTabState();
}

class _AssistantTabState extends State<AssistantTab> {
  final _input = TextEditingController();
  String? _diagramId;

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final value = _input.text.trim();
    if (value.isEmpty) return;
    FocusScope.of(context).unfocus();
    try {
      await widget.onSend(value, diagramId: _diagramId);
      _input.clear();
    } on ApiException catch (exception) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(exception.message)));
    }
  }

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Container(
        width: double.infinity,
        color: const Color(0xFFFFF6DF),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
        child: const Text(
          'Consulta y recomendaciones. Las acciones que modifican UML se confirman en escritorio.',
          style: TextStyle(fontSize: 12, color: Color(0xFF6E4B00)),
        ),
      ),
      if (widget.diagrams.isNotEmpty)
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 10, 12, 0),
          child: DropdownButtonFormField<String?>(
            initialValue: _diagramId,
            decoration: const InputDecoration(
              labelText: 'Contexto UML',
              prefixIcon: Icon(Icons.schema_outlined),
            ),
            items: [
              const DropdownMenuItem<String?>(
                value: null,
                child: Text('Proyecto completo'),
              ),
              ...widget.diagrams.map(
                (diagram) => DropdownMenuItem<String?>(
                  value: diagram.id,
                  child: Text(
                    diagram.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ),
            ],
            onChanged: (value) => setState(() => _diagramId = value),
          ),
        ),
      if (widget.actions.any((item) => item.status == 'proposed'))
        Container(
          width: double.infinity,
          margin: const EdgeInsets.fromLTRB(12, 10, 12, 0),
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: const Color(0xFFEAF3FA),
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: const Color(0xFFBDD5E8)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Propuestas pendientes',
                style: TextStyle(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 5),
              ...widget.actions
                  .where((item) => item.status == 'proposed')
                  .take(3)
                  .map(
                    (item) => Text(
                      '${item.actionType.replaceAll('_', ' ')} (${item.riskLevel})',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
              const SizedBox(height: 4),
              const Text(
                'Revisar y confirmar desde escritorio.',
                style: TextStyle(fontSize: 12),
              ),
            ],
          ),
        ),
      Expanded(
        child: widget.messages.isEmpty
            ? const EmptyState(
                icon: Icons.auto_awesome_outlined,
                title: 'Asistente del proyecto',
                message:
                    'Pregunta por el modelo, decisiones o recomendaciones.',
              )
            : ListView.builder(
                reverse: true,
                padding: const EdgeInsets.all(14),
                itemCount: widget.messages.length,
                itemBuilder: (context, reverseIndex) {
                  final index = widget.messages.length - 1 - reverseIndex;
                  final message = widget.messages[index];
                  final user = message.role == 'user';
                  return Align(
                    alignment: user
                        ? Alignment.centerRight
                        : Alignment.centerLeft,
                    child: Container(
                      constraints: const BoxConstraints(maxWidth: 340),
                      margin: const EdgeInsets.only(bottom: 9),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: user ? const Color(0xFF087F78) : Colors.white,
                        borderRadius: BorderRadius.circular(8),
                        border: user
                            ? null
                            : Border.all(color: const Color(0xFFD9E5E7)),
                      ),
                      child: Text(
                        message.content,
                        style: TextStyle(color: user ? Colors.white : null),
                      ),
                    ),
                  );
                },
              ),
      ),
      SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: TextField(
                  controller: _input,
                  minLines: 1,
                  maxLines: 4,
                  textInputAction: TextInputAction.newline,
                  decoration: const InputDecoration(
                    hintText: 'Escribe una consulta',
                  ),
                ),
              ),
              const SizedBox(width: 8),
              IconButton.filled(
                tooltip: 'Enviar',
                onPressed: widget.sending ? null : _send,
                icon: widget.sending
                    ? const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.send),
              ),
            ],
          ),
        ),
      ),
    ],
  );
}
