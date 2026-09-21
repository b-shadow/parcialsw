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

  dynamic _decode(http.Response response) {{
    if (response.statusCode >= 400) {{
      throw Exception('Error HTTP ${{response.statusCode}}: ${{response.body}}');
    }}
    if (response.body.isEmpty) {{
      return null;
    }}
    return jsonDecode(response.body);
  }}
}}
"""


def render_widget_test(project: FlutterProject) -> str:
    return f"""import 'package:flutter_test/flutter_test.dart';

import 'package:{project.package_name}/main.dart';

void main() {{
  testWidgets('renders generated app', (tester) async {{
    await tester.pumpWidget(const GeneratedCaseApp());
    expect(find.text('{project.name}'), findsWidgets);
  }});
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


def render_app_theme() -> str:
    return """import 'package:flutter/material.dart';

class AppTheme {
  static ThemeData get light {
    return ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0F766E)),
      useMaterial3: true,
      inputDecorationTheme: const InputDecorationTheme(border: OutlineInputBorder()),
      cardTheme: const CardThemeData(margin: EdgeInsets.all(8)),
    );
  }
}
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


def render_entity_form_screen(entity: DartEntity) -> str:
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
    form_fields = "\n".join(_render_form_field(field) for field in entity.fields)
    model_args = "\n".join(_render_model_arg(field) for field in entity.fields)
    date_helper = _render_date_helper(entity)
    return f"""import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

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
          padding: const EdgeInsets.all(16),
          children: [
{form_fields}
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _save,
              child: const Text('Guardar'),
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


def render_shared_button() -> str:
    return """import 'package:flutter/material.dart';

class PrimaryActionButton extends StatelessWidget {
  const PrimaryActionButton({super.key, required this.label, required this.onPressed});

  final String label;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return FilledButton(onPressed: onPressed, child: Text(label));
  }
}
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


def _render_form_field(field: DartField) -> str:
    if field.input_type == "switch":
        return f"""            SwitchListTile(
              title: const Text('{field.name}'),
              value: _{field.name}Value,
              onChanged: (value) => setState(() => _{field.name}Value = value),
            ),"""
    if field.input_type == "date":
        validator = "if (value == null || value.isEmpty) return 'Campo requerido';" if field.required else ""
        return f"""            TextFormField(
              controller: _{field.name}Controller,
              readOnly: true,
              decoration: const InputDecoration(
                labelText: '{field.name}',
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
            const SizedBox(height: 12),"""
    if field.input_type == "relation" and field.relation_target and field.relation_module:
        service_name = f"{field.relation_target}Service"
        return f"""            FutureBuilder<List<{field.relation_target}>>(
              future: {service_name}().findAll(),
              builder: (context, snapshot) {{
                final options = snapshot.data ?? const <{field.relation_target}>[];
                return DropdownButtonFormField<String>(
                  isExpanded: true,
                  initialValue: _{field.name}Value,
                  decoration: const InputDecoration(labelText: '{field.name}'),
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
            const SizedBox(height: 12),"""
    keyboard = "TextInputType.number" if field.input_type == "number" else "TextInputType.emailAddress" if field.input_type == "email" else "TextInputType.text"
    validator = "if (value == null || value.isEmpty) return 'Campo requerido';" if field.required else ""
    return f"""            TextFormField(
              controller: _{field.name}Controller,
              decoration: const InputDecoration(labelText: '{field.name}'),
              keyboardType: {keyboard},
              validator: (value) {{
                {validator}
                return null;
              }},
            ),
            const SizedBox(height: 12),"""


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
