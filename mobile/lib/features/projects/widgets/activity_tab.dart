import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/models/project_models.dart';
import '../../../shared/widgets/content_states.dart';

class ActivityTab extends StatelessWidget {
  final List<ActivityItem> items;
  const ActivityTab({super.key, required this.items});

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return const EmptyState(
        icon: Icons.history,
        title: 'Sin actividad',
        message: 'Los cambios persistentes del proyecto apareceran aqui.',
      );
    }
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: items.length,
      separatorBuilder: (_, _) => const SizedBox(height: 8),
      itemBuilder: (context, index) {
        final item = items[index];
        return Card(
          child: ListTile(
            leading: CircleAvatar(
              child: Text(
                item.userName.isEmpty ? '?' : item.userName[0].toUpperCase(),
              ),
            ),
            title: Text(_humanize(item.type)),
            subtitle: Text(
              '${item.userName} | ${DateFormat('dd/MM HH:mm').format(item.createdAt)}',
            ),
            trailing: Text(
              '#${item.sequence}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
        );
      },
    );
  }

  String _humanize(String value) => value.toLowerCase().replaceAll('_', ' ');
}
