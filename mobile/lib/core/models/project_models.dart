import 'common.dart';

class ActivityItem {
  final String id;
  final String userName;
  final String type;
  final int sequence;
  final DateTime createdAt;

  const ActivityItem({
    required this.id,
    required this.userName,
    required this.type,
    required this.sequence,
    required this.createdAt,
  });

  factory ActivityItem.fromJson(Json json) => ActivityItem(
    id: json['id'].toString(),
    userName: json['user_name']?.toString() ?? 'Sistema',
    type: json['event_type']?.toString() ?? 'CAMBIO',
    sequence: json['sequence_number'] as int? ?? 0,
    createdAt: parseDate(json['created_at']),
  );
}

class VersionItem {
  final String id;
  final int number;
  final String name;
  final String? description;
  final String? createdBy;
  final DateTime createdAt;

  const VersionItem({
    required this.id,
    required this.number,
    required this.name,
    this.description,
    this.createdBy,
    required this.createdAt,
  });

  factory VersionItem.fromJson(Json json) => VersionItem(
    id: json['id'].toString(),
    number: json['version_number'] as int? ?? 0,
    name: json['name']?.toString() ?? 'Version',
    description: json['description']?.toString(),
    createdBy: json['created_by_name']?.toString(),
    createdAt: parseDate(json['created_at']),
  );
}

class GenerationItem {
  final String id;
  final String name;
  final String status;
  final String stage;
  final String? error;
  final DateTime updatedAt;

  const GenerationItem({
    required this.id,
    required this.name,
    required this.status,
    required this.stage,
    this.error,
    required this.updatedAt,
  });

  factory GenerationItem.fromJson(Json json) => GenerationItem(
    id: json['id'].toString(),
    name: json['name']?.toString() ?? 'Generacion',
    status: json['status']?.toString() ?? 'pending',
    stage: json['stage']?.toString() ?? '',
    error: json['error_detail']?.toString(),
    updatedAt: parseDate(json['updated_at']),
  );
}
