import 'package:flutter/material.dart';

import '../../core/models/modelos_comunicacion.dart';
import '../../core/models/modelos_uml.dart';
import '../../core/network/cliente_api.dart';
import '../../shared/widgets/estados_contenido.dart';
import '../controlador_aplicacion.dart';
import '../projects/pagina_detalle_proyecto.dart';
import '../uml/pagina_visualizador_diagrama.dart';
import 'widgets/tarjeta_notificacion.dart';

class PaginaNotificaciones extends StatefulWidget {
  final ControladorAplicacion controller;
  const PaginaNotificaciones({super.key, required this.controller});

  @override
  State<PaginaNotificaciones> createState() => _EstadoPaginaNotificaciones();
}

class _EstadoPaginaNotificaciones extends State<PaginaNotificaciones> {
  List<ElementoNotificacion> _items = const [];
  bool _loading = true;
  bool _unreadOnly = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      _items = await widget.controller.repository.notifications(
        unreadOnly: _unreadOnly,
      );
    } on ExcepcionApi catch (exception) {
      _error = exception.message;
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _open(ElementoNotificacion item) async {
    if (!item.isRead) {
      try {
        await widget.controller.repository.markNotificationRead(
          item.id,
          clicked: true,
        );
        await widget.controller.refreshProjects();
        await _load();
      } on ExcepcionApi catch (exception) {
        if (mounted) {
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(SnackBar(content: Text(exception.message)));
        }
        return;
      }
    }
    if (!mounted) return;
    final route = item.deepLink['route_name']?.toString();
    final params = item.deepLink['params'] as Map? ?? const {};
    final projectId = item.projectId ?? params['project_id']?.toString();
    final matches = widget.controller.projects.where(
      (candidate) => candidate.id == projectId,
    );
    final project = matches.isEmpty ? null : matches.first;
    if (route == 'project_diagram' && params['diagram_id'] != null) {
      try {
        final detail = await widget.controller.repository.diagram(
          params['diagram_id'].toString(),
        );
        if (!mounted) return;
        await Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => PaginaVisualizadorDiagrama(
              controller: widget.controller,
              summary: ResumenDiagrama(
                id: detail.id,
                projectId: projectId ?? '',
                name: detail.name,
                type: 'class',
                classCount: detail.classes.length,
                relationshipCount: detail.relationships.length,
                updatedAt: DateTime.now(),
              ),
            ),
          ),
        );
        return;
      } on ExcepcionApi catch (exception) {
        if (mounted) {
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(SnackBar(content: Text(exception.message)));
        }
        return;
      }
    }
    if (project != null) {
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => PaginaDetalleProyecto(
            controller: widget.controller,
            project: project,
            initialTab: route == 'project_ai' ? 4 : 0,
          ),
        ),
      );
      return;
    }
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Notificacion revisada.')));
  }

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
        child: Row(
          children: [
            Expanded(
              child: SegmentedButton<bool>(
                segments: const [
                  ButtonSegment(value: false, label: Text('Todas')),
                  ButtonSegment(value: true, label: Text('No leidas')),
                ],
                selected: {_unreadOnly},
                onSelectionChanged: (value) {
                  _unreadOnly = value.first;
                  _load();
                },
              ),
            ),
            const SizedBox(width: 8),
            IconButton.filledTonal(
              tooltip: 'Actualizar',
              onPressed: _loading ? null : _load,
              icon: const Icon(Icons.refresh),
            ),
          ],
        ),
      ),
      Expanded(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
            ? PanelError(message: _error!, onRetry: _load)
            : _items.isEmpty
            ? const EstadoVacio(
                icon: Icons.notifications_none,
                title: 'Todo al dia',
                message: 'No hay notificaciones para mostrar.',
              )
            : RefreshIndicator(
                onRefresh: _load,
                child: ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 6, 16, 24),
                  itemCount: _items.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 8),
                  itemBuilder: (context, index) => TarjetaNotificacion(
                    notification: _items[index],
                    onTap: () => _open(_items[index]),
                  ),
                ),
              ),
      ),
    ],
  );
}
