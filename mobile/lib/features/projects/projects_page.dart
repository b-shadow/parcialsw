import 'package:flutter/material.dart';

import '../../shared/widgets/content_states.dart';
import '../app_controller.dart';
import 'project_detail_page.dart';
import 'widgets/project_card.dart';

class ProjectsPage extends StatefulWidget {
  final AppController controller;
  const ProjectsPage({super.key, required this.controller});

  @override
  State<ProjectsPage> createState() => _ProjectsPageState();
}

class _ProjectsPageState extends State<ProjectsPage> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final projects = widget.controller.projects
        .where((item) => item.name.toLowerCase().contains(_query.toLowerCase()))
        .toList();
    return RefreshIndicator(
      onRefresh: widget.controller.refreshProjects,
      child: CustomScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        slivers: [
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Mis proyectos',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    widget.controller.offline
                        ? 'Mostrando la ultima sincronizacion disponible.'
                        : 'Consulta diagramas, actividad y avances.',
                  ),
                  const SizedBox(height: 14),
                  TextField(
                    onChanged: (value) => setState(() => _query = value.trim()),
                    decoration: const InputDecoration(
                      hintText: 'Buscar proyecto',
                      prefixIcon: Icon(Icons.search),
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (widget.controller.loadingProjects &&
              widget.controller.projects.isEmpty)
            const SliverFillRemaining(
              child: Center(child: CircularProgressIndicator()),
            )
          else if (projects.isEmpty)
            SliverFillRemaining(
              hasScrollBody: false,
              child: EmptyState(
                icon: Icons.folder_off_outlined,
                title: _query.isEmpty ? 'Sin proyectos' : 'Sin coincidencias',
                message: _query.isEmpty
                    ? 'Cuando participes en un proyecto aparecera aqui.'
                    : 'Prueba con otro nombre.',
              ),
            )
          else
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
              sliver: SliverList.separated(
                itemCount: projects.length,
                separatorBuilder: (_, _) => const SizedBox(height: 10),
                itemBuilder: (context, index) {
                  final project = projects[index];
                  return ProjectCard(
                    project: project,
                    onOpen: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => ProjectDetailPage(
                          controller: widget.controller,
                          project: project,
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
        ],
      ),
    );
  }
}
