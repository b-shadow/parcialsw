import 'package:flutter/material.dart';

import '../../core/models/account_models.dart';
import '../../core/realtime/project_realtime.dart';
import '../../shared/widgets/case_top_bar.dart';
import '../../shared/widgets/content_states.dart';
import '../app_controller.dart';
import 'project_detail_controller.dart';
import 'widgets/activity_tab.dart';
import 'widgets/assistant_tab.dart';
import 'widgets/diagrams_tab.dart';
import 'widgets/project_overview_tab.dart';
import 'widgets/versions_tab.dart';

class ProjectDetailPage extends StatefulWidget {
  final AppController controller;
  final ProjectSummary project;
  final int initialTab;
  const ProjectDetailPage({
    super.key,
    required this.controller,
    required this.project,
    this.initialTab = 0,
  });

  @override
  State<ProjectDetailPage> createState() => _ProjectDetailPageState();
}

class _ProjectDetailPageState extends State<ProjectDetailPage> {
  late final ProjectDetailController _controller;

  @override
  void initState() {
    super.initState();
    _controller = ProjectDetailController(
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
      appBar: CaseTopBar(
        title: widget.project.name,
        offline: widget.controller.offline,
        leading: const BackButton(),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 4),
            child: Tooltip(
              message: _realtimeLabel(_controller.realtime.state),
              child: Icon(
                _controller.realtime.state == RealtimeState.connected
                    ? Icons.cloud_done_outlined
                    : Icons.cloud_sync_outlined,
                color: _controller.realtime.state == RealtimeState.connected
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
          const Material(
            color: Colors.white,
            child: TabBar(
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
                ? ErrorPanel(
                    message: _controller.error!,
                    onRetry: _controller.refresh,
                  )
                : TabBarView(
                    children: [
                      ProjectOverviewTab(
                        project: widget.project,
                        generations: _controller.generations,
                      ),
                      DiagramsTab(
                        controller: widget.controller,
                        diagrams: _controller.diagrams,
                      ),
                      ActivityTab(items: _controller.activity),
                      VersionsTab(
                        versions: _controller.versions,
                        restricted: _controller.versionsRestricted,
                      ),
                      AssistantTab(
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

  String _realtimeLabel(RealtimeState state) => switch (state) {
    RealtimeState.connected => 'Actualizacion en tiempo real activa',
    RealtimeState.connecting => 'Conectando',
    RealtimeState.reconnecting => 'Reconectando',
    RealtimeState.disconnected => 'Sin tiempo real',
  };
}
