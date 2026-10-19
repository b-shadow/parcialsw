import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../core/models/account_models.dart';
import '../../core/models/communication_models.dart';
import '../../core/models/project_models.dart';
import '../../core/models/uml_models.dart';
import '../../core/network/api_client.dart';
import '../../core/realtime/project_realtime.dart';
import '../app_controller.dart';

class ProjectDetailController extends ChangeNotifier {
  final AppController app;
  final ProjectSummary project;
  late final ProjectRealtime realtime;
  StreamSubscription<Map<String, dynamic>>? _events;
  Timer? _refreshDebounce;
  bool _disposed = false;

  List<DiagramSummary> diagrams = const [];
  List<ActivityItem> activity = const [];
  List<VersionItem> versions = const [];
  List<GenerationItem> generations = const [];
  List<AiMessage> messages = const [];
  List<AiAction> actions = const [];
  bool loading = true;
  bool sendingMessage = false;
  bool versionsRestricted = false;
  String? error;

  ProjectDetailController({required this.app, required this.project}) {
    realtime = ProjectRealtime(
      apiBaseUrl: app.repository.api.baseUrl,
      sessionStore: app.sessionStore,
    )..addListener(_onRealtimeChanged);
  }

  void _onRealtimeChanged() {
    if (!_disposed) notifyListeners();
  }

  Future<void> initialize() async {
    _events = realtime.events.listen(_handleEvent);
    await realtime.connect(project.id);
    if (_disposed) return;
    await refresh();
  }

  Future<void> refresh() async {
    if (_disposed) return;
    loading = true;
    error = null;
    notifyListeners();
    try {
      final results = await Future.wait<dynamic>([
        app.repository.diagrams(project.id),
        app.repository.activity(project.id),
        app.repository.generations(project.id),
        app.repository.messages(project.id),
        app.repository.actions(project.id),
      ]);
      diagrams = results[0] as List<DiagramSummary>;
      activity = results[1] as List<ActivityItem>;
      generations = results[2] as List<GenerationItem>;
      messages = results[3] as List<AiMessage>;
      actions = results[4] as List<AiAction>;
      await _loadVersions();
    } on ApiException catch (exception) {
      error = exception.message;
    } finally {
      loading = false;
      if (!_disposed) notifyListeners();
    }
  }

  Future<void> _loadVersions() async {
    try {
      versions = await app.repository.versions(project.id);
      versionsRestricted = false;
    } on ApiException catch (exception) {
      if (exception.statusCode == 403) {
        versions = const [];
        versionsRestricted = true;
        return;
      }
      rethrow;
    }
  }

  Future<void> sendMessage(String content, {String? diagramId}) async {
    if (_disposed || content.trim().isEmpty || sendingMessage) return;
    sendingMessage = true;
    notifyListeners();
    try {
      await app.repository.sendMessage(
        project.id,
        content,
        diagramId: diagramId,
      );
      messages = await app.repository.messages(project.id);
      actions = await app.repository.actions(project.id);
    } finally {
      sendingMessage = false;
      if (!_disposed) notifyListeners();
    }
  }

  void _handleEvent(Map<String, dynamic> event) {
    if (_disposed) return;
    const relevant = {
      'PROJECT_VERSION_CREATED',
      'PROJECT_VERSION_RESTORED',
      'PROJECT_STATE_INVALIDATED',
      'AI_MESSAGE_COMPLETED',
      'AI_ACTION_STATUS_CHANGED',
      'GENERATION_COMPLETED',
      'UML_CLASS_CREATED',
      'UML_CLASS_UPDATED',
      'UML_RELATIONSHIP_CREATED',
    };
    if (!relevant.contains(event['type'])) return;
    _refreshDebounce?.cancel();
    _refreshDebounce = Timer(const Duration(milliseconds: 500), refresh);
  }

  @override
  void dispose() {
    _disposed = true;
    _refreshDebounce?.cancel();
    _events?.cancel();
    realtime.removeListener(_onRealtimeChanged);
    realtime.dispose();
    super.dispose();
  }
}
