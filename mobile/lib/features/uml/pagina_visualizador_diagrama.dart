import 'package:flutter/material.dart';

import '../../core/models/modelos_uml.dart';
import '../../core/network/cliente_api.dart';
import '../../shared/widgets/barra_superior_case.dart';
import '../../shared/widgets/estados_contenido.dart';
import '../controlador_aplicacion.dart';
import 'widgets/lienzo_uml_lectura.dart';

class PaginaVisualizadorDiagrama extends StatefulWidget {
  final ControladorAplicacion controller;
  final ResumenDiagrama summary;
  const PaginaVisualizadorDiagrama({
    super.key,
    required this.controller,
    required this.summary,
  });

  @override
  State<PaginaVisualizadorDiagrama> createState() =>
      _EstadoPaginaVisualizadorDiagrama();
}

class _EstadoPaginaVisualizadorDiagrama
    extends State<PaginaVisualizadorDiagrama> {
  DetalleDiagrama? _diagram;
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
        throw const ExcepcionApi(
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
    } on ExcepcionApi catch (exception) {
      final userId = widget.controller.profile?.id;
      final cached = userId == null
          ? null
          : await widget.controller.cache.read(
              userId,
              'diagram:${widget.summary.id}',
            );
      final data = cached?['data'];
      if (data is Map<String, dynamic>) {
        if (mounted) setState(() => _diagram = DetalleDiagrama.fromJson(data));
      } else if (mounted) {
        setState(() => _error = exception.message);
      }
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: BarraSuperiorCase(
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
        ? PanelError(message: _error!, onRetry: _load)
        : _diagram == null
        ? const Center(child: CircularProgressIndicator())
        : _diagram!.classes.isEmpty
        ? const EstadoVacio(
            icon: Icons.schema_outlined,
            title: 'Diagrama vacio',
            message: 'Este diagrama aun no contiene clases.',
          )
        : LienzoUMLLectura(diagram: _diagram!),
  );
}
