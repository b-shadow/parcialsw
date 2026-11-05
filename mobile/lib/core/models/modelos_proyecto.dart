import 'common.dart';

class ElementoActividad {
  final String id;
  final String userName;
  final String type;
  final int sequence;
  final DateTime createdAt;

  const ElementoActividad({
    required this.id,
    required this.userName,
    required this.type,
    required this.sequence,
    required this.createdAt,
  });

  factory ElementoActividad.fromJson(Json json) => ElementoActividad(
    id: json['id'].toString(),
    userName: json['user_name']?.toString() ?? 'Sistema',
    type: json['event_type']?.toString() ?? 'CAMBIO',
    sequence: json['sequence_number'] as int? ?? 0,
    createdAt: parseDate(json['created_at']),
  );
}

class ElementoVersion {
  final String id;
  final int number;
  final String name;
  final String? description;
  final String? createdBy;
  final DateTime createdAt;

  const ElementoVersion({
    required this.id,
    required this.number,
    required this.name,
    this.description,
    this.createdBy,
    required this.createdAt,
  });

  factory ElementoVersion.fromJson(Json json) => ElementoVersion(
    id: json['id'].toString(),
    number: json['version_number'] as int? ?? 0,
    name: json['name']?.toString() ?? 'Version',
    description: json['description']?.toString(),
    createdBy: json['created_by_name']?.toString(),
    createdAt: parseDate(json['created_at']),
  );
}

class ElementoGeneracion {
  final String id;
  final String name;
  final String status;
  final String stage;
  final String? error;
  final DateTime updatedAt;

  const ElementoGeneracion({
    required this.id,
    required this.name,
    required this.status,
    required this.stage,
    this.error,
    required this.updatedAt,
  });

  factory ElementoGeneracion.fromJson(Json json) => ElementoGeneracion(
    id: json['id'].toString(),
    name: json['name']?.toString() ?? 'Generacion',
    status: json['status']?.toString() ?? 'pending',
    stage: json['stage']?.toString() ?? '',
    error: json['error_detail']?.toString(),
    updatedAt: parseDate(json['updated_at']),
  );
}
