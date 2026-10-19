import struct
import zlib

from app.modules.generacion_software.flutter_generator.api_analyzer import endpoint_for_entity
from app.modules.generacion_software.flutter_generator.uml_analyzer.model_analyzer import (
    DartEntity,
    DartField,
    FlutterProject,
    to_camel_case,
)


def render_pubspec(project: FlutterProject) -> str:
    return f"""name: {project.package_name}
description: Aplicacion Flutter generada desde UML por CASE Inteligente.
publish_to: 'none'
version: 0.1.0+1

environment:
  sdk: '>=3.4.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  http: ^1.2.2
  provider: ^6.1.2

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^4.0.0

flutter:
  uses-material-design: true
"""


def render_analysis_options() -> str:
    return """include: package:flutter_lints/flutter.yaml

linter:
  rules:
    prefer_single_quotes: true
"""


def render_main(project: FlutterProject) -> str:
    provider_imports = "\n".join(
        f"import 'modules/{entity.module_name}/{entity.module_name}_provider.dart';"
        for entity in project.entities
    )
    providers = "\n".join(
        f"        ChangeNotifierProvider(create: (_) => {entity.name}Provider()),"
        for entity in project.entities
    )
    return f"""import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/routes/app_router.dart';
import 'shared/themes/app_theme.dart';
{provider_imports}

void main() {{
  runApp(const GeneratedCaseApp());
}}

class GeneratedCaseApp extends StatelessWidget {{
  const GeneratedCaseApp({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MultiProvider(
      providers: [
{providers}
      ],
      child: MaterialApp(
        title: '{project.name}',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        darkTheme: AppTheme.dark,
        themeMode: AppTheme.mode,
        routes: AppRouter.routes,
        initialRoute: AppRouter.home,
      ),
    );
  }}
}}
"""


def render_api_client(project: FlutterProject) -> str:
    return f"""import 'dart:convert';

import 'package:http/http.dart' as http;

class ApiClient {{
  ApiClient({{this.baseUrl = const String.fromEnvironment('API_BASE_URL', defaultValue: '{project.api_base_url}') }});

  final String baseUrl;
  String? token;

  Map<String, String> get _headers => {{
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      }};

  Future<dynamic> get(String path) async {{
    final response = await http.get(Uri.parse('$baseUrl$path'), headers: _headers);
    return _decode(response);
  }}

  Future<dynamic> post(String path, Map<String, dynamic> body) async {{
    final response = await http.post(Uri.parse('$baseUrl$path'), headers: _headers, body: jsonEncode(body));
    return _decode(response);
  }}

  Future<dynamic> put(String path, Map<String, dynamic> body) async {{
    final response = await http.put(Uri.parse('$baseUrl$path'), headers: _headers, body: jsonEncode(body));
    return _decode(response);
  }}

  Future<void> delete(String path) async {{
    final response = await http.delete(Uri.parse('$baseUrl$path'), headers: _headers);
    if (response.statusCode >= 400) {{
      throw Exception('Error HTTP ${{response.statusCode}}');
    }}
  }}

  Future<dynamic> request(
    String method,
    String path, {{
    Map<String, dynamic>? body,
    Map<String, String>? query,
  }}) async {{
    final baseUri = Uri.parse('$baseUrl$path');
    final uri = query == null || query.isEmpty
        ? baseUri
        : baseUri.replace(queryParameters: query);
    final encoded = body == null || body.isEmpty ? null : jsonEncode(body);
    late final http.Response response;
    switch (method.toUpperCase()) {{
      case 'GET':
        response = await http.get(uri, headers: _headers);
        break;
      case 'POST':
        response = await http.post(uri, headers: _headers, body: encoded);
        break;
      case 'PUT':
        response = await http.put(uri, headers: _headers, body: encoded);
        break;
      case 'PATCH':
        response = await http.patch(uri, headers: _headers, body: encoded);
        break;
      case 'DELETE':
        response = await http.delete(uri, headers: _headers, body: encoded);
        break;
      default:
        throw ArgumentError.value(method, 'method', 'Metodo HTTP no soportado');
    }}
    return _decode(response);
  }}

  dynamic _decode(http.Response response) {{
    if (response.statusCode >= 400) {{
      throw ApiException(response.statusCode, response.body);
    }}
    if (response.body.isEmpty) {{
      return null;
    }}
    return jsonDecode(response.body);
  }}
}}

class ApiException implements Exception {{
  const ApiException(this.statusCode, this.message);

  final int statusCode;
  final String message;

  @override
  String toString() => 'ApiException($statusCode): $message';
}}
"""


