import 'dart:convert';

import 'package:cryptography/cryptography.dart';

/// Signature et vérification Ed25519, hors ligne, des manifestes.
///
/// IMPORTANT : l'algorithme, l'encodage et l'ordre des champs doivent
/// rester identiques à `build_manifeste_payload` côté backend
/// (`backend/app/security.py`) — voir `Manifeste.canonicalPayload()`.
class CryptoService {
  final Ed25519 _algorithm = Ed25519();

  /// Signe [payload] (le texte canonique du manifeste) avec la clé
  /// privée du poste frontière, provisionnée sur cet appareil par
  /// l'administrateur à l'affectation de l'agent.
  Future<String> signerPayload({
    required String payload,
    required String clePriveeBase64,
  }) async {
    final seed = base64Decode(clePriveeBase64);
    final keyPair = await _algorithm.newKeyPairFromSeed(seed);
    final signature = await _algorithm.sign(utf8.encode(payload), keyPair: keyPair);
    return base64Encode(signature.bytes);
  }

  /// Vérifie hors ligne qu'un manifeste scanné au dépôt a bien été
  /// signé par le poste frontière déclaré, en utilisant sa clé
  /// publique (préchargée sur l'appareil dépôt, voir
  /// `services/postes_cache_service.dart`).
  Future<bool> verifierSignature({
    required String payload,
    required String signatureBase64,
    required String clePubliqueBase64,
  }) async {
    try {
      final publicKey = SimplePublicKey(
        base64Decode(clePubliqueBase64),
        type: KeyPairType.ed25519,
      );
      final signature = Signature(base64Decode(signatureBase64), publicKey: publicKey);
      return await _algorithm.verify(utf8.encode(payload), signature: signature);
    } catch (_) {
      // Clé, signature ou payload malformé : jamais une exception qui
      // remonte à l'écran, toujours un simple "non valide".
      return false;
    }
  }
}
