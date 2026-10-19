import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';

import '../core/auth/session_store.dart';
import '../core/cache/private_cache.dart';
import '../core/models/account_models.dart';
import '../core/models/common.dart';
import '../core/network/api_client.dart';
import 'mobile_repository.dart';

class AppController extends ChangeNotifier {
  final MobileRepository repository;
  final SessionStore sessionStore;
  final PrivateCache cache;
  StreamSubscription<List<ConnectivityResult>>? _connectivitySubscription;

  UserProfile? profile;
  List<ProjectSummary> projects = const [];
  bool restoring = true;
  bool loadingProjects = false;
  bool offline = false;
  int unreadCount = 0;
  String? error;

  AppController({
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
    final token = await sessionStore.readToken();
    if (token != null) {
      try {
        profile = await repository.profile();
        await cache.write(profile!.id, 'profile', profile!.toJson());
        await refreshProjects();
      } on ApiException catch (exception) {
        if (exception.statusCode == 401) {
          await sessionStore.clear();
        } else {
          await _loadCachedProfile();
          await _loadCachedProjects();
        }
      }
    }
    restoring = false;
    notifyListeners();
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
    } on ApiException catch (exception) {
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
    } on ApiException catch (exception) {
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
      projects = data.whereType<Json>().map(ProjectSummary.fromJson).toList();
      offline = true;
    }
  }

  Future<void> _loadCachedProfile() async {
    final userId = await sessionStore.readUserId();
    if (userId == null || userId == 'pending') return;
    final cached = await cache.read(userId, 'profile');
    final data = cached?['data'];
    if (data is Json) {
      profile = UserProfile.fromJson(data);
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
}
