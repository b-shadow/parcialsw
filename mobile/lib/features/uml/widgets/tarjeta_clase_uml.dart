import 'package:flutter/material.dart';

import '../../../core/models/modelos_uml.dart';

class TarjetaClaseUML extends StatelessWidget {
  final NodoClaseUML node;
  final VoidCallback onTap;
  const TarjetaClaseUML({super.key, required this.node, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final colores = Theme.of(context).colorScheme;
    final oscuro = Theme.of(context).brightness == Brightness.dark;
    final borde = oscuro ? colores.outline : const Color(0xFF7C6C58);
    return Material(
      color: oscuro ? colores.surface : const Color(0xFFFFF9F0),
      shape: RoundedRectangleBorder(
        side: BorderSide(color: borde, width: 1.2),
        borderRadius: BorderRadius.circular(4),
      ),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: SizedBox(
          width: node.width,
          height: node.height,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(
                color: oscuro
                    ? colores.surfaceContainerHigh
                    : const Color(0xFFF0E4D4),
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
                child: Column(
                  children: [
                    if (node.stereotype != null || node.elementType != 'class')
                      Text(
                        '<<${node.stereotype ?? node.elementType}>>',
                        style: const TextStyle(fontSize: 10),
                      ),
                    Text(
                      node.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontWeight: FontWeight.w800,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              Divider(height: 1, color: borde),
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 7,
                    vertical: 5,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      ...node.attributes.map(
                        (item) => Text(
                          '${_visibility(item.visibility)} ${item.name}: ${item.dataType}',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 11),
                        ),
                      ),
                      Divider(height: 10, color: borde.withValues(alpha: .45)),
                      ...node.methods.map(
                        (item) => Text(
                          '${_visibility(item.visibility)} ${item.firma}',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 11),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _visibility(String value) => switch (value) {
    'private' => '-',
    'protected' => '#',
    'package' => '~',
    _ => '+',
  };
}
