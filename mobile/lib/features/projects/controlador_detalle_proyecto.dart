import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../core/models/modelos_cuenta.dart';
import '../../core/models/modelos_comunicacion.dart';
import '../../core/models/modelos_proyecto.dart';
import '../../core/models/modelos_uml.dart';
import '../../core/network/cliente_api.dart';
import '../../core/realtime/tiempo_real_proyecto.dart';
import '../controlador_aplicacion.dart';

class ControladorDetalleProyecto extends ChangeNotifier {
  final ControladorAplicacion app;
  final ResumenProyecto project;
  late final TiempoRealProyecto realtime;
  StreamSubscription<Map<String, dynamic>>? _events;
  Timer? _refreshDebounce;
  bool _disposed = false;

  List<ResumenDiagrama> diagrams = const [];
  List<ElementoActividad> activity = const [];
  List<ElementoVersion> versions = const [];
  List<ElementoGeneracion> generations = const [];
  List<MensajeIA> messages = const [];
  List<AccionIA> actions = const [];
  bool loading = true;
  bool sendingMessage = false;
  String? pendingMessage;
  bool versionsRestricted = false;
  String? error;

  ControladorDetalleProyecto({required this.app, required this.project}) {
    realtime = TiempoRealProyecto(
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
      diagrams = results[0] as List<ResumenDiagrama>;
      activity = results[1] as List<ElementoActividad>;
      generations = results[2] as List<ElementoGeneracion>;
      messages = results[3] as List<MensajeIA>;
      actions = results[4] as List<AccionIA>;
      await _loadVersions();
    } on ExcepcionApi catch (exception) {
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
    } on ExcepcionApi catch (exception) {
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
    pendingMessage = content.trim();
    notifyListeners();
    try {
      final response = await app.repository.sendMessage(
        project.id,
        content,
        diagramId: diagramId,
      );
      List<MensajeIA> updated;
      try {
        updated = await app.repository.messages(project.id);
      } on ExcepcionApi {
        // La respuesta ya llegó: conservarla hasta que se recupere el historial.
        updated = messages;
      }
      final answer = response['answer']?.toString().trim() ?? '';
      final responseId = response['message_id']?.toString();
      final responseSequence = response['conversation_sequence'] as int?;
      if (answer.isNotEmpty && responseId != null &&
          !updated.any((message) => message.id == responseId)) {
        final questionSequence = (responseSequence ??
            (updated.isEmpty ? 2 : updated.last.sequence + 2)) - 1;
        messages = [
          ...updated,
          if (!updated.any((message) => message.role == 'user' &&
              message.sequence == questionSequence))
            MensajeIA(
              id: 'local-user-$responseId',
              role: 'user',
              content: content.trim(),
              sequence: questionSequence,
              createdAt: DateTime.now(),
            ),
          MensajeIA(
            id: responseId,
            role: 'assistant',
            content: answer,
            sequence: responseSequence ?? questionSequence + 1,
            createdAt: DateTime.now(),
          ),
        ]..sort((a, b) => a.sequence.compareTo(b.sequence));
      } else {
        messages = updated;
      }
      try {
        actions = await app.repository.actions(project.id);
      } on ExcepcionApi {
        // Las acciones se recuperarán con la siguiente actualización.
      }
    } catch (_) {
      // El servidor puede haber guardado la pregunta antes de devolver un error.
      try {
        messages = await app.repository.messages(project.id);
      } catch (_) {}
      rethrow;
    } finally {
      sendingMessage = false;
      pendingMessage = null;
      if (!_disposed) notifyListeners();
    }
  }

  Future<void> _refreshAssistant() async {
    if (_disposed) return;
    try {
      messages = await app.repository.messages(project.id);
      actions = await app.repository.actions(project.id);
      if (!_disposed) notifyListeners();
    } on ExcepcionApi {
      // La siguiente actualización o recarga puede recuperar el historial.
    }
  }

  void _handleEvent(Map<String, dynamic> event) {
    if (_disposed) return;
    const relevant = {
      'PROJECT_VERSION_CREATED',
      'PROJECT_VERSION_RESTORED',
      'PROJECT_STATE_INVALIDATED',
      'AI_MESSAGE_CREATED',
      'AI_MESSAGE_STATUS_CHANGED',
      'AI_PROCESSING_FINISHED',
      'AI_PROCESSING_FAILED',
      'AI_ACTION_STATUS_CHANGED',
      'GENERATION_COMPLETED',
      'UML_CLASS_CREATED',
      'UML_CLASS_UPDATED',
      'UML_RELATIONSHIP_CREATED',
    };
    if (!relevant.contains(event['type'])) return;
    _refreshDebounce?.cancel();
    final assistantEvent = event['type'].toString().startsWith('AI_');
    _refreshDebounce = Timer(
      const Duration(milliseconds: 500),
      assistantEvent ? _refreshAssistant : refresh,
    );
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