def render_widget_test(project: FlutterProject) -> str:
    mode = {"light": "ThemeMode.light", "dark": "ThemeMode.dark"}.get(project.theme_config.mode, "ThemeMode.system")
    return f"""import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';

import 'package:{project.package_name}/main.dart';
import 'package:{project.package_name}/shared/themes/app_theme.dart';

void main() {{
  testWidgets('renders generated app', (tester) async {{
    await tester.pumpWidget(const GeneratedCaseApp());
    expect(find.text('{project.name}'), findsWidgets);
  }});

  test('theme contract is applied in light and dark modes', () {{
    expect(AppTheme.mode, {mode});
    expect(AppTheme.light.colorScheme.primary, const Color({_dart_color(project.theme_config.primary_color)}));
    expect(AppTheme.dark.colorScheme.primary, const Color({_dart_color(project.theme_config.dark_primary_color)}));
    expect(AppTheme.light.inputDecorationTheme.filled, {str(project.theme_config.input_style == 'filled').lower()});
    expect(AppTheme.light.cardTheme.elevation, { {'flat': '0', 'outlined': '0', 'elevated': '2'}.get(project.theme_config.card_style, '0')});
  }});

  testWidgets('theme semantic tokens match the generated golden', (tester) async {{
    const goldenKey = Key('theme-token-golden');
    await tester.pumpWidget(
      const Center(
        child: RepaintBoundary(
          key: goldenKey,
          child: SizedBox(
            width: 96,
            height: 32,
            child: CustomPaint(painter: _ThemeTokenPainter()),
          ),
        ),
      ),
    );
    await expectLater(
      find.byKey(goldenKey),
      matchesGoldenFile('goldens/theme_tokens.png'),
    );
  }});
}}

class _ThemeTokenPainter extends CustomPainter {{
  const _ThemeTokenPainter();

  @override
  void paint(Canvas canvas, Size size) {{
    final width = size.width / 3;
    canvas.drawRect(Rect.fromLTWH(0, 0, width, size.height), Paint()..color = AppTheme.light.colorScheme.primary);
    canvas.drawRect(Rect.fromLTWH(width, 0, width, size.height), Paint()..color = AppTheme.dark.colorScheme.primary);
    canvas.drawRect(Rect.fromLTWH(width * 2, 0, width, size.height), Paint()..color = AppTheme.light.colorScheme.error);
  }}

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}}
"""


def render_android_manifest(project: FlutterProject) -> str:
    return f"""<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />

    <application
        android:label="{project.package_name}"
        android:name="${{applicationName}}"
        android:icon="@mipmap/ic_launcher"
        android:usesCleartextTraffic="true">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTop"
            android:taskAffinity=""
            android:theme="@style/LaunchTheme"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
            android:hardwareAccelerated="true"
            android:windowSoftInputMode="adjustResize">
            <meta-data
              android:name="io.flutter.embedding.android.NormalTheme"
              android:resource="@style/NormalTheme" />
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
        <meta-data
            android:name="flutterEmbedding"
            android:value="2" />
    </application>

    <queries>
        <intent>
            <action android:name="android.intent.action.PROCESS_TEXT" />
            <data android:mimeType="text/plain" />
        </intent>
    </queries>
</manifest>
"""


def _dart_color(hex_color: str) -> str:
    value = hex_color.strip().lstrip("#").upper()
    if len(value) != 6:
        value = "0F766E"
    return f"0xFF{value}"


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    payload = kind + data
    return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)


