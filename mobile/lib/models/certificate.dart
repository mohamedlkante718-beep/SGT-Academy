class SgtCertificate {
  final String id;
  final String code;
  final String courseTitle;
  final String learnerName;
  final DateTime issuedAt;

  SgtCertificate({
    required this.id,
    required this.code,
    required this.courseTitle,
    required this.learnerName,
    required this.issuedAt,
  });

  factory SgtCertificate.fromJson(Map<String, dynamic> json) {
    return SgtCertificate(
      id: json['id'] as String,
      code: json['code'] as String,
      courseTitle: json['course_title_snapshot'] as String,
      learnerName: json['learner_name_snapshot'] as String,
      issuedAt: DateTime.parse(json['issued_at'] as String),
    );
  }
}
