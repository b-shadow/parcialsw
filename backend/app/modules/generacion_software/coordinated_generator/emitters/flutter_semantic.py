import json
import re
from pathlib import Path

from app.modules.generacion_software.coordinated_generator.contracts import (
    GenerationPlan,
    OperationPlan,
    ParameterPlan,
    UiFieldPlan,
    build_ui_manifest,
)


def emit_flutter_semantics(plan: GenerationPlan, project_dir: Path) -> list[Path]:
    package_name = _package_name(project_dir, plan.project.package_name)
    display_name = _display_name(project_dir, plan.project.name)
    files: dict[Path, str] = {
        project_dir / "generation-plan.json": json.dumps(
            plan.model_dump(mode="json"), indent=2, sort_keys=True
        ),
        project_dir / "lib/generated/functional_contract.dart": _contract(plan),
        project_dir / "test/functional_contract_test.dart": _contract_test(plan, package_name),
        project_dir / "ui_manifest.json": json.dumps(
            build_ui_manifest(plan).model_dump(mode="json"), indent=2, sort_keys=True
        ),
    }
    readme = project_dir / "README.md"
    if readme.exists():
        files[readme] = readme.read_text(encoding="utf-8") + _readme_appendix(plan)
    for operation in plan.operations:
        if operation.route:
            module = operation.owner_module
            action_file = _snake(operation.dart_name)
            files[
                project_dir / f"lib/modules/{module}/actions/{action_file}_service.dart"
            ] = _service(operation)
        if operation.ui_action:
            action_file = _snake(operation.dart_name)
            files[
                project_dir / f"lib/modules/{operation.owner_module}/actions/{action_file}_screen.dart"
            ] = _screen(operation)
    files[project_dir / "lib/core/routes/app_router.dart"] = _router(plan, display_name)
    written = []
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def _dart_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _snake(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).replace("-", "_").lower()


def _package_name(project_dir: Path, fallback: str) -> str:
    pubspec = project_dir / "pubspec.yaml"
    if pubspec.exists():
        for line in pubspec.read_text(encoding="utf-8").splitlines():
            if line.startswith("name:"):
                return line.split(":", 1)[1].strip()
    return fallback


def _display_name(project_dir: Path, fallback: str) -> str:
    router = project_dir / "lib/core/routes/app_router.dart"
    if router.exists():
        match = re.search(r"AppBar\(title: const Text\('([^']+)'\)\)", router.read_text(encoding="utf-8"))
        if match:
            return match.group(1)
    return fallback


def _contract(plan: GenerationPlan) -> str:
    rows = ",\n".join(
        f"    FunctionalRoute(operationId: '{route.operation_id}', method: '{route.http_method}', path: '{_dart_literal(route.effective_path)}')"
        for route in plan.routes
    )
    return f"""class FunctionalRoute {{
  const FunctionalRoute({{required this.operationId, required this.method, required this.path}});

  final String operationId;
  final String method;
  final String path;
}}

const functionalRoutes = <FunctionalRoute>[
{rows}
];
"""


def _service(operation: OperationPlan) -> str:
    assert operation.route is not None
    signature = ", ".join(
        (
            f"required {item.logical_type.dart} {item.name}"
            if item.required
            else f"{item.logical_type.dart}? {item.name}"
        )
        for item in operation.parameters
    )
    path = operation.route.effective_path
    for name in operation.route.path_parameters:
        path = path.replace("{" + name + "}", f"${name}")
    body = "\n".join(
        f"      '{item.name}': {_encode_value(item)},"
        for item in operation.parameters
        if item.location == "body"
    )
    query = "\n".join(
        f"      '{item.name}': {item.name}.toString(),"
        for item in operation.parameters
        if item.location == "query"
    )
    date_helper = """
String _dateOnly(DateTime value) {
  return '${value.year.toString().padLeft(4, '0')}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';
}
""" if any(item.logical_type.logical == "date" for item in operation.parameters) else ""
    return f"""import '../../../core/network/api_client.dart';

class {operation.owner_entity}{operation.dart_name[:1].upper() + operation.dart_name[1:]}ActionService {{
  {operation.owner_entity}{operation.dart_name[:1].upper() + operation.dart_name[1:]}ActionService({{ApiClient? apiClient}})
      : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<dynamic> execute({{{signature}}}) {{
    return _apiClient.request(
      '{operation.route.http_method}',
      '{path}',
      body: <String, dynamic>{{
{body}
      }},
      query: <String, String>{{
{query}
      }},
    );
  }}
}}
{date_helper}
"""


