import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import '../models/poste.dart';

/// Client HTTP vers le backend central. Chaque appel peut échouer par
/// absence de réseau : les écrans et services appelants doivent
/// toujours retomber sur les données locales (voir `SyncService`),
/// jamais bloquer une action critique en l'attendant.
class ApiClient {
  ApiClient({String? baseUrl}) : baseUrl = baseUrl ?? _defaultBaseUrl;

  // À adapter selon l'environnement (dev local, Render/Fly.io, etc.),
  // par ex. via --dart-define=API_BASE_URL=... au build.
  static const _defaultBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  final String baseUrl;

  Future<Map<String, Object?>> login({
    required String matricule,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: _jsonHeaders(),
      body: jsonEncode({'matricule': matricule, 'password': password}),
    );
    _throwIfError(response);
    return jsonDecode(response.body) as Map<String, Object?>;
  }

  Future<List<Poste>> recupererPostes({required String token}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/postes'),
      headers: _jsonHeaders(token: token),
    );
    _throwIfError(response);
    final list = jsonDecode(response.body) as List<dynamic>;
    return list.map((e) => Poste.fromMap(_apiPosteToDbMap(e as Map<String, Object?>))).toList();
  }

  Future<List<Map<String, Object?>>> envoyerManifestes({
    required String token,
    required List<Map<String, Object?>> manifestes,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/sync/manifestes'),
      headers: _jsonHeaders(token: token),
      body: jsonEncode({'manifestes': manifestes}),
    );
    _throwIfError(response);
    final body = jsonDecode(response.body) as Map<String, Object?>;
    return (body['resultats'] as List<dynamic>).cast<Map<String, Object?>>();
  }

  Future<List<Map<String, Object?>>> envoyerControles({
    required String token,
    required List<Map<String, Object?>> controles,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/sync/controles'),
      headers: _jsonHeaders(token: token),
      body: jsonEncode({'controles': controles}),
    );
    _throwIfError(response);
    final body = jsonDecode(response.body) as Map<String, Object?>;
    return (body['resultats'] as List<dynamic>).cast<Map<String, Object?>>();
  }

  /// Envoie la photo (prise via la caméra, donc systématiquement
  /// réencodée en JPEG par `image_picker`) après que le manifeste
  /// lui-même a déjà été synchronisé — c'est un envoi plus lourd,
  /// jamais un prérequis pour la vérification hors ligne au dépôt.
  Future<String> envoyerPhoto({
    required String token,
    required String manifesteId,
    required String cheminFichier,
  }) async {
    final uri = Uri.parse('$baseUrl/sync/manifestes/$manifesteId/photo');
    final request = http.MultipartRequest('POST', uri)
      ..headers['Authorization'] = 'Bearer $token'
      ..files.add(
        await http.MultipartFile.fromPath(
          'fichier',
          cheminFichier,
          contentType: MediaType('image', 'jpeg'),
        ),
      );
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    _throwIfError(response);
    final body = jsonDecode(response.body) as Map<String, Object?>;
    return body['photo_path'] as String;
  }

  Future<Map<String, Object?>> tableauDeBordResume({required String token}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/dashboard/summary'),
      headers: _jsonHeaders(token: token),
    );
    _throwIfError(response);
    return jsonDecode(response.body) as Map<String, Object?>;
  }

  Future<List<Map<String, Object?>>> tableauDeBordManifestes({required String token}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/dashboard/manifestes'),
      headers: _jsonHeaders(token: token),
    );
    _throwIfError(response);
    return (jsonDecode(response.body) as List<dynamic>).cast<Map<String, Object?>>();
  }

  Future<List<Map<String, Object?>>> tableauDeBordAlertes({required String token}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/dashboard/alertes'),
      headers: _jsonHeaders(token: token),
    );
    _throwIfError(response);
    return (jsonDecode(response.body) as List<dynamic>).cast<Map<String, Object?>>();
  }

  Map<String, Object?> _apiPosteToDbMap(Map<String, Object?> apiPoste) => apiPoste;

  Map<String, String> _jsonHeaders({String? token}) => {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

  void _throwIfError(http.Response response) {
    if (response.statusCode >= 400) {
      throw ApiException(response.statusCode, response.body);
    }
  }
}

class ApiException implements Exception {
  final int statusCode;
  final String body;

  ApiException(this.statusCode, this.body);

  @override
  String toString() => 'ApiException($statusCode): $body';
}
