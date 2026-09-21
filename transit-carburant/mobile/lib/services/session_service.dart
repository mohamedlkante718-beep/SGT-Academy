import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/app_user.dart';

/// Session locale de l'agent connecté sur cet appareil.
///
/// Le token et le profil (non sensibles) vivent dans les préférences
/// partagées ; la clé privée de signature d'un poste frontière (très
/// sensible) est chiffrée séparément via le trousseau du système
/// (Keystore Android / Keychain iOS), jamais envoyée au serveur ni
/// visible en clair sur le disque.
class SessionService {
  static const _kToken = 'auth_token';
  static const _kUserId = 'user_id';
  static const _kMatricule = 'matricule';
  static const _kNomComplet = 'nom_complet';
  static const _kRole = 'role';
  static const _kPosteId = 'poste_id';
  static const _kClePriveePrefix = 'cle_privee_poste_';

  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  Future<void> enregistrerSession({
    required String token,
    required AppUser user,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kToken, token);
    await prefs.setString(_kUserId, user.id);
    await prefs.setString(_kMatricule, user.matricule);
    await prefs.setString(_kNomComplet, user.nomComplet);
    await prefs.setString(_kRole, user.role.name);
    if (user.posteId != null) {
      await prefs.setString(_kPosteId, user.posteId!);
    }
  }

  Future<String?> token() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_kToken);
  }

  Future<AppUser?> utilisateurCourant() async {
    final prefs = await SharedPreferences.getInstance();
    final id = prefs.getString(_kUserId);
    if (id == null) return null;
    return AppUser(
      id: id,
      matricule: prefs.getString(_kMatricule) ?? '',
      nomComplet: prefs.getString(_kNomComplet) ?? '',
      role: UserRole.values.byName(prefs.getString(_kRole) ?? 'agentFrontiere'),
      posteId: prefs.getString(_kPosteId),
    );
  }

  Future<void> deconnecter() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
  }

  /// Provisionnement initial (par l'administrateur) de la clé privée
  /// Ed25519 d'un poste frontière sur l'appareil de l'agent affecté.
  Future<void> provisionnerClePriveePoste(String posteId, String clePriveeBase64) async {
    await _secureStorage.write(key: '$_kClePriveePrefix$posteId', value: clePriveeBase64);
  }

  Future<String?> clePriveePoste(String posteId) {
    return _secureStorage.read(key: '$_kClePriveePrefix$posteId');
  }
}
