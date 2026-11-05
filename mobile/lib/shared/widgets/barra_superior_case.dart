import 'package:flutter/material.dart';

import '../../app/aplicacion.dart';

class BarraSuperiorCase extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final bool offline;
  final List<Widget> actions;
  final Widget? leading;

  const BarraSuperiorCase({
    super.key,
    required this.title,
    this.offline = false,
    this.actions = const [],
    this.leading,
  });

  @override
  Size get preferredSize => const Size.fromHeight(64);

  @override
  Widget build(BuildContext context) {
    final tema = ControlTemaMovil.de(context);
    return AppBar(
      toolbarHeight: 64,
      leading: leading,
      titleSpacing: leading == null ? 16 : 0,
      title: Row(
        children: [
          if (leading == null) ...[
            const MarcaGrafica(size: 36),
            const SizedBox(width: 10),
          ],
          Flexible(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                if (offline)
                  const Text(
                    'Modo sin conexion',
                    style: TextStyle(fontSize: 11, color: Color(0xFFFFD180)),
                  ),
              ],
            ),
          ),
        ],
      ),
      actions: [
        IconButton(
          tooltip: tema.modo == ThemeMode.dark
              ? 'Activar modo claro'
              : 'Activar modo oscuro',
          onPressed: tema.alternar,
          icon: Icon(
            tema.modo == ThemeMode.dark
                ? Icons.light_mode_outlined
                : Icons.dark_mode_outlined,
          ),
        ),
        ...actions,
      ],
    );
  }
}
