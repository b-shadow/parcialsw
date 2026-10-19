import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/models/project_models.dart';
import '../../../shared/widgets/content_states.dart';

class VersionsTab extends StatelessWidget {
  final List<VersionItem> versions;
  final bool restricted;
  const VersionsTab({
    super.key,
    required this.versions,
    required this.restricted,
  });

  @override
  Widget build(BuildContext context) {
    if (restricted) {
      return const EmptyState(
        icon: Icons.lock_outline,
        title: 'Acceso restringido',
        message:
            'Solo el propietario u organizador puede consultar versiones guardadas.',
      );
    }
    if (versions.isEmpty) {
      return const EmptyState(
        icon: Icons.bookmarks_outlined,
        title: 'Sin versiones guardadas',
        message: 'Las versiones se crean y restauran desde escritorio.',
      );
    }
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: versions.length,
      separatorBuilder: (_, _) => const SizedBox(height: 8),
      itemBuilder: (context, index) {
        final version = versions[index];
        return Card(
          child: ListTile(
            leading: CircleAvatar(child: Text('v${version.number}')),
            title: Text(version.name),
            subtitle: Text(
              '${version.createdBy ?? 'Usuario'} | ${DateFormat('dd/MM/yyyy HH:mm').format(version.createdAt)}${version.description == null ? '' : '\n${version.description}'}',
            ),
            isThreeLine: version.description != null,
          ),
        );
      },
    );
  }
}
