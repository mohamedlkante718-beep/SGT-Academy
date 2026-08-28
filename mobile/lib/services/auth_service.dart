import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../models/user.dart';

class AuthException implements Exception {
  final String message;
  AuthException(this.message);
}

class AuthService {
  final Dio _dio;
  AuthService(this._dio);

  Future<void> login(String email, String password) async {
    try {
      final response = await _dio.post('/auth/login/', data: {
        'email': email,
        'password': password,
      });
      await TokenStorage.save(response.data['access'], response.data['refresh']);
    } on DioException {
      throw AuthException('Email ou mot de passe incorrect.');
    }
  }

  Future<void> register({
    required String firstName,
    required String lastName,
    required String email,
    required String password,
    String? phone,
    String country = 'ML',
  }) async {
    try {
      await _dio.post('/auth/register/', data: {
        'first_name': firstName,
        'last_name': lastName,
        'email': email,
        'phone': phone ?? '',
        'country': country,
        'password': password,
        'password_confirm': password,
      });
    } on DioException catch (e) {
      final data = e.response?.data;
      String message = 'Inscription impossible.';
      if (data is Map && data.isNotEmpty) {
        final firstError = data.values.first;
        if (firstError is List && firstError.isNotEmpty) message = firstError.first.toString();
      }
      throw AuthException(message);
    }
  }

  Future<SgtUser> me() async {
    final response = await _dio.get('/auth/me/');
    return SgtUser.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> logout() async {
    await TokenStorage.clear();
  }
}
