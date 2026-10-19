import 'package:uuid/uuid.dart';

import '../core/models/account_models.dart';
import '../core/models/common.dart';
import '../core/models/communication_models.dart';
import '../core/models/project_models.dart';
import '../core/models/uml_models.dart';
import '../core/network/api_client.dart';

class MobileRepository {
  final ApiClient api;
  const MobileRepository(this.api);

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

  Future<UserProfile> profile() async =>
      UserProfile.fromJson(await api.get('/auth/me') as Json);

  Future<List<ProjectSummary>> projects() async =>
      (await api.get('/mobile/projects') as List)
          .cast<Json>()
          .map(ProjectSummary.fromJson)
          .toList();

  Future<List<DiagramSummary>> diagrams(String projectId) async =>
      (await api.get('/mobile/projects/$projectId/diagrams') as List)
          .cast<Json>()
          .map(DiagramSummary.fromJson)
          .toList();

  Future<DiagramDetail> diagram(String diagramId) async =>
      DiagramDetail.fromJson(
        await api.get('/mobile/diagrams/$diagramId') as Json,
      );

  Future<List<ActivityItem>> activity(String projectId) async {
    final json =
        await api.get('/projects/$projectId/activity', query: {'limit': '50'})
            as Json;
    return jsonList(json['items']).map(ActivityItem.fromJson).toList();
  }

  Future<List<VersionItem>> versions(String projectId) async =>
      (await api.get('/projects/$projectId/versions') as List)
          .cast<Json>()
          .map(VersionItem.fromJson)
          .toList();

  Future<List<GenerationItem>> generations(String projectId) async =>
      (await api.get('/mobile/projects/$projectId/generations') as List)
          .cast<Json>()
          .map(GenerationItem.fromJson)
          .toList();

  Future<List<AiMessage>> messages(String projectId) async {
    final json =
        await api.get(
              '/projects/$projectId/ai/messages',
              query: {'limit': '60'},
            )
            as Json;
    return jsonList(json['items']).map(AiMessage.fromJson).toList();
  }

  Future<List<AiAction>> actions(String projectId) async =>
      (await api.get('/projects/$projectId/ai/actions', query: {'limit': '30'})
              as List)
          .cast<Json>()
          .map(AiAction.fromJson)
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

  Future<List<NotificationItem>> notifications({
    bool unreadOnly = false,
  }) async {
    final json =
        await api.get(
              '/notifications',
              query: {'limit': '60', 'unread_only': unreadOnly.toString()},
            )
            as Json;
    return jsonList(json['items']).map(NotificationItem.fromJson).toList();
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
