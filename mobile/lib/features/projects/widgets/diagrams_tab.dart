import 'package:flutter/material.dart';

import '../../../core/models/uml_models.dart';
import '../../../shared/widgets/content_states.dart';
import '../../uml/diagram_viewer_page.dart';
import '../../app_controller.dart';

class DiagramsTab extends StatelessWidget {
  final AppController controller;
  final List<DiagramSummary> diagrams;
  const DiagramsTab({
    super.key,
    required this.controller,
    required this.diagrams,
  });

  @override
  Widget build(BuildContext context) {
    if (diagrams.isEmpty) {
      return const EmptyState(
        icon: Icons.schema_outlined,
        title: 'Sin diagramas',
        message: 'Los diagramas creados en la plataforma apareceran aqui.',
      );
    }
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: diagrams.length,
      separatorBuilder: (_, _) => const SizedBox(height: 8),
      itemBuilder: (context, index) {
        final diagram = diagrams[index];
        return Card(
          child: ListTile(
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) =>
                    DiagramViewerPage(controller: controller, summary: diagram),
              ),
            ),
            leading: const Icon(Icons.account_tree_outlined),
            title: Text(
              diagram.name,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            subtitle: Text(
              '${diagram.classCount} clases | ${diagram.relationshipCount} relaciones',
            ),
            trailing: const Icon(Icons.chevron_right),
          ),
        );
      },
    );
  }
}
