import 'common.dart';

String contenidoVisibleMensajeIA(String content) => content
    .replaceAll(
      RegExp(
        r'^[ \t]*ID de recomendaci[oó]n:[ \t]*[0-9a-fA-F-]{36}[ \t]*(?:\r?\n|$)',
        multiLine: true,
        caseSensitive: false,
      ),
      '',
    )
    .trim();

class ElementoNotificacion {
  final String id;
  final String? projectId;
  final String title;
  final String body;
  final String severity;
  final DateTime occurredAt;
  final bool isRead;
  final Json deepLink;

  const ElementoNotificacion({
    required this.id,
    this.projectId,
    required this.title,
    required this.body,
    required this.severity,
    required this.occurredAt,
    required this.isRead,
    required this.deepLink,
  });

  factory ElementoNotificacion.fromJson(Json json) => ElementoNotificacion(
    id: json['id'].toString(),
    projectId: json['project_id']?.toString(),
    title: json['title']?.toString() ?? 'Notificacion',
    body: json['body']?.toString() ?? '',
    severity: json['severity']?.toString() ?? 'info',
    occurredAt: parseDate(json['occurred_at']),
    isRead: json['read_at'] != null,
    deepLink: (json['deep_link'] as Json?) ?? const {},
  );
}

class MensajeIA {
  final String id;
  final String role;
  final String content;
  final String? author;
  final int sequence;
  final DateTime createdAt;
  final String status;
  final bool proactive;

  const MensajeIA({
    required this.id,
    required this.role,
    required this.content,
    this.author,
    required this.sequence,
    required this.createdAt,
    this.status = 'completed',
    this.proactive = false,
  });

  factory MensajeIA.fromJson(Json json) => MensajeIA(
    id: json['id'].toString(),
    role: json['role']?.toString() ?? 'assistant',
    content: json['content']?.toString() ?? '',
    author: json['author_display_name']?.toString(),
    sequence: json['sequence_number'] as int? ?? 0,
    createdAt: parseDate(json['created_at']),
    status: json['status']?.toString() ?? 'completed',
    proactive:
        json['metadata_json'] is Json &&
        (json['metadata_json'] as Json)['kind'] == 'proactive',
  );
}

class AccionIA {
  final String id;
  final String sourceMessageId;
  final String actionType;
  final String status;
  final String riskLevel;
  final Json payload;
  final String? errorMessage;

  const AccionIA({
    required this.id,
    required this.sourceMessageId,
    required this.actionType,
    required this.status,
    required this.riskLevel,
    this.payload = const {},
    this.errorMessage,
  });

  factory AccionIA.fromJson(Json json) => AccionIA(
    id: json['id'].toString(),
    sourceMessageId: json['source_message_id']?.toString() ?? '',
    actionType: json['action_type']?.toString() ?? 'action',
    status: json['status']?.toString() ?? 'proposed',
    riskLevel: json['risk_level']?.toString() ?? 'medium',
    payload: json['payload'] is Json ? json['payload'] as Json : const {},
    errorMessage: json['error_message']?.toString(),
  );
}
