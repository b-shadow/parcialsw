import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../core/models/uml_models.dart';

class UmlRelationshipPainter extends CustomPainter {
  final List<UmlClassNode> classes;
  final List<UmlRelationship> relationships;
  const UmlRelationshipPainter({
    required this.classes,
    required this.relationships,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final nodes = {for (final node in classes) node.id: node};
    for (final relation in relationships) {
      final source = nodes[relation.sourceId];
      final target = nodes[relation.targetId];
      if (source == null || target == null) continue;
      final start = Offset(
        source.x + source.width / 2,
        source.y + source.height / 2,
      );
      final end = Offset(
        target.x + target.width / 2,
        target.y + target.height / 2,
      );
      final paint = Paint()
        ..color = const Color(0xFF35515A)
        ..strokeWidth = 1.7
        ..style = PaintingStyle.stroke;
      if (relation.type == 'dependency' || relation.type == 'implementation') {
        _dashedLine(canvas, start, end, paint);
      } else {
        canvas.drawLine(start, end, paint);
      }
      _ending(canvas, start, end, relation.type, paint);
      _label(canvas, relation, start, end);
    }
  }

  void _dashedLine(Canvas canvas, Offset start, Offset end, Paint paint) {
    final distance = (end - start).distance;
    if (distance == 0) return;
    final direction = (end - start) / distance;
    for (double offset = 0; offset < distance; offset += 12) {
      canvas.drawLine(
        start + direction * offset,
        start + direction * math.min(offset + 7, distance),
        paint,
      );
    }
  }

  void _ending(
    Canvas canvas,
    Offset start,
    Offset end,
    String type,
    Paint paint,
  ) {
    final angle = math.atan2(end.dy - start.dy, end.dx - start.dx);
    const length = 14.0;
    final a = end - Offset(math.cos(angle - .5), math.sin(angle - .5)) * length;
    final b = end - Offset(math.cos(angle + .5), math.sin(angle + .5)) * length;
    final path = Path()
      ..moveTo(end.dx, end.dy)
      ..lineTo(a.dx, a.dy)
      ..lineTo(b.dx, b.dy)
      ..close();
    if (type == 'inheritance' || type == 'implementation') {
      canvas.drawPath(
        path,
        paint
          ..style = PaintingStyle.fill
          ..color = Colors.white,
      );
      canvas.drawPath(
        path,
        paint
          ..style = PaintingStyle.stroke
          ..color = const Color(0xFF35515A),
      );
    } else if (type == 'composition' || type == 'aggregation') {
      canvas.save();
      canvas.translate(start.dx, start.dy);
      canvas.rotate(angle);
      final diamond = Path()
        ..moveTo(0, 0)
        ..lineTo(10, -6)
        ..lineTo(20, 0)
        ..lineTo(10, 6)
        ..close();
      canvas.drawPath(
        diamond,
        paint
          ..style = type == 'composition'
              ? PaintingStyle.fill
              : PaintingStyle.stroke
          ..color = const Color(0xFF35515A),
      );
      canvas.restore();
    } else {
      canvas.drawLine(end, a, paint);
      canvas.drawLine(end, b, paint);
    }
  }

  void _label(
    Canvas canvas,
    UmlRelationship relation,
    Offset start,
    Offset end,
  ) {
    final midpoint = Offset((start.dx + end.dx) / 2, (start.dy + end.dy) / 2);
    final text = [
      if (relation.label?.isNotEmpty == true) relation.label!,
      '${relation.sourceCardinality ?? ''} - ${relation.targetCardinality ?? ''}',
    ].join('\n');
    final painter = TextPainter(
      text: TextSpan(
        text: text,
        style: const TextStyle(
          color: Color(0xFF20383F),
          fontSize: 10,
          backgroundColor: Color(0xFFF2F8F8),
        ),
      ),
      textDirection: TextDirection.ltr,
      textAlign: TextAlign.center,
    )..layout(maxWidth: 120);
    painter.paint(
      canvas,
      midpoint - Offset(painter.width / 2, painter.height / 2),
    );
  }

  @override
  bool shouldRepaint(covariant UmlRelationshipPainter oldDelegate) =>
      oldDelegate.classes != classes ||
      oldDelegate.relationships != relationships;
}
