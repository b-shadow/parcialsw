import 'package:flutter/material.dart';

import 'app/aplicacion.dart';
import 'core/auth/almacen_sesion.dart';
import 'core/cache/cache_privada.dart';
import 'core/network/cliente_api.dart';
import 'features/controlador_aplicacion.dart';
import 'features/repositorio_movil.dart';

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
  await controller.restoreSession();
  runApp(
    AplicacionCaseMovil(
      controller: controller,
      modoInicial: await cargarModoTemaMovil(),
    ),
  );
}
