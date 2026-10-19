import 'package:flutter/material.dart';

import '../../core/models/uml_models.dart';
import '../../core/network/api_client.dart';
import '../../shared/widgets/case_top_bar.dart';
import '../../shared/widgets/content_states.dart';
import '../app_controller.dart';
import 'widgets/uml_readonly_canvas.dart';

class DiagramViewerPage extends StatefulWidget {
  final AppController controller;
  final DiagramSummary summary;
  const DiagramViewerPage({
    super.key,
    required this.controller,
    required this.summary,
  });

  @override
  State<DiagramViewerPage> createState() => _DiagramViewerPageState();
}

class _DiagramViewerPageState extends State<DiagramViewerPage> {
  DiagramDetail? _diagram;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _error = null);
    try {
      final diagram = await widget.controller.repository.diagram(
        widget.summary.id,
      );
      if (diagram.canEdit) {
        throw const ApiException(
          'El backend no aplico el contrato movil de solo lectura.',
        );
      }
      final userId = widget.controller.profile?.id;
      if (userId != null) {
        await widget.controller.cache.write(
          userId,
          'diagram:${widget.summary.id}',
          diagram.toJson(),
        );
      }
      if (mounted) setState(() => _diagram = diagram);
    } on ApiException catch (exception) {
      final userId = widget.controller.profile?.id;
      final cached = userId == null
          ? null
          : await widget.controller.cache.read(
              userId,
              'diagram:${widget.summary.id}',
            );
      final data = cached?['data'];
      if (data is Map<String, dynamic>) {
        if (mounted) setState(() => _diagram = DiagramDetail.fromJson(data));
      } else if (mounted) {
        setState(() => _error = exception.message);
      }
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: CaseTopBar(
      title: widget.summary.name,
      leading: const BackButton(),
      actions: const [
        Padding(
          padding: EdgeInsets.only(right: 12),
          child: Tooltip(
            message: 'Solo lectura',
            child: Icon(Icons.visibility_outlined),
          ),
        ),
      ],
    ),
    body: _error != null
        ? ErrorPanel(message: _error!, onRetry: _load)
        : _diagram == null
        ? const Center(child: CircularProgressIndicator())
        : _diagram!.classes.isEmpty
        ? const EmptyState(
            icon: Icons.schema_outlined,
            title: 'Diagrama vacio',
            message: 'Este diagrama aun no contiene clases.',
          )
        : UmlReadonlyCanvas(diagram: _diagram!),
  );
}
