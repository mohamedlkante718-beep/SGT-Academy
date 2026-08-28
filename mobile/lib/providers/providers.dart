import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../models/certificate.dart';
import '../models/my_course.dart';
import '../services/auth_service.dart';
import '../services/learning_service.dart';

final dioProvider = Provider<Dio>((ref) => buildApiClient());

final authServiceProvider = Provider<AuthService>((ref) => AuthService(ref.watch(dioProvider)));

final learningServiceProvider =
    Provider<LearningService>((ref) => LearningService(ref.watch(dioProvider)));

/// Statut d'authentification courant, vérifié au démarrage puis mis à jour
/// après connexion/déconnexion.
final authStateProvider = FutureProvider<bool>((ref) async {
  final token = await TokenStorage.readAccess();
  return token != null;
});

final myCoursesProvider = FutureProvider.autoDispose<List<MyCourse>>((ref) {
  return ref.watch(learningServiceProvider).myCourses();
});

final myCertificatesProvider = FutureProvider.autoDispose<List<SgtCertificate>>((ref) {
  return ref.watch(learningServiceProvider).myCertificates();
});

final courseProgressProvider =
    FutureProvider.autoDispose.family<List<ModuleOutline>, String>((ref, slug) {
  return ref.watch(learningServiceProvider).courseProgress(slug);
});
