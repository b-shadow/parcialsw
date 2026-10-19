import 'package:flutter/material.dart';

import '../features/app_controller.dart';
import '../features/auth/login_page.dart';
import '../features/home/home_shell.dart';

class CaseMobileApp extends StatelessWidget {
  final AppController controller;
  const CaseMobileApp({super.key, required this.controller});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) => MaterialApp(
        debugShowCheckedModeBanner: false,
        title: 'CASE Inteligente',
        theme: _theme(),
        home: controller.restoring
            ? const _LaunchScreen()
            : controller.authenticated
            ? HomeShell(controller: controller)
            : LoginPage(controller: controller),
      ),
    );
  }

  ThemeData _theme() {
    const navy = Color(0xFF071426);
    const teal = Color(0xFF087F78);
    const cyan = Color(0xFF15B8AD);
    final scheme = ColorScheme.fromSeed(
      seedColor: teal,
      brightness: Brightness.light,
      primary: teal,
      secondary: cyan,
      surface: const Color(0xFFF5FAFA),
      error: const Color(0xFFBF2438),
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: const Color(0xFFF2F8F8),
      appBarTheme: const AppBarTheme(
        backgroundColor: navy,
        foregroundColor: Colors.white,
        centerTitle: false,
        elevation: 0,
      ),
      cardTheme: const CardThemeData(
        elevation: 0,
        color: Colors.white,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(8)),
          side: BorderSide(color: Color(0xFFD9E5E7)),
        ),
      ),
      inputDecorationTheme: const InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.all(Radius.circular(6)),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        height: 68,
        backgroundColor: Colors.white,
        indicatorColor: teal.withValues(alpha: 0.14),
        labelTextStyle: WidgetStateProperty.all(
          const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
        ),
      ),
    );
  }
}

class _LaunchScreen extends StatelessWidget {
  const _LaunchScreen();

  @override
  Widget build(BuildContext context) => const Scaffold(
    backgroundColor: Color(0xFF071426),
    body: Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          BrandMark(size: 58),
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

class BrandMark extends StatelessWidget {
  final double size;
  const BrandMark({super.key, this.size = 40});

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
