import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class PrivateCache {
  String _key(String userId, String resource) => 'case:$userId:$resource';

  Future<void> write(String userId, String resource, Object value) async {
    final preferences = await SharedPreferences.getInstance();
    await preferences.setString(
      _key(userId, resource),
      jsonEncode({
        'cached_at': DateTime.now().toUtc().toIso8601String(),
        'data': value,
      }),
    );
  }

  Future<Map<String, dynamic>?> read(String userId, String resource) async {
    final preferences = await SharedPreferences.getInstance();
    final raw = preferences.getString(_key(userId, resource));
    if (raw == null) return null;
    try {
      return jsonDecode(raw) as Map<String, dynamic>;
    } on FormatException {
      await preferences.remove(_key(userId, resource));
      return null;
    }
  }

  Future<void> purgeUser(String userId) async {
    final preferences = await SharedPreferences.getInstance();
    final prefix = 'case:$userId:';
    final keys = preferences.getKeys().where((key) => key.startsWith(prefix));
    for (final key in keys.toList()) {
      await preferences.remove(key);
    }
  }
}
