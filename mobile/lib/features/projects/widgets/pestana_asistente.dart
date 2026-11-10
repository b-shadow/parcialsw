import 'package:flutter/material.dart';

import '../../../core/models/modelos_comunicacion.dart';
import '../../../core/models/modelos_uml.dart';
import '../../../core/network/cliente_api.dart';
import '../../../shared/widgets/estados_contenido.dart';

class PestanaAsistente extends StatefulWidget {
  final List<MensajeIA> messages;
  final List<AccionIA> actions;
  final List<ResumenDiagrama> diagrams;
  final bool sending;
  final String? pendingMessage;
  final Future<void> Function(String content, {String? diagramId}) onSend;
  const PestanaAsistente({
    super.key,
    required this.messages,
    required this.actions,
    required this.diagrams,
    required this.sending,
    this.pendingMessage,
    required this.onSend,
  });

  @override
  State<PestanaAsistente> createState() => _EstadoPestanaAsistente();
}

class _EstadoPestanaAsistente extends State<PestanaAsistente> {
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
    } on ExcepcionApi catch (exception) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(exception.message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final chatMessages = widget.messages.where((message) => !message.proactive).toList()
      ..sort((a, b) => a.sequence.compareTo(b.sequence));
    final notices = <String>{};
    for (final message in widget.messages.where((message) => message.proactive)) {
      notices.add(message.content);
    }
    final pendingVisible = widget.pendingMessage != null &&
        !chatMessages.any((message) => message.role == 'user' &&
            message.content == widget.pendingMessage);
    return Column(
    children: [
      Container(
        width: double.infinity,
        color: Theme.of(context).colorScheme.tertiaryContainer,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
        child: Text(
          'Consulta y recomendaciones. Las acciones que modifican UML se confirman en escritorio.',
          style: TextStyle(
            fontSize: 12,
            color: Theme.of(context).colorScheme.onTertiaryContainer,
          ),
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
            color: Theme.of(context).colorScheme.primaryContainer,
            borderRadius: BorderRadius.circular(6),
            border: Border.all(
              color: Theme.of(context).colorScheme.outlineVariant,
            ),
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
      if (notices.isNotEmpty)
        ExpansionTile(
          title: Text('Avisos automáticos de la IA (${notices.length})'),
          children: notices.take(3).map((notice) => Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
            child: Align(alignment: Alignment.centerLeft, child: Text(notice)),
          )).toList(),
        ),
      Expanded(
        child: chatMessages.isEmpty && !pendingVisible
            ? const EstadoVacio(
                icon: Icons.auto_awesome_outlined,
                title: 'Asistente del proyecto',
                message:
                    'Pregunta por el modelo, decisiones o recomendaciones.',
              )
            : ListView.builder(
                reverse: true,
                padding: const EdgeInsets.all(14),
                itemCount: chatMessages.length + (pendingVisible ? 1 : 0) +
                    (widget.sending ? 1 : 0),
                itemBuilder: (context, reverseIndex) {
                  final index = chatMessages.length + (pendingVisible ? 1 : 0) +
                      (widget.sending ? 1 : 0) - 1 - reverseIndex;
                  if (widget.sending && index == chatMessages.length +
                      (pendingVisible ? 1 : 0)) {
                    return const Padding(
                      padding: EdgeInsets.only(bottom: 9),
                      child: Align(alignment: Alignment.centerLeft,
                        child: Text('El asistente está analizando...')),
                    );
                  }
                  if (pendingVisible && index == chatMessages.length) {
                    return Align(
                      alignment: Alignment.centerRight,
                      child: Container(
                        constraints: const BoxConstraints(maxWidth: 340),
                        margin: const EdgeInsets.only(bottom: 9),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Theme.of(context).colorScheme.primary,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(widget.pendingMessage!, style: TextStyle(
                          color: Theme.of(context).colorScheme.onPrimary,
                        )),
                      ),
                    );
                  }
                  final message = chatMessages[index];
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
                        color: user
                            ? Theme.of(context).colorScheme.primary
                            : Theme.of(context).colorScheme.surface,
                        borderRadius: BorderRadius.circular(8),
                        border: user
                            ? null
                            : Border.all(
                                color: Theme.of(
                                  context,
                                ).colorScheme.outlineVariant,
                              ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(message.content, style: TextStyle(
                            color: user ? Theme.of(context).colorScheme.onPrimary : null,
                          )),
                          if (message.status == 'failed')
                            const Padding(
                              padding: EdgeInsets.only(top: 6),
                              child: Text('No se pudo procesar. Inténtalo de nuevo.'),
                            ),
                          if (message.status == 'pending' || message.status == 'streaming')
                            const Padding(
                              padding: EdgeInsets.only(top: 6),
                              child: Text('Procesando...'),
                            ),
                        ],
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
}
