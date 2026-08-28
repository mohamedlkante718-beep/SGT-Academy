import 'package:flutter/material.dart';
import '../core/theme.dart';
import '../models/my_course.dart';

class CourseProgressCard extends StatelessWidget {
  final MyCourse course;
  final VoidCallback onTap;

  const CourseProgressCard({super.key, required this.course, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(course.courseTitle, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 12),
              ClipRRect(
                borderRadius: BorderRadius.circular(6),
                child: LinearProgressIndicator(
                  value: course.percentComplete / 100,
                  minHeight: 8,
                  backgroundColor: SgtColors.primaryLight,
                  color: SgtColors.primary,
                ),
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('${course.percentComplete}%',
                      style: const TextStyle(color: SgtColors.muted, fontSize: 13)),
                  Text(
                    course.percentComplete >= 100 ? 'Terminée' : 'Continuer',
                    style: const TextStyle(
                      color: SgtColors.primary,
                      fontWeight: FontWeight.w600,
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
