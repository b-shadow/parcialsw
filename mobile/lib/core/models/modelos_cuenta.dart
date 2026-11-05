import 'common.dart';

class PerfilUsuario {
  final String id;
  final String fullName;
  final String email;
  final List<String> roles;

  const PerfilUsuario({
    required this.id,
    required this.fullName,
    required this.email,
    required this.roles,
  });

  factory PerfilUsuario.fromJson(Json json) => PerfilUsuario(
    id: json['id'].toString(),
    fullName: json['full_name']?.toString() ?? '',
    email: json['email']?.toString() ?? '',
    roles: (json['role_names'] as List? ?? const <Object>[])
        .map((item) => item.toString())
        .toList(),
  );

  Json toJson() => {
    'id': id,
    'full_name': fullName,
    'email': email,
    'role_names': roles,
  };
}

class ResumenProyecto {
  final String id;
  final String name;
  final String? description;
  final String role;
  final String status;
  final int diagramCount;
  final int memberCount;
  final int unreadCount;
  final DateTime updatedAt;

  const ResumenProyecto({
    required this.id,
    required this.name,
    this.description,
    required this.role,
    required this.status,
    required this.diagramCount,
    required this.memberCount,
    required this.unreadCount,
    required this.updatedAt,
  });

  factory ResumenProyecto.fromJson(Json json) => ResumenProyecto(
    id: json['id'].toString(),
    name: json['name']?.toString() ?? 'Proyecto',
    description: json['description']?.toString(),
    role: json['project_role']?.toString() ?? 'EDITOR',
    status: json['status']?.toString() ?? 'active',
    diagramCount: json['diagram_count'] as int? ?? 0,
    memberCount: json['member_count'] as int? ?? 0,
    unreadCount: json['unread_notification_count'] as int? ?? 0,
    updatedAt: parseDate(json['updated_at']),
  );

  Json toJson() => {
    'id': id,
    'name': name,
    'description': description,
    'project_role': role,
    'status': status,
    'diagram_count': diagramCount,
    'member_count': memberCount,
    'unread_notification_count': unreadCount,
    'updated_at': updatedAt.toUtc().toIso8601String(),
  };
}
