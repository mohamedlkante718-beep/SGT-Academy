import 'package:dio/dio.dart';
import '../models/my_course.dart';
import '../models/certificate.dart';

class LearningService {
  final Dio _dio;
  LearningService(this._dio);

  Future<List<MyCourse>> myCourses() async {
    final response = await _dio.get('/my-courses/');
    final results = (response.data['results'] as List);
    return results.map((r) => MyCourse.fromJson(r as Map<String, dynamic>)).toList();
  }

  Future<List<ModuleOutline>> courseProgress(String slug) async {
    final response = await _dio.get('/courses/$slug/progress/');
    final modules = response.data as List;
    return modules.map((m) => ModuleOutline.fromJson(m as Map<String, dynamic>)).toList();
  }

  Future<void> completeLesson(String lessonId) async {
    await _dio.post('/lessons/$lessonId/complete/');
  }

  Future<List<SgtCertificate>> myCertificates() async {
    final response = await _dio.get('/certificates/');
    final results = (response.data['results'] as List);
    return results.map((r) => SgtCertificate.fromJson(r as Map<String, dynamic>)).toList();
  }
}