def _encode_value(parameter: ParameterPlan) -> str:
    if parameter.logical_type.logical == "date":
        return (
            f"_dateOnly({parameter.name})"
            if parameter.required
            else f"{parameter.name} == null ? null : _dateOnly({parameter.name})"
        )
    if parameter.logical_type.logical == "datetime":
        return (
            f"{parameter.name}.toIso8601String()"
            if parameter.required
            else f"{parameter.name}?.toIso8601String()"
        )
    return parameter.name


def _screen(operation: OperationPlan) -> str:
    assert operation.ui_action is not None
    action_class = f"{operation.owner_entity}{operation.dart_name[:1].upper() + operation.dart_name[1:]}ActionService"
    controllers = []
    state_fields = []
    dispose = []
    widgets = []
    args = []
    state_validation = []
    ui_by_name = {item.json_name: item for item in operation.ui_action.fields}
    for parameter in operation.parameters:
        field = ui_by_name.get(parameter.name)
        if field is None or field.hidden:
            continue
        if field.control == "switch":
            state_fields.append(f"  bool _{parameter.name} = false;")
            args.append(f"{parameter.name}: _{parameter.name}")
        elif field.control in {"date_picker", "date_time_picker"}:
            state_fields.append(f"  DateTime? _{parameter.name};")
            args.append(
                f"{parameter.name}: _{parameter.name}{'!' if parameter.required else ''}"
            )
            if parameter.required:
                state_validation.append(
                    f"    if (_{parameter.name} == null) {{ setState(() => _error = 'Seleccione {field.label}'); return; }}"
                )
        elif field.control == "entity_selector":
            state_fields.append(f"  String? _{parameter.name};")
            args.append(f"{parameter.name}: _{parameter.name}!")
        else:
            controllers.append(
                f"  final _{parameter.name}Controller = TextEditingController();"
            )
            dispose.append(f"    _{parameter.name}Controller.dispose();")
            args.append(f"{parameter.name}: {_parsed_controller(parameter)}")
        widgets.append(_field_widget(field, parameter))
    confirm = ""
    if operation.ui_action.confirmation_required:
        confirm = """
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirmar accion'),
        content: const Text('Revise los datos antes de continuar.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Confirmar')),
        ],
      ),
    );
    if (confirmed != true) return;
"""
    success = _dart_literal(operation.ui_action.success_message or "Operacion completada")
    date_helper = """
String _dateOnly(DateTime value) {
  return '${value.year.toString().padLeft(4, '0')}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';
}
"""
    action_file = _snake(operation.dart_name)
    return f"""import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '{action_file}_service.dart';

class {operation.owner_entity}{operation.dart_name[:1].upper() + operation.dart_name[1:]}ActionScreen extends StatefulWidget {{
  const {operation.owner_entity}{operation.dart_name[:1].upper() + operation.dart_name[1:]}ActionScreen({{super.key}});

  @override
  State<{operation.owner_entity}{operation.dart_name[:1].upper() + operation.dart_name[1:]}ActionScreen> createState() => _ActionScreenState();
}}

class _ActionScreenState extends State<{operation.owner_entity}{operation.dart_name[:1].upper() + operation.dart_name[1:]}ActionScreen> {{
  final _formKey = GlobalKey<FormState>();
  final _service = {action_class}();
{chr(10).join(controllers)}
{chr(10).join(state_fields)}
  bool _submitting = false;
  String? _error;

  @override
  void dispose() {{
{chr(10).join(dispose)}
    super.dispose();
  }}

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(title: const Text('{_dart_literal(operation.ui_action.label)}')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
{chr(10).join(widgets)}
            if (_error != null) Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ),
            FilledButton.icon(
              onPressed: _submitting ? null : _submit,
              icon: _submitting
                  ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.play_arrow),
              label: const Text('Ejecutar'),
            ),
          ],
        ),
      ),
    );
  }}

  Future<void> _submit() async {{
    if (!_formKey.currentState!.validate()) return;
{chr(10).join(state_validation)}
{confirm}
    setState(() {{ _submitting = true; _error = null; }});
    try {{
      await _service.execute({', '.join(args)});
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('{success}')));
      Navigator.pop(context, true);
    }} on ApiException catch (exception) {{
      if (mounted) setState(() => _error = exception.message);
    }} finally {{
      if (mounted) setState(() => _submitting = false);
    }}
  }}
}}

{date_helper}
"""


