import 'package:case_inteligente_mobile/app/aplicacion.dart';
import 'package:case_inteligente_mobile/core/models/modelos_uml.dart';
import 'package:case_inteligente_mobile/features/uml/widgets/lienzo_uml_lectura.dart';
import 'package:case_inteligente_mobile/features/uml/widgets/pintor_relaciones_uml.dart';
import 'package:case_inteligente_mobile/shared/widgets/barra_superior_case.dart';
import 'package:case_inteligente_mobile/shared/widgets/estados_contenido.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  testWidgets('el estado vacio usa una accion reutilizable', (tester) async {
    var retried = false;
    await tester.pumpWidget(
      MaterialApp(
        home: EstadoVacio(
          icon: Icons.folder_off_outlined,
          title: 'Sin datos',
          message: 'No existen elementos.',
          onRetry: () => retried = true,
        ),
      ),
    );

    expect(find.text('Sin datos'), findsOneWidget);
    await tester.tap(find.text('Reintentar'));
    expect(retried, isTrue);
  });

  testWidgets('el lienzo UML muestra clases pero no controles de edicion', (
    tester,
  ) async {
    const diagram = DetalleDiagrama(
      id: 'diagram-1',
      name: 'Ventas',
      logicalVersion: 2,
      canEdit: false,
      classes: [
        NodoClaseUML(
          id: 'class-1',
          name: 'Cliente',
          x: 20,
          y: 20,
          width: 230,
          height: 130,
          attributes: [AtributoUML('id', 'UUID', 'private', null)],
          methods: [],
        ),
      ],
      relationships: [],
    );
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: LienzoUMLLectura(diagram: diagram)),
      ),
    );

    expect(find.text('Cliente'), findsOneWidget);
    expect(find.byIcon(Icons.add), findsOneWidget);
    expect(find.text('Guardar'), findsNothing);
    expect(find.text('Eliminar'), findsNothing);
  });

  test('las relaciones terminan sobre el borde de las clases', () {
    const origen = NodoClaseUML(
      id: 'a',
      name: 'Venta',
      x: 20,
      y: 20,
      width: 100,
      height: 80,
      attributes: [],
      methods: [],
    );
    const destino = NodoClaseUML(
      id: 'b',
      name: 'Producto',
      x: 320,
      y: 20,
      width: 100,
      height: 80,
      attributes: [],
      methods: [],
    );
    final puntos = PintorRelacionesUML.puntosRelacion(origen, destino);
    expect(puntos, isNotNull);
    expect(puntos!.$1.dx, 120);
    expect(puntos.$2.dx, 320);
    expect(puntos.$1.dy, 60);
    expect(puntos.$2.dy, 60);
  });

  testWidgets('la barra superior ofrece alternar el tema', (tester) async {
    var cambios = 0;
    await tester.pumpWidget(
      MaterialApp(
        builder: (context, child) => ControlTemaMovil(
          modo: ThemeMode.light,
          alternar: () => cambios++,
          child: child!,
        ),
        home: const Scaffold(appBar: BarraSuperiorCase(title: 'Proyectos')),
      ),
    );
    expect(find.byTooltip('Activar modo oscuro'), findsOneWidget);
    await tester.tap(find.byTooltip('Activar modo oscuro'));
    expect(cambios, 1);
  });

  test('la preferencia del tema se conserva entre lecturas', () async {
    SharedPreferences.setMockInitialValues({});
    expect(await cargarModoTemaMovil(), ThemeMode.light);
    await guardarModoTemaMovil(ThemeMode.dark);
    expect(await cargarModoTemaMovil(), ThemeMode.dark);
    await guardarModoTemaMovil(ThemeMode.light);
    expect(await cargarModoTemaMovil(), ThemeMode.light);
  });
}
