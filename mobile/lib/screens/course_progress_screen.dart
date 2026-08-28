import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/theme.dart';
import '../providers/providers.dart';

class CourseProgressScreen extends ConsumerWidget {
  final String slug;
  const CourseProgressScreen({super.key, required this.slug});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final modulesAsync = ref.watch(courseProgressProvider(slug));

    return Scaffold(
      appBar: AppBar(title: const Text('Programme de la formation')),
      body: modulesAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Impossible de charger le programme.\n$err')),
        data: (modules) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            for (final module in modules) ...[
              Padding(
                padding: const EdgeInsets.only(bottom: 8, top: 8),
                child: Text('Module ${module.order} — ${module.title}',
                    style: Theme.of(context).textTheme.titleMedium),
              ),
              for (final lesson in module.lessons)
                Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    leading: Icon(
                      lesson.isCompleted ? Icons.check_circle : Icons.play_circle_outline,
                      color: lesson.isCompleted ? SgtColors.primary : SgtColors.muted,
                    ),
                    title: Text(lesson.title),
                    subtitle: Text('${(lesson.durationSeconds / 60).round()} min'
                        '${lesson.isPreview ? ' · Aperçu gratuit' : ''}'),
                    trailing: lesson.isCompleted
                        ? null
                        : TextButton(
                            onPressed: () async {
                              await ref.read(learningServiceProvider).completeLesson(lesson.id);
                              ref.invalidate(courseProgressProvider(slug));
                              ref.invalidate(myCoursesProvider);
                            },
                            child: const Text('Terminer'),
                          ),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}
