import 'package:flutter/material.dart';

import '../../shared/widgets/case_top_bar.dart';
import '../app_controller.dart';
import '../notifications/notifications_page.dart';
import '../profile/profile_page.dart';
import '../projects/projects_page.dart';

class HomeShell extends StatefulWidget {
  final AppController controller;
  const HomeShell({super.key, required this.controller});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _index = 0;

  static const _titles = ['Proyectos', 'Notificaciones', 'Perfil'];

  @override
  Widget build(BuildContext context) {
    final pages = [
      ProjectsPage(controller: widget.controller),
      NotificationsPage(controller: widget.controller),
      ProfilePage(controller: widget.controller),
    ];
    return Scaffold(
      appBar: CaseTopBar(
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
