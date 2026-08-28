import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// URL de base de l'API backend. Passez la vôtre au build/lancement :
/// flutter run --dart-define=API_BASE_URL=https://votre-domaine.up.railway.app/api/v1
const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://127.0.0.1:8000/api/v1',
);

const _accessTokenKey = 'sgt_access_token';
const _refreshTokenKey = 'sgt_refresh_token';

class TokenStorage {
  static Future<void> save(String access, String refresh) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_accessTokenKey, access);
    await prefs.setString(_refreshTokenKey, refresh);
  }

  static Future<String?> readAccess() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_accessTokenKey);
  }

  static Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_accessTokenKey);
    await prefs.remove(_refreshTokenKey);
  }
}

Dio buildApiClient() {
  final dio = Dio(BaseOptions(baseUrl: apiBaseUrl));

  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await TokenStorage.readAccess();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
    ),
  );

  return dio;
}
