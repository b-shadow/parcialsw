import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../core/models/modelos_uml.dart';

class PintorRelacionesUML extends CustomPainter {
  final List<NodoClaseUML> classes;
  final List<RelacionUML> relationships;
  final Color color;
  final Color fondo;

  const PintorRelacionesUML({
    required this.classes,
    required this.relationships,
    this.color = const Color(0xFF35515A),
    this.fondo = const Color(0xFFF2F8F8),
  });

  /// Calcula puntos sobre el borde de cada clase, no en su centro.
  static (Offset, Offset)? puntosRelacion(
    NodoClaseUML origen,
    NodoClaseUML destino,
  ) {
    final centroOrigen = Offset(
      origen.x + origen.width / 2,
      origen.y + origen.height / 2,
    );
    final centroDestino = Offset(
      destino.x + destino.width / 2,
      destino.y + destino.height / 2,
    );
    final vector = centroDestino - centroOrigen;
    if (vector.distance < 1) return null;
    Offset borde(Offset centro, double ancho, double alto, Offset direccion) {
      final escalaX = direccion.dx == 0
          ? double.infinity
          : ancho / 2 / direccion.dx.abs();
      final escalaY = direccion.dy == 0
          ? double.infinity
          : alto / 2 / direccion.dy.abs();
      return centro + direccion * math.min(escalaX, escalaY);
    }

    return (
      borde(centroOrigen, origen.width, origen.height, vector),
      borde(centroDestino, destino.width, destino.height, -vector),
    );
  }

  @override
  void paint(Canvas canvas, Size size) {
    final nodos = {for (final nodo in classes) nodo.id: nodo};
    for (final relacion in relationships) {
      final origen = nodos[relacion.sourceId];
      final destino = nodos[relacion.targetId];
      if (origen == null || destino == null) continue;
      final puntos = puntosRelacion(origen, destino);
      if (puntos == null) continue;
      final (inicio, fin) = puntos;
      final vector = fin - inicio;
      final distancia = vector.distance;
      if (distancia < 2) continue;
      final direccion = vector / distancia;
      final tipo = relacion.type.toLowerCase();
      final diamante = tipo == 'composition' || tipo == 'aggregation';
      final triangulo =
          tipo == 'inheritance' ||
          tipo == 'generalization' ||
          tipo == 'implementation' ||
          tipo == 'realization';
      final rayada =
          tipo == 'dependency' ||
          tipo == 'implementation' ||
          tipo == 'realization';
      final inicioLinea = diamante
          ? inicio + direccion * math.min(20, distancia / 3)
          : inicio;
      final finLinea = triangulo
          ? fin - direccion * math.min(14, distancia / 3)
          : fin;
      final trazo = Paint()
        ..color = color
        ..strokeWidth = 1.7
        ..style = PaintingStyle.stroke;
      if (rayada) {
        _lineaRayada(canvas, inicioLinea, finLinea, trazo);
      } else {
        canvas.drawLine(inicioLinea, finLinea, trazo);
      }
      if (diamante) {
        _diamante(canvas, inicio, direccion, tipo == 'composition', trazo);
      } else if (triangulo) {
        _triangulo(canvas, fin, direccion, trazo);
      } else if (tipo == 'association' ||
          tipo == 'association_class' ||
          tipo == 'dependency') {
        _flecha(canvas, fin, direccion, trazo);
      }
      if (relacion.label?.isNotEmpty == true) {
        _etiqueta(canvas, relacion.label!, Offset.lerp(inicio, fin, .5)!, -15);
      }
      if (relacion.sourceCardinality?.isNotEmpty == true) {
        _etiqueta(
          canvas,
          relacion.sourceCardinality!,
          inicio + direccion * 25,
          9,
        );
      }
      if (relacion.targetCardinality?.isNotEmpty == true) {
        _etiqueta(canvas, relacion.targetCardinality!, fin - direccion * 25, 9);
      }
    }
  }

  void _lineaRayada(Canvas canvas, Offset inicio, Offset fin, Paint trazo) {
    final distancia = (fin - inicio).distance;
    if (distancia < 1) return;
    final direccion = (fin - inicio) / distancia;
    for (double avance = 0; avance < distancia; avance += 12) {
      canvas.drawLine(
        inicio + direccion * avance,
        inicio + direccion * math.min(avance + 7, distancia),
        trazo,
      );
    }
  }

  void _triangulo(Canvas canvas, Offset punta, Offset direccion, Paint trazo) {
    final normal = Offset(-direccion.dy, direccion.dx);
    final base = punta - direccion * 14;
    final figura = Path()
      ..moveTo(punta.dx, punta.dy)
      ..lineTo(base.dx + normal.dx * 8, base.dy + normal.dy * 8)
      ..lineTo(base.dx - normal.dx * 8, base.dy - normal.dy * 8)
      ..close();
    canvas.drawPath(figura, Paint()..color = fondo);
    canvas.drawPath(figura, trazo);
  }

  void _diamante(
    Canvas canvas,
    Offset inicio,
    Offset direccion,
    bool lleno,
    Paint trazo,
  ) {
    final normal = Offset(-direccion.dy, direccion.dx);
    final medio = inicio + direccion * 10;
    final punta = inicio + direccion * 20;
    final figura = Path()
      ..moveTo(inicio.dx, inicio.dy)
      ..lineTo(medio.dx + normal.dx * 6, medio.dy + normal.dy * 6)
      ..lineTo(punta.dx, punta.dy)
      ..lineTo(medio.dx - normal.dx * 6, medio.dy - normal.dy * 6)
      ..close();
    canvas.drawPath(figura, Paint()..color = lleno ? color : fondo);
    canvas.drawPath(figura, trazo);
  }

  void _flecha(Canvas canvas, Offset punta, Offset direccion, Paint trazo) {
    final normal = Offset(-direccion.dy, direccion.dx);
    final base = punta - direccion * 11;
    canvas.drawLine(punta, base + normal * 6, trazo);
    canvas.drawLine(punta, base - normal * 6, trazo);
  }

  void _etiqueta(
    Canvas canvas,
    String texto,
    Offset posicion,
    double desplazamientoY,
  ) {
    final pintor = TextPainter(
      text: TextSpan(
        text: texto,
        style: TextStyle(color: color, fontSize: 10, backgroundColor: fondo),
      ),
      textDirection: TextDirection.ltr,
      textAlign: TextAlign.center,
    )..layout(maxWidth: 120);
    pintor.paint(
      canvas,
      posicion - Offset(pintor.width / 2, pintor.height / 2 - desplazamientoY),
    );
  }

  @override
  bool shouldRepaint(covariant PintorRelacionesUML anterior) =>
      anterior.classes != classes ||
      anterior.relationships != relationships ||
      anterior.color != color ||
      anterior.fondo != fondo;
}
