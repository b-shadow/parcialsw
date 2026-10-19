import 'package:flutter/material.dart';

import '../../../core/models/account_models.dart';
import '../../../core/models/project_models.dart';
import '../../../shared/widgets/content_states.dart';

class ProjectOverviewTab extends StatelessWidget {
  final ProjectSummary project;
  final List<GenerationItem> generations;
  const ProjectOverviewTab({
    super.key,
    required this.project,
    required this.generations,
  });

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(16),
    children: [
      Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      project.name,
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                  StatusBadge(label: project.role),
                ],
              ),
              if (project.description?.isNotEmpty == true) ...[
                const SizedBox(height: 10),
                Text(project.description!),
              ],
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: _SummaryMetric(
                      icon: Icons.schema_outlined,
                      value: '${project.diagramCount}',
                      label: 'Diagramas',
                    ),
                  ),
                  Expanded(
                    child: _SummaryMetric(
                      icon: Icons.group_outlined,
                      value: '${project.memberCount}',
                      label: 'Miembros',
                    ),
                  ),
                  Expanded(
                    child: _SummaryMetric(
                      icon: Icons.notifications_outlined,
                      value: '${project.unreadCount}',
                      label: 'Avisos',
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
      const SizedBox(height: 18),
      Text(
        'Generaciones recientes',
        style: Theme.of(
          context,
        ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
      ),
      const SizedBox(height: 8),
      if (generations.isEmpty)
        const Card(
          child: ListTile(
            leading: Icon(Icons.inventory_2_outlined),
            title: Text('Sin generaciones coordinadas'),
            subtitle: Text(
              'La generacion se inicia desde la version de escritorio.',
            ),
          ),
        )
      else
        ...generations
            .take(5)
            .map(
              (item) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Card(
                  child: ListTile(
                    leading: const Icon(Icons.code),
                    title: Text(
                      item.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    subtitle: Text(item.error ?? item.stage),
                    trailing: StatusBadge(
                      label: item.status,
                      color: item.status == 'completed'
                          ? const Color(0xFF16875B)
                          : null,
                    ),
                  ),
                ),
              ),
            ),
    ],
  );
}

class _SummaryMetric extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;
  const _SummaryMetric({
    required this.icon,
    required this.value,
    required this.label,
  });

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Icon(icon, color: Theme.of(context).colorScheme.primary),
      const SizedBox(height: 5),
      Text(
        value,
        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
      ),
      Text(label, style: Theme.of(context).textTheme.bodySmall),
    ],
  );
}
