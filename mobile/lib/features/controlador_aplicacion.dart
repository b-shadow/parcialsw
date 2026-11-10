import 'package:firebase_messaging/firebase_messaging.dart';
import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';

import '../core/auth/almacen_sesion.dart';
import '../core/cache/cache_privada.dart';
import '../core/models/modelos_cuenta.dart';
import '../core/models/common.dart';
import '../core/network/cliente_api.dart';
import 'repositorio_movil.dart';

class ControladorAplicacion extends ChangeNotifier {
  final RepositorioMovil repository;
  final AlmacenSesion sessionStore;
  final CachePrivada cache;
  StreamSubscription<List<ConnectivityResult>>? _connectivitySubscription;

  PerfilUsuario? profile;
  List<ResumenProyecto> projects = const [];
  bool restoring = true;
  bool loadingProjects = false;
  bool offline = false;
  int unreadCount = 0;
  String? error;

  ControladorAplicacion({
    required this.repository,
    required this.sessionStore,
    required this.cache,
  }) {
    _connectivitySubscription = Connectivity().onConnectivityChanged.listen((
      results,
    ) {
      final next = results.every((item) => item == ConnectivityResult.none);
      if (offline != next) {
        offline = next;
        notifyListeners();
      }
    });
  }

  bool get authenticated => profile != null;

  Future<void> restoreSession() async {
    restoring = true;
    try {
      final token = await sessionStore.readToken().timeout(
        const Duration(seconds: 5),
      );
      if (token != null) {
        profile = await repository.profile();
        await cache.write(profile!.id, 'profile', profile!.toJson());
        await refreshProjects();
        unawaited(syncMobileDeviceToken());
      }
    } on ExcepcionApi catch (exception) {
      if (exception.statusCode == 401) {
        await sessionStore.clear();
      } else {
        await _loadCachedProfile();
        await _loadCachedProjects();
      }
    } catch (exception) {
      debugPrint('No se pudo restaurar la sesion: $exception');
      error = 'No se pudo restaurar la sesion. Inicia sesion nuevamente.';
    } finally {
      restoring = false;
      notifyListeners();
    }
  }

  Future<void> login(String email, String password) async {
    error = null;
    try {
      final token = await repository.login(email, password);
      await sessionStore.save(token: token, userId: 'pending');
      profile = await repository.profile();
      await sessionStore.save(token: token, userId: profile!.id);
      await cache.write(profile!.id, 'profile', profile!.toJson());
      await refreshProjects();
      unawaited(syncMobileDeviceToken());
    } on ExcepcionApi catch (exception) {
      await sessionStore.clear();
      profile = null;
      error = exception.message;
      rethrow;
    } finally {
      notifyListeners();
    }
  }

  Future<void> refreshProjects() async {
    loadingProjects = true;
    error = null;
    notifyListeners();
    try {
      projects = await repository.projects();
      unreadCount = await repository.unreadCount();
      offline = false;
      if (profile != null) {
        await cache.write(
          profile!.id,
          'projects',
          projects.map((item) => item.toJson()).toList(),
        );
      }
    } on ExcepcionApi catch (exception) {
      error = exception.message;
      offline = exception.isConnectivityFailure || offline;
      await _loadCachedProjects();
      if (exception.statusCode == 401) await logout();
    } finally {
      loadingProjects = false;
      notifyListeners();
    }
  }

  Future<void> _loadCachedProjects() async {
    final userId = profile?.id ?? await sessionStore.readUserId();
    if (userId == null || userId == 'pending') return;
    final cached = await cache.read(userId, 'projects');
    final data = cached?['data'];
    if (data is List) {
      projects = data.whereType<Json>().map(ResumenProyecto.fromJson).toList();
      offline = true;
    }
  }

  Future<void> _loadCachedProfile() async {
    final userId = await sessionStore.readUserId();
    if (userId == null || userId == 'pending') return;
    final cached = await cache.read(userId, 'profile');
    final data = cached?['data'];
    if (data is Json) {
      profile = PerfilUsuario.fromJson(data);
      offline = true;
    }
  }

  Future<void> logout() async {
    final userId = profile?.id ?? await sessionStore.readUserId();
    await sessionStore.clear();
    if (userId != null && userId != 'pending') await cache.purgeUser(userId);
    profile = null;
    projects = const [];
    unreadCount = 0;
    error = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _connectivitySubscription?.cancel();
    super.dispose();
  }

  Future<void> syncMobileDeviceToken() async {
    try {
      final messaging = FirebaseMessaging.instance;
      final settings = await messaging.requestPermission(
        alert: true,
        badge: true,
        sound: true,
      );
      if (settings.authorizationStatus == AuthorizationStatus.authorized ||
          settings.authorizationStatus == AuthorizationStatus.provisional) {
        final registration = messaging.onRegistered.first.timeout(
          const Duration(seconds: 10),
        );
        await messaging.register();
        final token = await registration;
        if (authenticated) {
          await repository.registerMobileDevice(token);
        }
      }
    } catch (_) {
      // Ignora en entornos sin Firebase configurado o pruebas
    }
  }
}
