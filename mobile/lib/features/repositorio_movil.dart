import 'package:uuid/uuid.dart';

import '../core/models/modelos_cuenta.dart';
import '../core/models/common.dart';
import '../core/models/modelos_comunicacion.dart';
import '../core/models/modelos_proyecto.dart';
import '../core/models/modelos_uml.dart';
import '../core/network/cliente_api.dart';

class RepositorioMovil {
  final ClienteApi api;
  const RepositorioMovil(this.api);

  Future<String> login(String email, String password) async {
    final json =
        await api.post(
              '/auth/login',
              authenticated: false,
              body: {'email': email.trim(), 'password': password},
            )
            as Json;
    return json['access_token'].toString();
  }

  Future<PerfilUsuario> profile() async =>
      PerfilUsuario.fromJson(await api.get('/auth/me') as Json);

  Future<List<ResumenProyecto>> projects() async =>
      (await api.get('/mobile/projects') as List)
          .cast<Json>()
          .map(ResumenProyecto.fromJson)
          .toList();

  Future<List<ResumenDiagrama>> diagrams(String projectId) async =>
      (await api.get('/mobile/projects/$projectId/diagrams') as List)
          .cast<Json>()
          .map(ResumenDiagrama.fromJson)
          .toList();

  Future<DetalleDiagrama> diagram(String diagramId) async =>
      DetalleDiagrama.fromJson(
        await api.get('/mobile/diagrams/$diagramId') as Json,
      );

  Future<List<ElementoActividad>> activity(String projectId) async {
    final json =
        await api.get('/projects/$projectId/activity', query: {'limit': '50'})
            as Json;
    return jsonList(json['items']).map(ElementoActividad.fromJson).toList();
  }

  Future<List<ElementoVersion>> versions(String projectId) async =>
      (await api.get('/projects/$projectId/versions') as List)
          .cast<Json>()
          .map(ElementoVersion.fromJson)
          .toList();

  Future<List<ElementoGeneracion>> generations(String projectId) async =>
      (await api.get('/mobile/projects/$projectId/generations') as List)
          .cast<Json>()
          .map(ElementoGeneracion.fromJson)
          .toList();

  Future<List<MensajeIA>> messages(String projectId) async {
    final json =
        await api.get(
              '/projects/$projectId/ai/messages',
              query: {'limit': '60'},
            )
            as Json;
    return jsonList(json['items']).map(MensajeIA.fromJson).toList();
  }

  Future<List<AccionIA>> actions(String projectId) async =>
      (await api.get('/projects/$projectId/ai/actions', query: {'limit': '30'})
              as List)
          .cast<Json>()
          .map(AccionIA.fromJson)
          .toList();

  Future<void> sendMessage(
    String projectId,
    String content, {
    String? diagramId,
  }) async {
    await api.post(
      '/projects/$projectId/ai/interactions',
      body: {
        'client_message_id': const Uuid().v4(),
        'content': content.trim(),
        'diagram_id': diagramId,
        'requested_context': {
          'include_diagram': diagramId != null,
          'include_recent_messages': true,
          'include_project_versions': false,
          'surface': 'mobile_readonly',
        },
      },
    );
  }

  Future<List<ElementoNotificacion>> notifications({
    bool unreadOnly = false,
  }) async {
    final json =
        await api.get(
              '/notifications',
              query: {'limit': '60', 'unread_only': unreadOnly.toString()},
            )
            as Json;
    return jsonList(json['items']).map(ElementoNotificacion.fromJson).toList();
  }

  Future<int> unreadCount() async {
    final json = await api.get('/notifications/unread-count') as Json;
    return json['count'] as int? ?? 0;
  }

  Future<void> markNotificationRead(String id, {bool clicked = false}) async {
    await api.post('/notifications/$id/${clicked ? 'clicked' : 'read'}');
  }

  Future<void> changePassword(
    String currentPassword,
    String newPassword,
  ) async {
    await api.patch(
      '/users/me/password',
      body: {'current_password': currentPassword, 'new_password': newPassword},
    );
  }
}
