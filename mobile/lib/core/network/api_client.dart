import 'dart:convert';

import 'package:http/http.dart' as http;

import '../auth/session_store.dart';

class ApiException implements Exception {
  final int? statusCode;
  final String message;
  final bool isConnectivityFailure;

  const ApiException(
    this.message, {
    this.statusCode,
    this.isConnectivityFailure = false,
  });

  @override
  String toString() => message;
}

class ApiClient {
  final String baseUrl;
  final SessionStore sessionStore;
  final http.Client _client;

  ApiClient({
    required this.baseUrl,
    required this.sessionStore,
    http.Client? client,
  }) : _client = client ?? http.Client();

  Uri _uri(String path, [Map<String, String>? query]) {
    final normalized = path.startsWith('/') ? path : '/$path';
    return Uri.parse('$baseUrl$normalized').replace(queryParameters: query);
  }

  Future<Map<String, String>> _headers({bool authenticated = true}) async {
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (authenticated) {
      final token = await sessionStore.readToken();
      if (token != null) headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  Future<dynamic> get(String path, {Map<String, String>? query}) async {
    try {
      final response = await _client.get(
        _uri(path, query),
        headers: await _headers(),
      );
      return _decode(response);
    } on ApiException {
      rethrow;
    } catch (_) {
      throw const ApiException(
        'No se pudo alcanzar el backend.',
        isConnectivityFailure: true,
      );
    }
  }

  Future<dynamic> post(
    String path, {
    Object? body,
    bool authenticated = true,
  }) async {
    try {
      final response = await _client.post(
        _uri(path),
        headers: await _headers(authenticated: authenticated),
        body: jsonEncode(body ?? const <String, dynamic>{}),
      );
      return _decode(response);
    } on ApiException {
      rethrow;
    } catch (_) {
      throw const ApiException(
        'No se pudo alcanzar el backend.',
        isConnectivityFailure: true,
      );
    }
  }

  Future<dynamic> patch(String path, {Object? body}) async {
    try {
      final response = await _client.patch(
        _uri(path),
        headers: await _headers(),
        body: jsonEncode(body ?? const <String, dynamic>{}),
      );
      return _decode(response);
    } on ApiException {
      rethrow;
    } catch (_) {
      throw const ApiException(
        'No se pudo alcanzar el backend.',
        isConnectivityFailure: true,
      );
    }
  }

  dynamic _decode(http.Response response) {
    dynamic value;
    if (response.body.isNotEmpty) {
      try {
        value = jsonDecode(utf8.decode(response.bodyBytes));
      } on FormatException {
        value = response.body;
      }
    }
    if (response.statusCode == 401) {
      throw const ApiException('La sesion expiro.', statusCode: 401);
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = value is Map ? value['detail'] : null;
      final message = detail is Map
          ? (detail['message'] ?? detail['code'])?.toString()
          : detail?.toString();
      throw ApiException(
        message ?? 'La solicitud no pudo completarse.',
        statusCode: response.statusCode,
      );
    }
    return value;
  }
}
