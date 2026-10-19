import 'package:flutter/material.dart';

import 'app/app.dart';
import 'core/auth/session_store.dart';
import 'core/cache/private_cache.dart';
import 'core/network/api_client.dart';
import 'features/app_controller.dart';
import 'features/mobile_repository.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  const baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8081/api/v1',
  );
  final sessionStore = SessionStore();
  final api = ApiClient(baseUrl: baseUrl, sessionStore: sessionStore);
  final controller = AppController(
    repository: MobileRepository(api),
    sessionStore: sessionStore,
    cache: PrivateCache(),
  );
  await controller.restoreSession();
  runApp(CaseMobileApp(controller: controller));
}