def _parsed_controller(parameter: ParameterPlan) -> str:
    name = f"_{parameter.name}Controller.text"
    if parameter.logical_type.dart == "int":
        return f"int.{'parse' if parameter.required else 'tryParse'}({name})"
    if parameter.logical_type.dart == "double":
        return f"double.{'parse' if parameter.required else 'tryParse'}({name})"
    return name


def _field_widget(field: UiFieldPlan, parameter: ParameterPlan) -> str:
    label = _dart_literal(field.label)
    required = "if (value == null || value.toString().trim().isEmpty) return 'Campo requerido';" if field.required else ""
    if field.control == "switch":
        return f"""            SwitchListTile(
              title: const Text('{label}'),
              value: _{parameter.name},
              onChanged: (value) => setState(() => _{parameter.name} = value),
            ),"""
    if field.control in {"date_picker", "date_time_picker"}:
        return f"""            ListTile(
              title: const Text('{label}'),
              subtitle: Text(_{parameter.name} == null ? 'Seleccionar fecha' : _dateOnly(_{parameter.name}!)),
              trailing: const Icon(Icons.calendar_today_outlined),
              onTap: () async {{
                final value = await showDatePicker(context: context, initialDate: DateTime.now(), firstDate: DateTime(1900), lastDate: DateTime(2100));
                if (value != null) setState(() => _{parameter.name} = value);
              }},
            ),"""
    if field.control == "entity_selector":
        source = field.source_module or ""
        return f"""            FutureBuilder<dynamic>(
              future: ApiClient().get('/api/{source}s'),
              builder: (context, snapshot) {{
                final values = snapshot.data is List ? snapshot.data as List : const [];
                return DropdownButtonFormField<String>(
                  isExpanded: true,
                  initialValue: _{parameter.name},
                  decoration: const InputDecoration(labelText: '{label}'),
                  items: values.map((item) {{
                    final map = item as Map<String, dynamic>;
                    return DropdownMenuItem(value: map['id'].toString(), child: Text((map['nombre'] ?? map['id']).toString(), overflow: TextOverflow.ellipsis));
                  }}).toList(),
                  onChanged: (value) => setState(() => _{parameter.name} = value),
                  validator: (value) {{ {required} return null; }},
                );
              }},
            ),"""
    keyboard = "TextInputType.number" if parameter.logical_type.dart in {"int", "double"} else "TextInputType.text"
    lines = "minLines: 3, maxLines: 6," if field.control == "multiline_text" else ""
    return f"""            TextFormField(
              controller: _{parameter.name}Controller,
              decoration: const InputDecoration(labelText: '{label}'),
              keyboardType: {keyboard},
              {lines}
              validator: (value) {{ {required} return null; }},
            ),
            const SizedBox(height: 12),"""


def _router_legacy(plan: GenerationPlan, display_name: str) -> str:
    imports = [
        f"import '../../modules/{entity.module_name}/{entity.module_name}_list_screen.dart';"
        for entity in plan.entities
    ]
    imports.extend(
        f"import '../../modules/{action.owner_module}/actions/{_snake(action.dart_name)}_screen.dart';"
        for action in plan.ui_actions
    )
    routes = [
        f"    '/{entity.module_name}': (_) => const {entity.name}ListScreen(),"
        for entity in plan.entities
    ]
    routes.extend(
        f"    '/actions/{action.dart_name}': (_) => const {action.owner_entity}{action.dart_name[:1].upper() + action.dart_name[1:]}ActionScreen(),"
        for action in plan.ui_actions
    )
    cards = [
        f"          ListTile(leading: const Icon(Icons.table_chart_outlined), title: const Text('{entity.name}'), trailing: const Icon(Icons.chevron_right), onTap: () => Navigator.pushNamed(context, '/{entity.module_name}'))," 
        for entity in plan.entities
    ]
    cards.extend(
        f"          ListTile(leading: const Icon(Icons.bolt_outlined), title: const Text('{_dart_literal(action.label)}'), trailing: const Icon(Icons.chevron_right), onTap: () => Navigator.pushNamed(context, '/actions/{action.dart_name}'))," 
        for action in plan.ui_actions
    )
    return f"""import 'package:flutter/material.dart';

{chr(10).join(imports)}

class AppRouter {{
  static const String home = '/';
  static Map<String, WidgetBuilder> get routes => {{
    home: (_) => const HomeScreen(),
{chr(10).join(routes)}
  }};
}}

class HomeScreen extends StatelessWidget {{
  const HomeScreen({{super.key}});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('{_dart_literal(display_name)}')),
    body: ListView(padding: const EdgeInsets.all(16), children: [
{chr(10).join(cards)}
    ]),
  );
}}
"""


