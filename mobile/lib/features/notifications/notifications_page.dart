import 'package:flutter/material.dart';

import '../../core/models/communication_models.dart';
import '../../core/models/uml_models.dart';
import '../../core/network/api_client.dart';
import '../../shared/widgets/content_states.dart';
import '../app_controller.dart';
import '../projects/project_detail_page.dart';
import '../uml/diagram_viewer_page.dart';
import 'widgets/notification_tile.dart';

class NotificationsPage extends StatefulWidget {
  final AppController controller;
  const NotificationsPage({super.key, required this.controller});

  @override
  State<NotificationsPage> createState() => _NotificationsPageState();
}

class _NotificationsPageState extends State<NotificationsPage> {
  List<NotificationItem> _items = const [];
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
    } on ApiException catch (exception) {
      _error = exception.message;
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _open(NotificationItem item) async {
    if (!item.isRead) {
      try {
        await widget.controller.repository.markNotificationRead(
          item.id,
          clicked: true,
        );
        await widget.controller.refreshProjects();
        await _load();
      } on ApiException catch (exception) {
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
            builder: (_) => DiagramViewerPage(
              controller: widget.controller,
              summary: DiagramSummary(
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
      } on ApiException catch (exception) {
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
          builder: (_) => ProjectDetailPage(
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
            ? ErrorPanel(message: _error!, onRetry: _load)
            : _items.isEmpty
            ? const EmptyState(
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
                  itemBuilder: (context, index) => NotificationTile(
                    notification: _items[index],
                    onTap: () => _open(_items[index]),
                  ),
                ),
              ),
      ),
    ],
  );
}
