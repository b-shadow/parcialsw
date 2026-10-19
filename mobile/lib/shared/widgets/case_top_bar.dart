import 'package:flutter/material.dart';

import '../../app/app.dart';

class CaseTopBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final bool offline;
  final List<Widget> actions;
  final Widget? leading;

  const CaseTopBar({
    super.key,
    required this.title,
    this.offline = false,
    this.actions = const [],
    this.leading,
  });

  @override
  Size get preferredSize => const Size.fromHeight(64);

  @override
  Widget build(BuildContext context) => AppBar(
    toolbarHeight: 64,
    leading: leading,
    titleSpacing: leading == null ? 16 : 0,
    title: Row(
      children: [
        if (leading == null) ...[
          const BrandMark(size: 36),
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
    actions: actions,
  );
}
