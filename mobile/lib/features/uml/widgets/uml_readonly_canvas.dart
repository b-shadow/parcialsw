import 'package:flutter/material.dart';

import '../../../core/models/uml_models.dart';
import 'uml_class_card.dart';
import 'uml_relationship_painter.dart';

class UmlReadonlyCanvas extends StatefulWidget {
  final DiagramDetail diagram;
  const UmlReadonlyCanvas({super.key, required this.diagram});

  @override
  State<UmlReadonlyCanvas> createState() => _UmlReadonlyCanvasState();
}

class _UmlReadonlyCanvasState extends State<UmlReadonlyCanvas> {
  final TransformationController _transformation = TransformationController();

  @override
  void dispose() {
    _transformation.dispose();
    super.dispose();
  }

  Size get _canvasSize {
    final maxX = widget.diagram.classes.fold<double>(
      900,
      (value, node) =>
          value > node.x + node.width + 100 ? value : node.x + node.width + 100,
    );
    final maxY = widget.diagram.classes.fold<double>(
      650,
      (value, node) => value > node.y + node.height + 100
          ? value
          : node.y + node.height + 100,
    );
    return Size(maxX.clamp(900, 5000), maxY.clamp(650, 5000));
  }

  void _zoom(double factor) {
    final next = (_transformation.value.getMaxScaleOnAxis() * factor).clamp(
      .3,
      3.5,
    );
    _transformation.value = Matrix4.diagonal3Values(next, next, 1);
  }

  void _reset() => _transformation.value = Matrix4.identity();

  @override
  Widget build(BuildContext context) => Stack(
    children: [
      Positioned.fill(
        child: InteractiveViewer(
          transformationController: _transformation,
          constrained: false,
          minScale: .25,
          maxScale: 4,
          boundaryMargin: const EdgeInsets.all(220),
          child: SizedBox(
            width: _canvasSize.width,
            height: _canvasSize.height,
            child: Stack(
              children: [
                Positioned.fill(
                  child: CustomPaint(
                    painter: UmlRelationshipPainter(
                      classes: widget.diagram.classes,
                      relationships: widget.diagram.relationships,
                    ),
                  ),
                ),
                ...widget.diagram.classes.map(
                  (node) => Positioned(
                    left: node.x,
                    top: node.y,
                    child: UmlClassCard(
                      node: node,
                      onTap: () => _showClass(node),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
      Positioned(
        right: 12,
        bottom: 12,
        child: Card(
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              IconButton(
                tooltip: 'Alejar',
                onPressed: () => _zoom(.8),
                icon: const Icon(Icons.remove),
              ),
              IconButton(
                tooltip: 'Centrar',
                onPressed: _reset,
                icon: const Icon(Icons.center_focus_strong),
              ),
              IconButton(
                tooltip: 'Acercar',
                onPressed: () => _zoom(1.25),
                icon: const Icon(Icons.add),
              ),
              IconButton(
                tooltip: 'Relaciones',
                onPressed: _showRelationships,
                icon: const Icon(Icons.share_outlined),
              ),
            ],
          ),
        ),
      ),
    ],
  );

  void _showClass(UmlClassNode node) {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
          children: [
            Text(
              node.name,
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
            ),
            if (node.stereotype != null) Text('<<${node.stereotype}>>'),
            const SizedBox(height: 14),
            const Text(
              'Atributos',
              style: TextStyle(fontWeight: FontWeight.w700),
            ),
            if (node.attributes.isEmpty) const Text('Sin atributos'),
            ...node.attributes.map(
              (item) => ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.data_object, size: 18),
                title: Text('${item.name}: ${item.dataType}'),
                subtitle: item.multiplicity == null
                    ? null
                    : Text('Multiplicidad ${item.multiplicity}'),
              ),
            ),
            const Divider(),
            const Text(
              'Metodos',
              style: TextStyle(fontWeight: FontWeight.w700),
            ),
            if (node.methods.isEmpty) const Text('Sin metodos'),
            ...node.methods.map(
              (item) => ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.functions, size: 18),
                title: Text('${item.name}(): ${item.returnType ?? 'void'}'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showRelationships() {
    final names = {
      for (final node in widget.diagram.classes) node.id: node.name,
    };
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: ListView.separated(
          shrinkWrap: true,
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
          itemCount: widget.diagram.relationships.length,
          separatorBuilder: (_, _) => const Divider(height: 1),
          itemBuilder: (context, index) {
            final item = widget.diagram.relationships[index];
            return ListTile(
              leading: const Icon(Icons.share_outlined),
              title: Text(
                '${names[item.sourceId] ?? 'Clase'} -> ${names[item.targetId] ?? 'Clase'}',
              ),
              subtitle: Text(
                '${item.type} | ${item.sourceCardinality ?? '-'} a ${item.targetCardinality ?? '-'}',
              ),
            );
          },
        ),
      ),
    );
  }
}
