import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/models/account_models.dart';
import '../../../shared/widgets/content_states.dart';

class ProjectCard extends StatelessWidget {
  final ProjectSummary project;
  final VoidCallback onOpen;
  const ProjectCard({super.key, required this.project, required this.onOpen});

  @override
  Widget build(BuildContext context) => Card(
    child: InkWell(
      borderRadius: BorderRadius.circular(8),
      onTap: onOpen,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                    color: Theme.of(
                      context,
                    ).colorScheme.primary.withValues(alpha: .1),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Icon(
                    Icons.account_tree_outlined,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        project.name,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 4),
                      StatusBadge(label: project.role),
                    ],
                  ),
                ),
                if (project.unreadCount > 0)
                  Badge(label: Text('${project.unreadCount.clamp(0, 99)}')),
                const SizedBox(width: 4),
                const Icon(Icons.chevron_right),
              ],
            ),
            if (project.description?.isNotEmpty == true) ...[
              const SizedBox(height: 12),
              Text(
                project.description!,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: Colors.blueGrey.shade700),
              ),
            ],
            const SizedBox(height: 14),
            Row(
              children: [
                _Metric(
                  icon: Icons.schema_outlined,
                  value: '${project.diagramCount} diagramas',
                ),
                const SizedBox(width: 16),
                _Metric(
                  icon: Icons.group_outlined,
                  value: '${project.memberCount} miembros',
                ),
                const Spacer(),
                Text(
                  DateFormat('dd/MM/yy').format(project.updatedAt),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ],
        ),
      ),
    ),
  );
}

class _Metric extends StatelessWidget {
  final IconData icon;
  final String value;
  const _Metric({required this.icon, required this.value});

  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Icon(icon, size: 16, color: Colors.blueGrey),
      const SizedBox(width: 4),
      Text(value, style: Theme.of(context).textTheme.bodySmall),
    ],
  );
}
