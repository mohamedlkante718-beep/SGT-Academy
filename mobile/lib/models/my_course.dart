class MyCourse {
  final String courseSlug;
  final String courseTitle;
  final int percentComplete;
  final String? lastLessonId;

  MyCourse({
    required this.courseSlug,
    required this.courseTitle,
    required this.percentComplete,
    required this.lastLessonId,
  });

  factory MyCourse.fromJson(Map<String, dynamic> json) {
    return MyCourse(
      courseSlug: json['course_slug'] as String,
      courseTitle: json['course_title'] as String,
      percentComplete: json['percent_complete'] as int,
      lastLessonId: json['last_lesson_id'] as String?,
    );
  }
}

class LessonOutline {
  final String id;
  final String title;
  final int order;
  final int durationSeconds;
  final bool isPreview;
  final String status;

  LessonOutline({
    required this.id,
    required this.title,
    required this.order,
    required this.durationSeconds,
    required this.isPreview,
    required this.status,
  });

  factory LessonOutline.fromJson(Map<String, dynamic> json) {
    return LessonOutline(
      id: json['id'] as String,
      title: json['title'] as String,
      order: json['order'] as int,
      durationSeconds: json['duration_seconds'] as int,
      isPreview: json['is_preview'] as bool,
      status: json['status'] as String,
    );
  }

  bool get isCompleted => status == 'COMPLETED';
}

class ModuleOutline {
  final String id;
  final String title;
  final int order;
  final List<LessonOutline> lessons;

  ModuleOutline({
    required this.id,
    required this.title,
    required this.order,
    required this.lessons,
  });

  factory ModuleOutline.fromJson(Map<String, dynamic> json) {
    return ModuleOutline(
      id: json['id'] as String,
      title: json['title'] as String,
      order: json['order'] as int,
      lessons: (json['lessons'] as List)
          .map((l) => LessonOutline.fromJson(l as Map<String, dynamic>))
          .toList(),
    );
  }
}
