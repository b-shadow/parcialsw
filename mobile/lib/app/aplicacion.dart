import 'dart:async';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../features/controlador_aplicacion.dart';
import '../features/auth/pagina_ingreso.dart';
import '../features/home/estructura_inicio.dart';

const claveTemaMovil = 'case_tema_oscuro';

Future<ThemeMode> cargarModoTemaMovil() async {
  final preferencias = await SharedPreferences.getInstance();
  return preferencias.getBool(claveTemaMovil) == true
      ? ThemeMode.dark
      : ThemeMode.light;
}

Future<void> guardarModoTemaMovil(ThemeMode modo) async {
  final preferencias = await SharedPreferences.getInstance();
  await preferencias.setBool(claveTemaMovil, modo == ThemeMode.dark);
}

class ControlTemaMovil extends InheritedWidget {
  final ThemeMode modo;
  final VoidCallback alternar;

  const ControlTemaMovil({
    super.key,
    required this.modo,
    required this.alternar,
    required super.child,
  });

  static ControlTemaMovil de(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<ControlTemaMovil>()!;

  @override
  bool updateShouldNotify(ControlTemaMovil anterior) => anterior.modo != modo;
}

class AplicacionCaseMovil extends StatefulWidget {
  final ControladorAplicacion controller;
  final ThemeMode modoInicial;
  const AplicacionCaseMovil({
    super.key,
    required this.controller,
    this.modoInicial = ThemeMode.light,
  });

  @override
  State<AplicacionCaseMovil> createState() => _EstadoAplicacionCaseMovil();
}

class _EstadoAplicacionCaseMovil extends State<AplicacionCaseMovil> {
  late ThemeMode _modo;

  @override
  void initState() {
    super.initState();
    _modo = widget.modoInicial;
    unawaited(_cargarTema());
  }

  Future<void> _cargarTema() async {
    try {
      final modo = await cargarModoTemaMovil().timeout(
        const Duration(seconds: 5),
      );
      if (mounted) setState(() => _modo = modo);
    } catch (_) {
      // La preferencia del tema no debe impedir abrir la aplicacion.
    }
  }

  void _alternarTema() {
    final siguiente = _modo == ThemeMode.dark
        ? ThemeMode.light
        : ThemeMode.dark;
    setState(() => _modo = siguiente);
    guardarModoTemaMovil(siguiente);
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) => MaterialApp(
        debugShowCheckedModeBanner: false,
        title: 'CASE Inteligente',
        theme: _theme(Brightness.light),
        darkTheme: _theme(Brightness.dark),
        themeMode: _modo,
        builder: (context, child) => ControlTemaMovil(
          modo: _modo,
          alternar: _alternarTema,
          child: child!,
        ),
        home: widget.controller.restoring
            ? const _PantallaInicio()
            : widget.controller.authenticated
            ? EstructuraInicio(controller: widget.controller)
            : PaginaIngreso(controller: widget.controller),
      ),
    );
  }

  ThemeData _theme(Brightness brillo) {
    const navy = Color(0xFF071426);
    const teal = Color(0xFF087F78);
    const cyan = Color(0xFF15B8AD);
    final oscuro = brillo == Brightness.dark;
    final scheme = ColorScheme.fromSeed(
      seedColor: oscuro ? cyan : teal,
      brightness: brillo,
      primary: oscuro ? cyan : teal,
      secondary: cyan,
      surface: oscuro ? const Color(0xFF172633) : const Color(0xFFF5FAFA),
      error: oscuro ? const Color(0xFFFF7185) : const Color(0xFFBF2438),
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: oscuro
          ? const Color(0xFF101B27)
          : const Color(0xFFF2F8F8),
      appBarTheme: const AppBarTheme(
        backgroundColor: navy,
        foregroundColor: Colors.white,
        centerTitle: false,
        elevation: 0,
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: scheme.surface,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: const BorderRadius.all(Radius.circular(8)),
          side: BorderSide(color: scheme.outlineVariant),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: scheme.surface,
        border: const OutlineInputBorder(
          borderRadius: BorderRadius.all(Radius.circular(6)),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        height: 68,
        backgroundColor: scheme.surface,
        indicatorColor: scheme.primary.withValues(alpha: 0.18),
        labelTextStyle: WidgetStateProperty.all(
          const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
        ),
      ),
    );
  }
}

class _PantallaInicio extends StatelessWidget {
  const _PantallaInicio();

  @override
  Widget build(BuildContext context) => const Scaffold(
    backgroundColor: Color(0xFF071426),
    body: Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          MarcaGrafica(size: 58),
          SizedBox(height: 18),
          Text(
            'CASE Inteligente',
            style: TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.w700,
            ),
          ),
          SizedBox(height: 24),
          CircularProgressIndicator(color: Color(0xFF15B8AD)),
        ],
      ),
    ),
  );
}

class MarcaGrafica extends StatelessWidget {
  final double size;
  const MarcaGrafica({super.key, this.size = 40});

  @override
  Widget build(BuildContext context) => Container(
    width: size,
    height: size,
    decoration: const BoxDecoration(
      color: Color(0xFF0D8D85),
      borderRadius: BorderRadius.all(Radius.circular(8)),
    ),
    child: Icon(
      Icons.view_in_ar_outlined,
      color: Colors.white,
      size: size * .55,
    ),
  );
}
