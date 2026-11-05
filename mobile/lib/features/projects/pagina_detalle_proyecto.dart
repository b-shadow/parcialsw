import 'package:flutter/material.dart';

import '../../core/models/modelos_cuenta.dart';
import '../../core/realtime/tiempo_real_proyecto.dart';
import '../../shared/widgets/barra_superior_case.dart';
import '../../shared/widgets/estados_contenido.dart';
import '../controlador_aplicacion.dart';
import 'controlador_detalle_proyecto.dart';
import 'widgets/pestana_actividad.dart';
import 'widgets/pestana_asistente.dart';
import 'widgets/pestana_diagramas.dart';
import 'widgets/pestana_resumen_proyecto.dart';
import 'widgets/pestana_versiones.dart';

class PaginaDetalleProyecto extends StatefulWidget {
  final ControladorAplicacion controller;
  final ResumenProyecto project;
  final int initialTab;
  const PaginaDetalleProyecto({
    super.key,
    required this.controller,
    required this.project,
    this.initialTab = 0,
  });

  @override
  State<PaginaDetalleProyecto> createState() => _EstadoPaginaDetalleProyecto();
}

class _EstadoPaginaDetalleProyecto extends State<PaginaDetalleProyecto> {
  late final ControladorDetalleProyecto _controller;

  @override
  void initState() {
    super.initState();
    _controller = ControladorDetalleProyecto(
      app: widget.controller,
      project: widget.project,
    )..addListener(_updated);
    _controller.initialize();
  }

  void _updated() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _controller
      ..removeListener(_updated)
      ..dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => DefaultTabController(
    length: 5,
    initialIndex: widget.initialTab.clamp(0, 4).toInt(),
    child: Scaffold(
      appBar: BarraSuperiorCase(
        title: widget.project.name,
        offline: widget.controller.offline,
        leading: const BackButton(),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 4),
            child: Tooltip(
              message: _realtimeLabel(_controller.realtime.state),
              child: Icon(
                _controller.realtime.state == EstadoTiempoReal.connected
                    ? Icons.cloud_done_outlined
                    : Icons.cloud_sync_outlined,
                color: _controller.realtime.state == EstadoTiempoReal.connected
                    ? const Color(0xFF80CBC4)
                    : const Color(0xFFFFD180),
              ),
            ),
          ),
          IconButton(
            tooltip: 'Actualizar proyecto',
            onPressed: _controller.loading ? null : _controller.refresh,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: Column(
        children: [
          Material(
            color: Theme.of(context).colorScheme.surface,
            child: const TabBar(
              isScrollable: true,
              tabs: [
                Tab(text: 'Resumen'),
                Tab(text: 'Diagramas'),
                Tab(text: 'Actividad'),
                Tab(text: 'Versiones'),
                Tab(text: 'IA'),
              ],
            ),
          ),
          Expanded(
            child: _controller.loading && _controller.diagrams.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : _controller.error != null
                ? PanelError(
                    message: _controller.error!,
                    onRetry: _controller.refresh,
                  )
                : TabBarView(
                    children: [
                      PestanaResumenProyecto(
                        project: widget.project,
                        generations: _controller.generations,
                      ),
                      PestanaDiagramas(
                        controller: widget.controller,
                        diagrams: _controller.diagrams,
                      ),
                      PestanaActividad(items: _controller.activity),
                      PestanaVersiones(
                        versions: _controller.versions,
                        restricted: _controller.versionsRestricted,
                      ),
                      PestanaAsistente(
                        messages: _controller.messages,
                        actions: _controller.actions,
                        diagrams: _controller.diagrams,
                        sending: _controller.sendingMessage,
                        onSend: _controller.sendMessage,
                      ),
                    ],
                  ),
          ),
        ],
      ),
    ),
  );

  String _realtimeLabel(EstadoTiempoReal state) => switch (state) {
    EstadoTiempoReal.connected => 'Actualizacion en tiempo real activa',
    EstadoTiempoReal.connecting => 'Conectando',
    EstadoTiempoReal.reconnecting => 'Reconectando',
    EstadoTiempoReal.disconnected => 'Sin tiempo real',
  };
}
