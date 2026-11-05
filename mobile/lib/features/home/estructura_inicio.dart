import 'package:flutter/material.dart';

import '../../shared/widgets/barra_superior_case.dart';
import '../controlador_aplicacion.dart';
import '../notifications/pagina_notificaciones.dart';
import '../profile/pagina_perfil.dart';
import '../projects/pagina_proyectos.dart';

class EstructuraInicio extends StatefulWidget {
  final ControladorAplicacion controller;
  const EstructuraInicio({super.key, required this.controller});

  @override
  State<EstructuraInicio> createState() => _EstadoEstructuraInicio();
}

class _EstadoEstructuraInicio extends State<EstructuraInicio> {
  int _index = 0;

  static const _titles = ['Proyectos', 'Notificaciones', 'Perfil'];

  @override
  Widget build(BuildContext context) {
    final pages = [
      PaginaProyectos(controller: widget.controller),
      PaginaNotificaciones(controller: widget.controller),
      PaginaPerfil(controller: widget.controller),
    ];
    return Scaffold(
      appBar: BarraSuperiorCase(
        title: _titles[_index],
        offline: widget.controller.offline,
        actions: [
          if (_index == 0)
            IconButton(
              tooltip: 'Actualizar proyectos',
              onPressed: widget.controller.loadingProjects
                  ? null
                  : widget.controller.refreshProjects,
              icon: const Icon(Icons.refresh),
            ),
        ],
      ),
      body: IndexedStack(index: _index, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        destinations: [
          const NavigationDestination(
            icon: Icon(Icons.folder_outlined),
            selectedIcon: Icon(Icons.folder),
            label: 'Proyectos',
          ),
          NavigationDestination(
            icon: Badge(
              isLabelVisible: widget.controller.unreadCount > 0,
              label: Text('${widget.controller.unreadCount.clamp(0, 99)}'),
              child: const Icon(Icons.notifications_outlined),
            ),
            selectedIcon: Badge(
              isLabelVisible: widget.controller.unreadCount > 0,
              label: Text('${widget.controller.unreadCount.clamp(0, 99)}'),
              child: const Icon(Icons.notifications),
            ),
            label: 'Avisos',
          ),
          const NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: 'Perfil',
          ),
        ],
      ),
    );
  }
}
