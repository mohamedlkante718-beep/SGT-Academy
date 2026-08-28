import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../core/theme.dart';
import '../providers/providers.dart';
import '../widgets/course_progress_card.dart';
import '../widgets/logo_mark.dart';

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  int _tabIndex = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            LogoMark(size: 28),
            SizedBox(width: 10),
            Text('SGT Academy'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Déconnexion',
            onPressed: () async {
              await ref.read(authServiceProvider).logout();
              ref.invalidate(authStateProvider);
              if (context.mounted) context.go('/login');
            },
          ),
        ],
      ),
      body: IndexedStack(
        index: _tabIndex,
        children: const [_MyCoursesTab(), _CertificatesTab()],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tabIndex,
        onDestinationSelected: (i) => setState(() => _tabIndex = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.school_outlined), label: 'Mes formations'),
          NavigationDestination(icon: Icon(Icons.workspace_premium_outlined), label: 'Certificats'),
        ],
      ),
    );
  }
}

class _MyCoursesTab extends ConsumerWidget {
  const _MyCoursesTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final coursesAsync = ref.watch(myCoursesProvider);

    return coursesAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, _) => Center(child: Text('Impossible de charger vos formations.\n$err')),
      data: (courses) {
        if (courses.isEmpty) {
          return const Center(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Text(
                "Vous n'avez pas encore de formation. Achetez-en une depuis le site pour la retrouver ici.",
                textAlign: TextAlign.center,
                style: TextStyle(color: SgtColors.muted),
              ),
            ),
          );
        }
        return RefreshIndicator(
          onRefresh: () async => ref.invalidate(myCoursesProvider),
          child: ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: courses.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final course = courses[index];
              return CourseProgressCard(
                course: course,
                onTap: () => context.push('/course/${course.courseSlug}'),
              );
            },
          ),
        );
      },
    );
  }
}

class _CertificatesTab extends ConsumerWidget {
  const _CertificatesTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final certsAsync = ref.watch(myCertificatesProvider);

    return certsAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, _) => Center(child: Text('Impossible de charger vos certificats.\n$err')),
      data: (certificates) {
        if (certificates.isEmpty) {
          return const Center(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Text(
                "Aucun certificat pour l'instant — terminez une formation et réussissez son examen final pour en obtenir un.",
                textAlign: TextAlign.center,
                style: TextStyle(color: SgtColors.muted),
              ),
            ),
          );
        }
        return ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: certificates.length,
          separatorBuilder: (_, __) => const SizedBox(height: 12),
          itemBuilder: (context, index) {
            final cert = certificates[index];
            return Card(
              child: ListTile(
                leading: const Icon(Icons.workspace_premium, color: SgtColors.primary),
                title: Text(cert.courseTitle),
                subtitle: Text('Code : ${cert.code}'),
              ),
            );
          },
        );
      },
    );
  }
}
