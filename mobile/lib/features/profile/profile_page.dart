import 'package:flutter/material.dart';

import '../../shared/widgets/content_states.dart';
import '../app_controller.dart';
import 'change_password_dialog.dart';

class ProfilePage extends StatelessWidget {
  final AppController controller;
  const ProfilePage({super.key, required this.controller});

  @override
  Widget build(BuildContext context) {
    final profile = controller.profile!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 30,
                  backgroundColor: Theme.of(context).colorScheme.primary,
                  child: Text(
                    profile.fullName.isEmpty
                        ? '?'
                        : profile.fullName[0].toUpperCase(),
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        profile.fullName,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(profile.email, overflow: TextOverflow.ellipsis),
                      const SizedBox(height: 7),
                      Wrap(
                        spacing: 6,
                        runSpacing: 6,
                        children: profile.roles
                            .map((role) => StatusBadge(label: role))
                            .toList(),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        Card(
          child: Column(
            children: [
              ListTile(
                leading: const Icon(Icons.password_outlined),
                title: const Text('Cambiar contrasena'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () async {
                  final changed = await showDialog<bool>(
                    context: context,
                    builder: (_) =>
                        ChangePasswordDialog(repository: controller.repository),
                  );
                  if (changed == true && context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Contrasena actualizada.')),
                    );
                  }
                },
              ),
              const Divider(height: 1),
              ListTile(
                leading: const Icon(Icons.logout, color: Color(0xFFBF2438)),
                title: const Text('Cerrar sesion'),
                onTap: () => _confirmLogout(context),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),
        Text(
          'La aplicacion movil permite consultar. La edicion UML, restauracion de versiones y generacion se realizan en escritorio.',
          style: Theme.of(context).textTheme.bodySmall,
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Future<void> _confirmLogout(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cerrar sesion'),
        content: const Text(
          'Se eliminara tambien la informacion almacenada sin conexion.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Cerrar sesion'),
          ),
        ],
      ),
    );
    if (confirmed == true) await controller.logout();
  }
}
