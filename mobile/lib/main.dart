import 'dart:async';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';

import 'app/aplicacion.dart';
import 'core/auth/almacen_sesion.dart';
import 'core/cache/cache_privada.dart';
import 'core/network/cliente_api.dart';
import 'features/controlador_aplicacion.dart';
import 'features/repositorio_movil.dart';
import 'firebase_options.dart';

@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  try {
    await Firebase.initializeApp(
      options: DefaultFirebaseOptions.currentPlatform,
    );
  } catch (_) {}
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  const baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8081/api/v1',
  );
  final sessionStore = AlmacenSesion();
  final api = ClienteApi(baseUrl: baseUrl, sessionStore: sessionStore);
  final controller = ControladorAplicacion(
    repository: RepositorioMovil(api),
    sessionStore: sessionStore,
    cache: CachePrivada(),
  );
  runApp(AplicacionCaseMovil(controller: controller));
  WidgetsBinding.instance.addPostFrameCallback((_) {
    unawaited(_initializeFirebase());
    unawaited(controller.restoreSession());
  });
}

Future<void> _initializeFirebase() async {
  try {
    await Firebase.initializeApp(
      options: DefaultFirebaseOptions.currentPlatform,
    ).timeout(const Duration(seconds: 10));
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  } catch (error) {
    debugPrint('Firebase no inicializado: $error');
  }
}
