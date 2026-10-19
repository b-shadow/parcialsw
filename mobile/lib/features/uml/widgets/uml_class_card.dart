import 'package:flutter/material.dart';

import '../../../core/models/uml_models.dart';

class UmlClassCard extends StatelessWidget {
  final UmlClassNode node;
  final VoidCallback onTap;
  const UmlClassCard({super.key, required this.node, required this.onTap});

  @override
  Widget build(BuildContext context) => Material(
    color: const Color(0xFFFFF9F0),
    shape: RoundedRectangleBorder(
      side: const BorderSide(color: Color(0xFF7C6C58), width: 1.2),
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
              color: const Color(0xFFF0E4D4),
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
              child: Column(
                children: [
                  if (node.stereotype != null)
                    Text(
                      '<<${node.stereotype}>>',
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
            const Divider(height: 1, color: Color(0xFF7C6C58)),
            Expanded(
              child: SingleChildScrollView(
                physics: const NeverScrollableScrollPhysics(),
                padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 5),
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
                    if (node.attributes.isNotEmpty && node.methods.isNotEmpty)
                      const Divider(height: 10, color: Color(0xFFB7A994)),
                    ...node.methods.map(
                      (item) => Text(
                        '${_visibility(item.visibility)} ${item.name}(): ${item.returnType ?? 'void'}',
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

  String _visibility(String value) => switch (value) {
    'private' => '-',
    'protected' => '#',
    'package' => '~',
    _ => '+',
  };
}
