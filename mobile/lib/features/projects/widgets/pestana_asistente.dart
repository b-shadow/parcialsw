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
    final chatMessages =
        widget.messages.where((message) => !message.proactive).toList()
          ..sort((a, b) => a.sequence.compareTo(b.sequence));
    final actionsByMessage = <String, List<AccionIA>>{};
    for (final action in widget.actions) {
      (actionsByMessage[action.sourceMessageId] ??= []).add(action);
    }
    for (final actions in actionsByMessage.values) {
      actions.sort((a, b) {
        final aOrder =
            (a.payload['_plan'] is Map
                    ? (a.payload['_plan'] as Map)['order']
                    : null)
                as int? ??
            0;
        final bOrder =
            (b.payload['_plan'] is Map
                    ? (b.payload['_plan'] as Map)['order']
                    : null)
                as int? ??
            0;
        return aOrder.compareTo(bOrder);
      });
    }
    final notices = <String>{};
    for (final message in widget.messages.where(
      (message) => message.proactive,
    )) {
      notices.add(message.content);
    }
    final pendingVisible =
        widget.pendingMessage != null &&
        !chatMessages.any(
          (message) =>
              message.role == 'user' &&
              message.content == widget.pendingMessage,
        );
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
        if (notices.isNotEmpty)
          ExpansionTile(
            title: Text('Avisos automáticos de la IA (${notices.length})'),
            children: notices
                .take(3)
                .map(
                  (notice) => Padding(
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                    child: Align(
                      alignment: Alignment.centerLeft,
                      child: Text(notice),
                    ),
                  ),
                )
                .toList(),
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
                  itemCount:
                      chatMessages.length +
                      (pendingVisible ? 1 : 0) +
                      (widget.sending ? 1 : 0),
                  itemBuilder: (context, reverseIndex) {
                    final index =
                        chatMessages.length +
                        (pendingVisible ? 1 : 0) +
                        (widget.sending ? 1 : 0) -
                        1 -
                        reverseIndex;
                    if (widget.sending &&
                        index ==
                            chatMessages.length + (pendingVisible ? 1 : 0)) {
                      return const Padding(
                        padding: EdgeInsets.only(bottom: 9),
                        child: Align(
                          alignment: Alignment.centerLeft,
                          child: Text('El asistente está analizando...'),
                        ),
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
                          child: Text(
                            contenidoVisibleMensajeIA(widget.pendingMessage!),
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.onPrimary,
                            ),
                          ),
                        ),
                      );
                    }
                    final message = chatMessages[index];
                    final user = message.role == 'user';
                    return Column(
                      crossAxisAlignment: user
                          ? CrossAxisAlignment.end
                          : CrossAxisAlignment.start,
                      children: [
                        Container(
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
                              Text(
                                contenidoVisibleMensajeIA(message.content),
                                style: TextStyle(
                                  color: user
                                      ? Theme.of(context).colorScheme.onPrimary
                                      : null,
                                ),
                              ),
                              if (message.status == 'failed')
                                const Padding(
                                  padding: EdgeInsets.only(top: 6),
                                  child: Text(
                                    'No se pudo procesar. Inténtalo de nuevo.',
                                  ),
                                ),
                              if (message.status == 'pending' ||
                                  message.status == 'streaming')
                                const Padding(
                                  padding: EdgeInsets.only(top: 6),
                                  child: Text('Procesando...'),
                                ),
                            ],
                          ),
                        ),
                        if (!user)
                          ...(actionsByMessage[message.id] ??
                                  const <AccionIA>[])
                              .map((action) => _TarjetaAccion(action: action)),
                      ],
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

class _TarjetaAccion extends StatelessWidget {
  final AccionIA action;
  const _TarjetaAccion({required this.action});

  @override
  Widget build(BuildContext context) {
    final applied = action.status == 'applied';
    final colorScheme = Theme.of(context).colorScheme;
    final plan = action.payload['_plan'];
    final explanation = plan is Map ? plan['explanation']?.toString() : null;
    final name = action.payload['name']?.toString();
    final dataType = action.payload['data_type']?.toString();
    final className = action.payload['class_name']?.toString();
    final detail = explanation != null && explanation.trim().isNotEmpty
        ? explanation
        : action.actionType == 'create_attribute' && name != null
        ? 'Agregar $name${dataType == null ? '' : ': $dataType'}'
              '${className == null ? '' : ' a $className'}.'
        : action.actionType.replaceAll('_', ' ');
    final title = switch (action.actionType) {
      'create_attribute' => 'Agregar atributo',
      'update_attribute' => 'Editar atributo',
      'delete_attribute' => 'Eliminar atributo',
      'create_class' => 'Crear clase',
      'update_class' => 'Editar clase',
      'create_relationship' => 'Crear relación',
      _ => 'Cambio UML',
    };
    final statusText = switch (action.status) {
      'applied' => 'Aplicado al diagrama',
      'proposed' => 'Propuesta pendiente',
      'rejected' => 'Rechazado',
      'failed' => 'No se pudo aplicar',
      _ => 'En proceso',
    };
    return Container(
      width: 340,
      margin: const EdgeInsets.only(bottom: 9),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: applied ? colorScheme.primaryContainer : colorScheme.surface,
        border: Border.all(
          color: applied ? colorScheme.primary : colorScheme.outlineVariant,
        ),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
          const SizedBox(height: 4),
          Text(detail),
          const SizedBox(height: 4),
          Text(
            statusText,
            style: TextStyle(
              color: applied
                  ? colorScheme.primary
                  : colorScheme.onSurfaceVariant,
              fontWeight: FontWeight.w600,
            ),
          ),
          if (action.status == 'proposed')
            const Text('Revisar y confirmar desde escritorio.'),
          if (action.status == 'failed' && action.errorMessage != null)
            Text(action.errorMessage!),
        ],
      ),
    );
  }
}
