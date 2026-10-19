import 'common.dart';

class NotificationItem {
  final String id;
  final String? projectId;
  final String title;
  final String body;
  final String severity;
  final DateTime occurredAt;
  final bool isRead;
  final Json deepLink;

  const NotificationItem({
    required this.id,
    this.projectId,
    required this.title,
    required this.body,
    required this.severity,
    required this.occurredAt,
    required this.isRead,
    required this.deepLink,
  });

  factory NotificationItem.fromJson(Json json) => NotificationItem(
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

class AiMessage {
  final String id;
  final String role;
  final String content;
  final String? author;
  final int sequence;
  final DateTime createdAt;

  const AiMessage({
    required this.id,
    required this.role,
    required this.content,
    this.author,
    required this.sequence,
    required this.createdAt,
  });

  factory AiMessage.fromJson(Json json) => AiMessage(
    id: json['id'].toString(),
    role: json['role']?.toString() ?? 'assistant',
    content: json['content']?.toString() ?? '',
    author: json['author_display_name']?.toString(),
    sequence: json['sequence_number'] as int? ?? 0,
    createdAt: parseDate(json['created_at']),
  );
}

class AiAction {
  final String id;
  final String actionType;
  final String status;
  final String riskLevel;

  const AiAction({
    required this.id,
    required this.actionType,
    required this.status,
    required this.riskLevel,
  });

  factory AiAction.fromJson(Json json) => AiAction(
    id: json['id'].toString(),
    actionType: json['action_type']?.toString() ?? 'action',
    status: json['status']?.toString() ?? 'proposed',
    riskLevel: json['risk_level']?.toString() ?? 'medium',
  );
}
