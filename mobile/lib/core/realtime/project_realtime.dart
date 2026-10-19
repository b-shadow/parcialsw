import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/io.dart';
import 'package:web_socket_channel/status.dart' as ws_status;

import '../auth/session_store.dart';

enum RealtimeState { disconnected, connecting, connected, reconnecting }

class ProjectRealtime extends ChangeNotifier {
  final String apiBaseUrl;
  final SessionStore sessionStore;
  final _events = StreamController<Map<String, dynamic>>.broadcast();
  final _seenIds = <String>{};
  IOWebSocketChannel? _channel;
  StreamSubscription? _subscription;
  Timer? _retryTimer;
  Timer? _pingTimer;
  String? _projectId;
  bool _closedByUser = false;
  bool _disposed = false;
  int _attempt = 0;
  RealtimeState state = RealtimeState.disconnected;

  ProjectRealtime({required this.apiBaseUrl, required this.sessionStore});

  Stream<Map<String, dynamic>> get events => _events.stream;

  Uri _socketUri(String projectId) {
    final apiUri = Uri.parse(apiBaseUrl);
    final path = apiUri.path.replaceFirst(RegExp(r'/api/v1/?$'), '');
    return apiUri.replace(
      scheme: apiUri.scheme == 'https' ? 'wss' : 'ws',
      path: '$path/api/v1/ws/projects/$projectId',
      query: null,
    );
  }

  Future<void> connect(String projectId) async {
    if (_projectId == projectId && state == RealtimeState.connected) return;
    await disconnect();
    _closedByUser = false;
    _projectId = projectId;
    await _open();
  }

  Future<void> _open() async {
    final projectId = _projectId;
    final token = await sessionStore.readToken();
    if (projectId == null || token == null || _closedByUser) return;
    state = _attempt == 0
        ? RealtimeState.connecting
        : RealtimeState.reconnecting;
    if (!_disposed) notifyListeners();
    try {
      _channel = IOWebSocketChannel.connect(
        _socketUri(projectId),
        protocols: ['case-v1', 'case-auth.$token'],
        pingInterval: const Duration(seconds: 20),
      );
      await _channel!.ready;
      _attempt = 0;
      state = RealtimeState.connected;
      if (!_disposed) notifyListeners();
      _subscription = _channel!.stream.listen(
        _onMessage,
        onError: (_) => _scheduleReconnect(),
        onDone: _scheduleReconnect,
        cancelOnError: true,
      );
      _pingTimer = Timer.periodic(const Duration(seconds: 25), (_) {
        _channel?.sink.add(jsonEncode({'type': 'PING'}));
      });
    } catch (_) {
      _scheduleReconnect();
    }
  }

  void _onMessage(dynamic raw) {
    try {
      final event = jsonDecode(raw.toString()) as Map<String, dynamic>;
      final eventId = event['event_id']?.toString();
      if (eventId != null && !_seenIds.add(eventId)) return;
      if (_seenIds.length > 500) _seenIds.remove(_seenIds.first);
      _events.add(event);
    } on FormatException {
      return;
    }
  }

  void _scheduleReconnect() {
    if (_closedByUser || _retryTimer?.isActive == true) return;
    _pingTimer?.cancel();
    state = RealtimeState.reconnecting;
    if (!_disposed) notifyListeners();
    _attempt = (_attempt + 1).clamp(1, 6).toInt();
    final seconds = 1 << (_attempt - 1);
    _retryTimer = Timer(Duration(seconds: seconds), _open);
  }

  Future<void> disconnect() async {
    _closedByUser = true;
    _retryTimer?.cancel();
    _pingTimer?.cancel();
    await _subscription?.cancel();
    await _channel?.sink.close(ws_status.normalClosure);
    _channel = null;
    state = RealtimeState.disconnected;
    if (!_disposed) notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    _closedByUser = true;
    _retryTimer?.cancel();
    _pingTimer?.cancel();
    _subscription?.cancel();
    _channel?.sink.close(ws_status.normalClosure);
    _events.close();
    super.dispose();
  }
}