def _router(plan: GenerationPlan, display_name: str) -> str:
    imports = [
        f"import '../../modules/{entity.module_name}/{entity.module_name}_list_screen.dart';"
        for entity in plan.entities
    ]
    imports.extend(
        f"import '../../modules/{action.owner_module}/actions/{_snake(action.dart_name)}_screen.dart';"
        for action in plan.ui_actions
    )
    entries = [
        (entity.name, f"/{entity.module_name}", "Icons.table_chart_outlined")
        for entity in plan.entities
    ]
    entries.extend(
        (_dart_literal(action.label), f"/actions/{action.dart_name}", "Icons.bolt_outlined")
        for action in plan.ui_actions
    )
    routes = [
        f"    '/{entity.module_name}': (_) => const {entity.name}ListScreen(),"
        for entity in plan.entities
    ]
    routes.extend(
        f"    '/actions/{action.dart_name}': (_) => const {action.owner_entity}{action.dart_name[:1].upper() + action.dart_name[1:]}ActionScreen(),"
        for action in plan.ui_actions
    )
    configured = str(plan.theme.get("components", {}).get("navigation_style", "automatic"))
    effective = "bottom_bar" if configured == "automatic" and 2 <= len(entries) <= 4 else configured
    if effective == "automatic":
        effective = "navigation_drawer"
    if effective == "bottom_bar" and len(entries) < 2:
        effective = "navigation_drawer"
    if effective == "navigation_drawer":
        tiles = "\n".join(
            f"            ListTile(leading: const Icon({icon}), title: const Text('{label}', overflow: TextOverflow.ellipsis), onTap: () => Navigator.pushNamed(context, '{path}')) ,"
            for label, path, icon in entries
        )
        home = f"""class HomeScreen extends StatelessWidget {{
  const HomeScreen({{super.key}});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('{_dart_literal(display_name)}')),
    drawer: Drawer(
      child: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(AppTheme.screenPadding),
          children: [
            const ListTile(title: Text('Modulos y acciones')),
{tiles}
          ],
        ),
      ),
    ),
    body: const Center(child: Text('Seleccione una opcion desde el menu.')),
  );
}}"""
    else:
        destinations = "\n".join(
            f"          NavigationDestination(icon: Icon({icon}), label: '{label}'),"
            for label, _, icon in entries
        ) or "          NavigationDestination(icon: Icon(Icons.home_outlined), label: 'Inicio'),"
        path_values = ", ".join(f"'{path}'" for _, path, _ in entries)
        navigate = "" if not entries else f"""          final paths = <String>[{path_values}];
          Navigator.pushNamed(context, paths[index]);"""
        home = f"""class HomeScreen extends StatefulWidget {{
  const HomeScreen({{super.key}});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}}

class _HomeScreenState extends State<HomeScreen> {{
  int _selectedIndex = 0;
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('{_dart_literal(display_name)}')),
    body: const Center(child: Text('Seleccione una opcion de la barra inferior.')),
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
}}"""
    theme_import = "import '../../shared/themes/app_theme.dart';" if effective == "navigation_drawer" else ""
    return f"""import 'package:flutter/material.dart';

{theme_import}
{chr(10).join(imports)}

class AppRouter {{
  static const String home = '/';
  static Map<String, WidgetBuilder> get routes => {{
    home: (_) => const HomeScreen(),
{chr(10).join(routes)}
  }};
}}

{home}
"""


def _contract_test(plan: GenerationPlan, package_name: str) -> str:
    return f"""import 'package:flutter_test/flutter_test.dart';
import 'package:{package_name}/generated/functional_contract.dart';

void main() {{
  test('functional route inventory is deterministic', () {{
    expect(functionalRoutes.length, {len(plan.routes)});
    expect(functionalRoutes.map((item) => item.operationId).toSet().length, {len(plan.routes)});
  }});
}}
"""


def _readme_appendix(plan: GenerationPlan) -> str:
    actions = "\n".join(
        f"- {item.label}: `/actions/{item.dart_name}`" for item in plan.ui_actions
    ) or "- No se definieron acciones visibles; las operaciones son internas o solo API."
    return f"""

## Acciones funcionales coordinadas

Plan inmutable: `{plan.canonical_hash}`

{actions}

Las llamadas HTTP y campos del formulario proceden de `generation-plan.json`.
"""
