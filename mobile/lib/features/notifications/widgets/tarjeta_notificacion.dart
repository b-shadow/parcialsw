import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/models/modelos_comunicacion.dart';

class TarjetaNotificacion extends StatelessWidget {
  final ElementoNotificacion notification;
  final VoidCallback onTap;
  const TarjetaNotificacion({
    super.key,
    required this.notification,
    required this.onTap,
  });

  Color _color() => switch (notification.severity) {
    'success' => const Color(0xFF16875B),
    'warning' => const Color(0xFFA85D00),
    'error' => const Color(0xFFBF2438),
    _ => const Color(0xFF087F78),
  };

  @override
  Widget build(BuildContext context) => Card(
    color: notification.isRead
        ? Theme.of(context).colorScheme.surface
        : Theme.of(context).colorScheme.primaryContainer,
    child: ListTile(
      onTap: onTap,
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      leading: Container(
        width: 38,
        height: 38,
        decoration: BoxDecoration(
          color: _color().withValues(alpha: .12),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Icon(Icons.notifications_outlined, color: _color()),
      ),
      title: Text(
        notification.title,
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(
          fontWeight: notification.isRead ? FontWeight.w600 : FontWeight.w800,
        ),
      ),
      subtitle: Padding(
        padding: const EdgeInsets.only(top: 5),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              notification.body,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 5),
            Text(
              DateFormat('dd/MM/yyyy HH:mm').format(notification.occurredAt),
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    ),
  );
}