def render_theme_golden_png(project: FlutterProject) -> bytes:
    light = project.theme_config.raw_v2.get("light", {})
    colors = (
        project.theme_config.primary_color,
        project.theme_config.dark_primary_color,
        str(light.get("error", "#B91C1C")),
    )
    pixels = []
    for color in colors:
        value = color.lstrip("#")
        red, green, blue = (int(value[index:index + 2], 16) for index in (0, 2, 4))
        pixels.extend([(red, green, blue, 255)] * 32)
    row = b"\x00" + b"".join(bytes(pixel) for pixel in pixels)
    raw = row * 32
    header = struct.pack(">IIBBBBB", 96, 32, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", header) + _png_chunk(b"IDAT", zlib.compress(raw)) + _png_chunk(b"IEND", b"")


def _render_app_theme_legacy(project: FlutterProject) -> str:
    theme = project.theme_config
    visual_density = {
        "compact": "VisualDensity.compact",
        "comfortable": "VisualDensity.comfortable",
    }.get(theme.density, "VisualDensity.standard")
    theme_mode = {"light": "ThemeMode.light", "dark": "ThemeMode.dark"}.get(theme.mode, "ThemeMode.system")
    input_filled = "true" if theme.input_style == "filled" else "false"
    card_elevation = {"flat": "0", "outlined": "0", "elevated": "2"}.get(theme.card_style, "0")
    font_scale = {"compact": 0.92, "large": 1.15}.get(theme.typography_scale, 1.0)
    font_weight = "FontWeight.w500" if theme.typography_weight == "medium" else "FontWeight.w400"
    return f"""import 'package:flutter/material.dart';

class AppTheme {{
  static const Color primaryColor = Color({_dart_color(theme.primary_color)});
  static const Color secondaryColor = Color({_dart_color(theme.secondary_color)});
  static const Color backgroundColor = Color({_dart_color(theme.background_color)});
  static const Color surfaceColor = Color({_dart_color(theme.surface_color)});
  static const Color buttonColor = Color({_dart_color(theme.button_color)});
  static const String fontFamily = '{theme.font_family}';
  static const double borderRadius = {float(theme.border_radius):.1f};
  static const ThemeMode mode = {theme_mode};
  static const Color onPrimaryColor = Color({_dart_color(theme.on_primary_color)});

  static ThemeData get light {{
    return ThemeData(
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryColor,
        primary: primaryColor,
        secondary: secondaryColor,
        surface: surfaceColor,
      ),
      scaffoldBackgroundColor: backgroundColor,
      fontFamily: fontFamily == 'system' ? null : fontFamily,
      useMaterial3: true,
      visualDensity: {visual_density},
      textTheme: ThemeData.light().textTheme.apply(
        fontFamily: fontFamily == 'system' ? null : fontFamily,
        fontSizeFactor: {font_scale},
      ).copyWith(bodyMedium: ThemeData.light().textTheme.bodyMedium?.copyWith(fontWeight: {font_weight})),
      appBarTheme: const AppBarTheme(
        backgroundColor: primaryColor,
        foregroundColor: onPrimaryColor,
        centerTitle: false,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: {input_filled},
        fillColor: surfaceColor,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular({float(theme.input_radius):.1f})),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular({float(theme.input_radius):.1f}),
          borderSide: BorderSide(color: primaryColor.withValues(alpha: 0.25)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular({float(theme.input_radius):.1f}),
          borderSide: const BorderSide(color: primaryColor, width: 1.4),
        ),
      ),
      cardTheme: CardThemeData(
        color: surfaceColor,
        margin: const EdgeInsets.all(8),
        elevation: {card_elevation},
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular({float(theme.card_radius):.1f})),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: buttonColor,
          foregroundColor: onPrimaryColor,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(borderRadius)),
          minimumSize: const Size.fromHeight(48),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: buttonColor,
          side: const BorderSide(color: buttonColor),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(borderRadius)),
          minimumSize: const Size.fromHeight(48),
        ),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: buttonColor,
        foregroundColor: onPrimaryColor,
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected) ? buttonColor : null,
        ),
        trackColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected) ? buttonColor.withValues(alpha: 0.35) : null,
        ),
      ),
      dialogTheme: DialogThemeData(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular({float(theme.dialog_radius):.1f})),
      ),
      navigationBarTheme: NavigationBarThemeData(
        indicatorColor: secondaryColor.withValues(alpha: 0.2),
        labelTextStyle: const WidgetStatePropertyAll(TextStyle(color: primaryColor)),
      ),
      drawerTheme: const DrawerThemeData(backgroundColor: surfaceColor),
    );
  }}

  static ThemeData get dark {{
    const darkPrimary = Color({_dart_color(theme.dark_primary_color)});
    const darkSecondary = Color({_dart_color(theme.dark_secondary_color)});
    const darkBackground = Color({_dart_color(theme.dark_background_color)});
    const darkSurface = Color({_dart_color(theme.dark_surface_color)});
    const darkOnPrimary = Color({_dart_color(theme.dark_on_primary_color)});
    const darkOnSurface = Color({_dart_color(theme.dark_on_surface_color)});
    return light.copyWith(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: darkBackground,
      colorScheme: const ColorScheme.dark(
        primary: darkPrimary, onPrimary: darkOnPrimary,
        secondary: darkSecondary, surface: darkSurface, onSurface: darkOnSurface,
      ),
      appBarTheme: const AppBarTheme(backgroundColor: darkSurface, foregroundColor: darkOnSurface),
      cardTheme: light.cardTheme.copyWith(color: darkSurface),
    );
  }}
}}
"""


def render_app_theme(project: FlutterProject) -> str:
    theme = project.theme_config
    light = theme.raw_v2.get("light", {})
    dark = theme.raw_v2.get("dark", {})
    light_token = lambda name, fallback: str(light.get(name, fallback))
    dark_token = lambda name, fallback: str(dark.get(name, fallback))
    visual_density = {
        "compact": "VisualDensity.compact",
        "comfortable": "VisualDensity.comfortable",
    }.get(theme.density, "VisualDensity.standard")
    theme_mode = {"light": "ThemeMode.light", "dark": "ThemeMode.dark"}.get(theme.mode, "ThemeMode.system")
    input_filled = "true" if theme.input_style == "filled" else "false"
    card_elevation = {"flat": "0", "outlined": "0", "elevated": "2"}.get(theme.card_style, "0")
    card_side = "BorderSide(color: colors.outline)" if theme.card_style == "outlined" else "BorderSide.none"
    font_scale = {"compact": 0.92, "large": 1.15}.get(theme.typography_scale, 1.0)
    font_weight = "FontWeight.w500" if theme.typography_weight == "medium" else "FontWeight.w400"
    screen_padding, section_gap, field_height = {
        "compact": (12, 8, 44), "comfortable": (20, 16, 52),
    }.get(theme.density, (16, 12, 48))
    return f"""import 'package:flutter/material.dart';

class AppTheme {{
  static const String fontFamily = '{theme.font_family}';
  static const double borderRadius = {float(theme.border_radius):.1f};
  static const double screenPadding = {float(screen_padding):.1f};
  static const double sectionGap = {float(section_gap):.1f};
  static const double fieldHeight = {float(field_height):.1f};
  static const ThemeMode mode = {theme_mode};

  static ThemeData _build(
    ColorScheme colors,
    Color background,
    Color actionColor,
    Color actionForeground,
  ) {{
    final baseTextTheme = colors.brightness == Brightness.dark
        ? ThemeData.dark().textTheme
        : ThemeData.light().textTheme;
    return ThemeData(
      colorScheme: colors,
      scaffoldBackgroundColor: background,
      fontFamily: fontFamily == 'system' ? null : fontFamily,
      useMaterial3: true,
      visualDensity: {visual_density},
      textTheme: baseTextTheme.apply(
        fontFamily: fontFamily == 'system' ? null : fontFamily,
        fontSizeFactor: {font_scale},
      ).copyWith(
        bodyMedium: baseTextTheme.bodyMedium?.copyWith(fontWeight: {font_weight}),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: colors.primary,
        foregroundColor: colors.onPrimary,
        centerTitle: false,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: {input_filled},
        fillColor: colors.surface,
        constraints: const BoxConstraints(minHeight: fieldHeight),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular({float(theme.input_radius):.1f}),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular({float(theme.input_radius):.1f}),
          borderSide: BorderSide(color: colors.outline),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular({float(theme.input_radius):.1f}),
          borderSide: BorderSide(color: colors.primary, width: 1.4),
        ),
      ),
      cardTheme: CardThemeData(
        color: colors.surface,
        margin: const EdgeInsets.all(sectionGap / 2),
        elevation: {card_elevation},
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular({float(theme.card_radius):.1f}),
          side: {card_side},
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: actionColor,
          foregroundColor: actionForeground,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(borderRadius)),
          minimumSize: const Size.fromHeight(fieldHeight),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: actionColor,
          side: BorderSide(color: actionColor),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(borderRadius)),
          minimumSize: const Size.fromHeight(fieldHeight),
        ),
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: actionColor,
        foregroundColor: actionForeground,
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected) ? actionColor : null,
        ),
        trackColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected)
              ? actionColor.withValues(alpha: 0.35)
              : null,
        ),
      ),
      dialogTheme: DialogThemeData(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular({float(theme.dialog_radius):.1f}),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        indicatorColor: colors.secondary.withValues(alpha: 0.2),
        labelTextStyle: WidgetStatePropertyAll(TextStyle(color: colors.primary)),
      ),
      drawerTheme: DrawerThemeData(backgroundColor: colors.surface),
    );
  }}

  static ThemeData get light => _build(
    const ColorScheme.light(
      primary: Color({_dart_color(theme.primary_color)}),
      onPrimary: Color({_dart_color(theme.on_primary_color)}),
      secondary: Color({_dart_color(theme.secondary_color)}),
      onSecondary: Color({_dart_color(light_token('on_secondary', '#FFFFFF'))}),
      surface: Color({_dart_color(theme.surface_color)}),
      onSurface: Color({_dart_color(theme.on_surface_color)}),
      error: Color({_dart_color(light_token('error', '#B91C1C'))}),
      onError: Color({_dart_color(light_token('on_error', '#FFFFFF'))}),
      outline: Color({_dart_color(light_token('outline', '#64748B'))}),
    ),
    const Color({_dart_color(theme.background_color)}),
    const Color({_dart_color(light_token('secondary', theme.button_color) if theme.button_style == 'tonal' else theme.button_color)}),
    const Color({_dart_color(light_token('on_secondary', '#FFFFFF') if theme.button_style == 'tonal' else theme.on_primary_color)}),
  );

  static ThemeData get dark => _build(
    const ColorScheme.dark(
      primary: Color({_dart_color(theme.dark_primary_color)}),
      onPrimary: Color({_dart_color(theme.dark_on_primary_color)}),
      secondary: Color({_dart_color(theme.dark_secondary_color)}),
      onSecondary: Color({_dart_color(dark_token('on_secondary', '#172554'))}),
      surface: Color({_dart_color(theme.dark_surface_color)}),
      onSurface: Color({_dart_color(theme.dark_on_surface_color)}),
      error: Color({_dart_color(dark_token('error', '#FCA5A5'))}),
      onError: Color({_dart_color(dark_token('on_error', '#450A0A'))}),
      outline: Color({_dart_color(dark_token('outline', '#94A3B8'))}),
    ),
    const Color({_dart_color(theme.dark_background_color)}),
    const Color({_dart_color(theme.dark_secondary_color if theme.button_style == 'tonal' else theme.dark_primary_color)}),
    const Color({_dart_color(dark_token('on_secondary', '#172554') if theme.button_style == 'tonal' else theme.dark_on_primary_color)}),
  );
}}
"""


def _render_app_router_legacy(project: FlutterProject) -> str:
    imports = "\n".join(
        f"import '../../modules/{entity.module_name}/{entity.module_name}_list_screen.dart';"
        for entity in project.entities
    )
    routes = "\n".join(
        f"    '/{entity.module_name}': (_) => const {entity.name}ListScreen(),"
        for entity in project.entities
    )
    menu_items = "\n".join(
        f"""          Card(
            child: ListTile(
              leading: const Icon(Icons.table_chart_outlined),
              title: const Text('{entity.name}'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => Navigator.pushNamed(context, '/{entity.module_name}'),
            ),
          ),"""
        for entity in project.entities
    )
    return f"""import 'package:flutter/material.dart';

{imports}

class AppRouter {{
  static const String home = '/';

  static Map<String, WidgetBuilder> get routes => {{
    home: (_) => const HomeScreen(),
{routes}
  }};
}}

class HomeScreen extends StatelessWidget {{
  const HomeScreen({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(title: const Text('{project.name}')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
{menu_items}
        ],
      ),
    );
  }}
}}
"""


def render_app_router(project: FlutterProject) -> str:
    imports = "\n".join(
        f"import '../../modules/{entity.module_name}/{entity.module_name}_list_screen.dart';"
        for entity in project.entities
    )
    routes = "\n".join(
        f"    '/{entity.module_name}': (_) => const {entity.name}ListScreen(),"
        for entity in project.entities
    )
    effective_navigation = project.theme_config.navigation_style
    if effective_navigation == "automatic":
        effective_navigation = "bottom_bar" if 2 <= len(project.entities) <= 4 else "navigation_drawer"
    if effective_navigation == "bottom_bar" and len(project.entities) < 2:
        effective_navigation = "navigation_drawer"
    if effective_navigation == "navigation_drawer":
        items = "\n".join(
            f"""            ListTile(
              leading: const Icon(Icons.table_chart_outlined),
              title: const Text('{entity.name}', overflow: TextOverflow.ellipsis),
              onTap: () => Navigator.pushNamed(context, '/{entity.module_name}'),
            ),"""
            for entity in project.entities
        )
        home = f"""class HomeScreen extends StatelessWidget {{
  const HomeScreen({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(title: const Text('{project.name}')),
      drawer: Drawer(
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(AppTheme.screenPadding),
            children: [
              const ListTile(title: Text('Modulos')),
{items}
            ],
          ),
        ),
      ),
      body: const Center(child: Text('Seleccione un modulo desde el menu.')),
    );
  }}
}}"""
    else:
        destinations = "\n".join(
            f"""          NavigationDestination(
            icon: Icon(Icons.table_chart_outlined),
            label: '{entity.name}',
          ),"""
            for entity in project.entities
        ) or "          NavigationDestination(icon: Icon(Icons.home_outlined), label: 'Inicio'),"
        route_names = ", ".join(f"'/{entity.module_name}'" for entity in project.entities)
        navigate = "" if not project.entities else f"""        final routes = <String>[{route_names}];
        Navigator.pushNamed(context, routes[index]);"""
        home = f"""class HomeScreen extends StatefulWidget {{
  const HomeScreen({{super.key}});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}}

class _HomeScreenState extends State<HomeScreen> {{
  int _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(title: const Text('{project.name}')),
      body: const Center(child: Text('Seleccione un modulo de la barra inferior.')),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) {{
          setState(() => _selectedIndex = index);
{navigate}
        }},
        destinations: const [
{destinations}
        ],
      ),
    );
  }}
}}"""
    theme_import = "import '../../shared/themes/app_theme.dart';" if effective_navigation == "navigation_drawer" else ""
    return f"""import 'package:flutter/material.dart';

{theme_import}
{imports}

class AppRouter {{
  static const String home = '/';

  static Map<String, WidgetBuilder> get routes => {{
    home: (_) => const HomeScreen(),
{routes}
  }};
}}

{home}
"""


def render_entity_model(entity: DartEntity) -> str:
    declarations = "\n".join(f"  final {field.dart_type}? {field.name};" for field in entity.fields)
    constructor_fields = "\n".join(f"    this.{field.name}," for field in entity.fields)
    from_json = "\n".join(
        f"      {field.name}: {_from_json_expression(field)},"
        for field in entity.fields
    )
    to_json = "\n".join(f"      '{field.name}': {_to_json_expression(field)}," for field in entity.fields)
    copy_fields = "\n".join(f"    {field.dart_type}? {field.name}," for field in entity.fields)
    copy_values = "\n".join(f"      {field.name}: {field.name} ?? this.{field.name}," for field in entity.fields)
    return f"""class {entity.name} {{
  const {entity.name}({{
    this.id,
{constructor_fields}
  }});

  final String? id;
{declarations}

  factory {entity.name}.fromJson(Map<String, dynamic> json) {{
    return {entity.name}(
      id: json['id']?.toString(),
{from_json}
    );
  }}

  Map<String, dynamic> toJson() {{
    return {{
      'id': id,
{to_json}
    }};
  }}

  {entity.name} copyWith({{
    String? id,
{copy_fields}
  }}) {{
    return {entity.name}(
      id: id ?? this.id,
{copy_values}
    );
  }}
}}
"""


def render_entity_service(entity: DartEntity) -> str:
    endpoint = endpoint_for_entity(entity)
    module = entity.module_name
    return f"""import '../../core/network/api_client.dart';
import '{module}_model.dart';

class {entity.name}Service {{
  {entity.name}Service({{ApiClient? apiClient}}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;
  static const String _path = '{endpoint}';

  Future<List<{entity.name}>> findAll() async {{
    final data = await _apiClient.get(_path) as List<dynamic>;
    return data.map((item) => {entity.name}.fromJson(item as Map<String, dynamic>)).toList();
  }}

  Future<{entity.name}> findById(String id) async {{
    final data = await _apiClient.get('$_path/$id') as Map<String, dynamic>;
    return {entity.name}.fromJson(data);
  }}

  Future<{entity.name}> create({entity.name} value) async {{
    final data = await _apiClient.post(_path, value.toJson()) as Map<String, dynamic>;
    return {entity.name}.fromJson(data);
  }}

  Future<{entity.name}> update(String id, {entity.name} value) async {{
    final data = await _apiClient.put('$_path/$id', value.toJson()) as Map<String, dynamic>;
    return {entity.name}.fromJson(data);
  }}

  Future<void> delete(String id) async {{
    await _apiClient.delete('$_path/$id');
  }}
}}
"""


def render_entity_provider(entity: DartEntity) -> str:
    module = entity.module_name
    camel = to_camel_case(entity.name)
    return f"""import 'package:flutter/foundation.dart';

import '{module}_model.dart';
import '{module}_service.dart';

class {entity.name}Provider extends ChangeNotifier {{
  {entity.name}Provider({{{entity.name}Service? service}}) : _service = service ?? {entity.name}Service();

  final {entity.name}Service _service;
  final List<{entity.name}> items = [];
  bool loading = false;
  String? error;

  Future<void> load() async {{
    loading = true;
    error = null;
    notifyListeners();
    try {{
      items
        ..clear()
        ..addAll(await _service.findAll());
    }} catch (exception) {{
      error = exception.toString();
    }} finally {{
      loading = false;
      notifyListeners();
    }}
  }}

  Future<void> save({entity.name} {camel}) async {{
    if ({camel}.id == null) {{
      await _service.create({camel});
    }} else {{
      await _service.update({camel}.id!, {camel});
    }}
    await load();
  }}

  Future<void> remove(String id) async {{
    await _service.delete(id);
    await load();
  }}
}}
"""


def render_entity_list_screen(entity: DartEntity) -> str:
    module = entity.module_name
    return f"""import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '{module}_form_screen.dart';
import '{module}_provider.dart';

class {entity.name}ListScreen extends StatefulWidget {{
  const {entity.name}ListScreen({{super.key}});

  @override
  State<{entity.name}ListScreen> createState() => _{entity.name}ListScreenState();
}}

class _{entity.name}ListScreenState extends State<{entity.name}ListScreen> {{
  @override
  void initState() {{
    super.initState();
    final provider = context.read<{entity.name}Provider>();
    Future.microtask(provider.load);
  }}

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(title: const Text('{entity.name}')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const {entity.name}FormScreen())),
        child: const Icon(Icons.add),
      ),
      body: Consumer<{entity.name}Provider>(
        builder: (context, provider, _) {{
          if (provider.loading) {{
            return const Center(child: CircularProgressIndicator());
          }}
          if (provider.error != null) {{
            return Center(child: Text(provider.error!));
          }}
          return ListView.builder(
            itemCount: provider.items.length,
            itemBuilder: (context, index) {{
              final item = provider.items[index];
              return Card(
                child: ListTile(
                  title: Text(item.id ?? 'Registro'),
                  subtitle: Text(item.toJson().entries.where((entry) => entry.key != 'id').map((entry) => '${{entry.key}}: ${{entry.value}}').join(' | ')),
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => {entity.name}FormScreen(initialValue: item))),
                  trailing: IconButton(
                    icon: const Icon(Icons.delete_outline),
                    onPressed: item.id == null ? null : () => provider.remove(item.id!),
                  ),
                ),
              );
            }},
          );
        }},
      ),
    );
  }}
}}
"""


def render_entity_form_screen(entity: DartEntity, show_field_labels: bool = True) -> str:
    module = entity.module_name
    relation_imports = _relation_imports(entity)
    controllers = "\n".join(
        f"  late final TextEditingController _{field.name}Controller;"
        for field in entity.fields
        if field.input_type not in {"switch", "relation"}
    )
    init_controllers = "\n".join(
        f"    _{field.name}Controller = TextEditingController(text: {_initial_controller_text(field)});"
        for field in entity.fields
        if field.input_type not in {"switch", "relation"}
    )
    dispose_controllers = "\n".join(
        f"    _{field.name}Controller.dispose();"
        for field in entity.fields
        if field.input_type not in {"switch", "relation"}
    )
    bool_fields = "\n".join(
        f"  bool _{field.name}Value = false;" for field in entity.fields if field.input_type == "switch"
    )
    relation_fields = "\n".join(
        f"  String? _{field.name}Value;" for field in entity.fields if field.input_type == "relation"
    )
    init_switches = "\n".join(
        f"    _{field.name}Value = widget.initialValue?.{field.name} ?? false;"
        for field in entity.fields
        if field.input_type == "switch"
    )
    init_relations = "\n".join(
        f"    _{field.name}Value = widget.initialValue?.{field.name};"
        for field in entity.fields
        if field.input_type == "relation"
    )
    form_fields = "\n".join(_render_form_field(field, show_field_labels) for field in entity.fields)
    model_args = "\n".join(_render_model_arg(field) for field in entity.fields)
    date_helper = _render_date_helper(entity)
    return f"""import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../shared/themes/app_theme.dart';
import '../../shared/widgets/primary_action_button.dart';
import '{module}_model.dart';
import '{module}_provider.dart';
{relation_imports}

class {entity.name}FormScreen extends StatefulWidget {{
  const {entity.name}FormScreen({{super.key, this.initialValue}});

  final {entity.name}? initialValue;

  @override
  State<{entity.name}FormScreen> createState() => _{entity.name}FormScreenState();
}}

class _{entity.name}FormScreenState extends State<{entity.name}FormScreen> {{
  final _formKey = GlobalKey<FormState>();
{controllers}
{bool_fields}
{relation_fields}

  @override
  void initState() {{
    super.initState();
{init_controllers}
{init_switches}
{init_relations}
  }}

  @override
  void dispose() {{
{dispose_controllers}
    super.dispose();
  }}

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(title: const Text('Formulario {entity.name}')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(AppTheme.screenPadding),
          children: [
{form_fields}
            const SizedBox(height: AppTheme.sectionGap),
            PrimaryActionButton(
              onPressed: _save,
              label: 'Guardar',
            ),
          ],
        ),
      ),
    );
  }}

  Future<void> _save() async {{
    if (!_formKey.currentState!.validate()) {{
      return;
    }}
    final value = {entity.name}(
      id: widget.initialValue?.id,
{model_args}
    );
    await context.read<{entity.name}Provider>().save(value);
    if (mounted) {{
      Navigator.pop(context);
    }}
  }}
{date_helper}
}}
"""


def render_shared_button(project: FlutterProject) -> str:
    button_widget = {
        "outline": "OutlinedButton",
        "tonal": "FilledButton.tonal",
    }.get(project.theme_config.button_style, "FilledButton")
    return f"""import 'package:flutter/material.dart';

class PrimaryActionButton extends StatelessWidget {{
  const PrimaryActionButton({{super.key, required this.label, required this.onPressed}});

  final String label;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {{
    return {button_widget}(onPressed: onPressed, child: Text(label));
  }}
}}
"""


def render_readme(project: FlutterProject) -> str:
    modules = "\n".join(f"- {entity.name}: `lib/modules/{entity.module_name}`" for entity in project.entities)
    return f"""# {project.name}

Aplicacion movil Flutter generada automaticamente desde UML por CASE Inteligente.

## Ejecucion

```bash
flutter pub get
flutter analyze
flutter run
```

## Backend esperado

`{project.api_base_url}`

## Estilo visual

- Color primario: `{project.theme_config.primary_color}`
- Color secundario: `{project.theme_config.secondary_color}`
- Fondo: `{project.theme_config.background_color}`
- Botones: `{project.theme_config.button_color}`
- Fuente: `{project.theme_config.font_family}`
- Bordes: `{project.theme_config.border_radius}px`
- Boton principal: `{project.theme_config.button_style}`
- Densidad: `{project.theme_config.density}`

## Modulos generados

{modules}
"""


def render_web_index(project: FlutterProject) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
  <base href="$FLUTTER_BASE_HREF">
  <meta charset="UTF-8">
  <meta content="IE=Edge" http-equiv="X-UA-Compatible">
  <meta name="description" content="Aplicacion Flutter generada por CASE Inteligente.">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black">
  <meta name="apple-mobile-web-app-title" content="{project.name}">
  <title>{project.name}</title>
  <link rel="manifest" href="manifest.json">
</head>
<body>
  <script src="flutter_bootstrap.js" async></script>
</body>
</html>
"""


def render_web_manifest(project: FlutterProject) -> str:
    return f"""{{
  "name": "{project.name}",
  "short_name": "{project.name}",
  "start_url": ".",
  "display": "standalone",
  "background_color": "#F8FAFC",
  "theme_color": "#0F766E",
  "description": "Aplicacion Flutter generada por CASE Inteligente.",
  "orientation": "portrait-primary",
  "prefer_related_applications": false
}}
"""


def _from_json_expression(field: DartField) -> str:
    if field.dart_type == "int":
        return f"int.tryParse(json['{field.name}']?.toString() ?? '')"
    if field.dart_type == "double":
        return f"double.tryParse(json['{field.name}']?.toString() ?? '')"
    if field.dart_type == "bool":
        return f"json['{field.name}'] == true"
    if field.dart_type == "DateTime":
        return f"json['{field.name}'] == null ? null : DateTime.tryParse(json['{field.name}'].toString())"
    return f"json['{field.name}']?.toString()"


def _to_json_expression(field: DartField) -> str:
    if field.dart_type == "DateTime":
        return f"{field.name} == null ? null : '${{{field.name}!.year.toString().padLeft(4, '0')}}-${{{field.name}!.month.toString().padLeft(2, '0')}}-${{{field.name}!.day.toString().padLeft(2, '0')}}'"
    return field.name


def _initial_controller_text(field: DartField) -> str:
    if field.dart_type == "DateTime":
        return f"_formatDate(widget.initialValue?.{field.name})"
    return f"widget.initialValue?.{field.name}?.toString() ?? ''"


def _render_date_helper(entity: DartEntity) -> str:
    if not any(field.input_type == "date" for field in entity.fields):
        return ""
    return """
  static String _formatDate(DateTime? value) {
    if (value == null) {
      return '';
    }
    return '${value.year.toString().padLeft(4, '0')}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';
  }
"""


def _render_form_field(field: DartField, show_label: bool = True) -> str:
    label = field.name if show_label else ""
    if field.input_type == "switch":
        return f"""            SwitchListTile(
              title: const Text('{label}'),
              value: _{field.name}Value,
              onChanged: (value) => setState(() => _{field.name}Value = value),
            ),"""
    if field.input_type == "date":
        validator = "if (value == null || value.isEmpty) return 'Campo requerido';" if field.required else ""
        return f"""            TextFormField(
              controller: _{field.name}Controller,
              readOnly: true,
              decoration: const InputDecoration(
                labelText: '{label}',
                suffixIcon: Icon(Icons.calendar_today_outlined),
              ),
              onTap: () async {{
                final current = DateTime.tryParse(_{field.name}Controller.text) ?? DateTime.now();
                final selected = await showDatePicker(
                  context: context,
                  initialDate: current,
                  firstDate: DateTime(1900),
                  lastDate: DateTime(2100),
                );
                if (selected != null) {{
                  _{field.name}Controller.text = _formatDate(selected);
                }}
              }},
              validator: (value) {{
                {validator}
                return null;
              }},
            ),
            const SizedBox(height: AppTheme.sectionGap),"""
    if field.input_type == "relation" and field.relation_target and field.relation_module:
        service_name = f"{field.relation_target}Service"
        return f"""            FutureBuilder<List<{field.relation_target}>>(
              future: {service_name}().findAll(),
              builder: (context, snapshot) {{
                final options = snapshot.data ?? const <{field.relation_target}>[];
                return DropdownButtonFormField<String>(
                  isExpanded: true,
                  initialValue: _{field.name}Value,
                  decoration: const InputDecoration(labelText: '{label}'),
                  selectedItemBuilder: (context) => options
                      .map((item) => Align(
                            alignment: Alignment.centerLeft,
                            child: Text(
                              _compactDisplayLabel(item.toJson()),
                              overflow: TextOverflow.ellipsis,
                              maxLines: 1,
                            ),
                          ))
                      .toList(),
                  items: options
                      .map((item) => DropdownMenuItem<String>(
                            value: item.id,
                            child: Text(
                              _displayLabel(item.toJson()),
                              overflow: TextOverflow.ellipsis,
                              maxLines: 1,
                            ),
                          ))
                      .toList(),
                  onChanged: (value) => setState(() => _{field.name}Value = value),
                  validator: (value) {{
                    {'if (value == null || value.isEmpty) return "Seleccione un registro";' if field.required else ''}
                    return null;
                  }},
                );
              }},
            ),
            const SizedBox(height: AppTheme.sectionGap),"""
    keyboard = "TextInputType.number" if field.input_type == "number" else "TextInputType.emailAddress" if field.input_type == "email" else "TextInputType.text"
    validator = "if (value == null || value.isEmpty) return 'Campo requerido';" if field.required else ""
    return f"""            TextFormField(
              controller: _{field.name}Controller,
              decoration: const InputDecoration(labelText: '{label}'),
              keyboardType: {keyboard},
              validator: (value) {{
                {validator}
                return null;
              }},
            ),
            const SizedBox(height: AppTheme.sectionGap),"""


def _render_model_arg(field: DartField) -> str:
    if field.input_type == "switch":
        return f"      {field.name}: _{field.name}Value,"
    if field.input_type == "relation":
        return f"      {field.name}: _{field.name}Value,"
    if field.dart_type == "int":
        return f"      {field.name}: int.tryParse(_{field.name}Controller.text),"
    if field.dart_type == "double":
        return f"      {field.name}: double.tryParse(_{field.name}Controller.text),"
    if field.dart_type == "DateTime":
        return f"      {field.name}: DateTime.tryParse(_{field.name}Controller.text),"
    return f"      {field.name}: _{field.name}Controller.text,"


def _relation_imports(entity: DartEntity) -> str:
    imports: list[str] = []
    for field in entity.fields:
        if field.input_type == "relation" and field.relation_module:
            imports.append(f"import '../{field.relation_module}/{field.relation_module}_model.dart';")
            imports.append(f"import '../{field.relation_module}/{field.relation_module}_service.dart';")
    helper = """
String _displayLabel(Map<String, dynamic> json) {
  final name = json['nombre'] ?? json['name'];
  final id = json['id'];
  if (name != null && id != null) {
    final value = id.toString();
    final shortId = value.length > 8 ? '${value.substring(0, 8)}...' : value;
    return '$name ($shortId)';
  }
  return (name ?? id ?? 'Registro').toString();
}

String _compactDisplayLabel(Map<String, dynamic> json) {
  return (json['nombre'] ?? json['name'] ?? json['id'] ?? 'Registro').toString();
}
""" if imports else ""
    return "\n".join(sorted(set(imports))) + ("\n" + helper if imports else "")
