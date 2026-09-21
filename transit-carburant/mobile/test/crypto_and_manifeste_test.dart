import 'dart:convert';

import 'package:cryptography/cryptography.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:transit_carburant/models/manifeste.dart';
import 'package:transit_carburant/services/crypto_service.dart';

void main() {
  final cryptoService = CryptoService();

  group('CryptoService (Ed25519 hors ligne)', () {
    test('un manifeste signé est vérifié valide avec la bonne clé publique', () async {
      final keyPair = await Ed25519().newKeyPair();
      final clePriveeBase64 = base64Encode(await keyPair.extractPrivateKeyBytes());
      final publicKey = await keyPair.extractPublicKey();
      final clePubliqueBase64 = base64Encode(publicKey.bytes);

      final manifeste = Manifeste(
        id: '11111111-1111-1111-1111-111111111111',
        plaqueImmatriculation: 'ML-4521-AB',
        transporteurNom: 'STMB Transport',
        chauffeurNom: 'Amadou Traoré',
        chauffeurPieceIdentite: 'CNI-99887',
        posteFrontiereId: 'poste-kouremale',
        depotDestinationId: 'depot-bamako',
        typeCargaison: Cargaison.essence,
        quantiteDeclaree: 32000.0,
        unite: Unite.litres,
        numeroScelle: 'SC-88213',
        agentFrontiereId: 'agent-1',
        signatureNumerique: '',
        dateCreation: DateTime.utc(2026, 9, 21, 9, 42),
      );

      final signature = await cryptoService.signerPayload(
        payload: manifeste.canonicalPayload(),
        clePriveeBase64: clePriveeBase64,
      );

      final valide = await cryptoService.verifierSignature(
        payload: manifeste.canonicalPayload(),
        signatureBase64: signature,
        clePubliqueBase64: clePubliqueBase64,
      );

      expect(valide, isTrue);
    });

    test('une donnée modifiée après signature rend la vérification invalide', () async {
      final keyPair = await Ed25519().newKeyPair();
      final clePriveeBase64 = base64Encode(await keyPair.extractPrivateKeyBytes());
      final clePubliqueBase64 = base64Encode((await keyPair.extractPublicKey()).bytes);

      const payloadOriginal = 'id|ML-4521-AB|STMB|Amadou|essence|32000.000|litres|SC-1|poste|depot|2026-09-21';
      final signature = await cryptoService.signerPayload(
        payload: payloadOriginal,
        clePriveeBase64: clePriveeBase64,
      );

      const payloadAltere = 'id|ML-4521-AB|STMB|Amadou|essence|99999.000|litres|SC-1|poste|depot|2026-09-21';
      final valide = await cryptoService.verifierSignature(
        payload: payloadAltere,
        signatureBase64: signature,
        clePubliqueBase64: clePubliqueBase64,
      );

      expect(valide, isFalse);
    });

    test('une clé publique incorrecte rend la vérification invalide', () async {
      final keyPairSigneur = await Ed25519().newKeyPair();
      final clePriveeBase64 = base64Encode(await keyPairSigneur.extractPrivateKeyBytes());

      final autreKeyPair = await Ed25519().newKeyPair();
      final mauvaiseClePubliqueBase64 = base64Encode((await autreKeyPair.extractPublicKey()).bytes);

      const payload = 'contenu-du-manifeste';
      final signature = await cryptoService.signerPayload(
        payload: payload,
        clePriveeBase64: clePriveeBase64,
      );

      final valide = await cryptoService.verifierSignature(
        payload: payload,
        signatureBase64: signature,
        clePubliqueBase64: mauvaiseClePubliqueBase64,
      );

      expect(valide, isFalse);
    });

    test('une signature malformée ne lève jamais d\'exception', () async {
      final valide = await cryptoService.verifierSignature(
        payload: 'peu importe',
        signatureBase64: 'pas-du-base64-valide!!',
        clePubliqueBase64: 'pas-du-base64-valide-non-plus!!',
      );
      expect(valide, isFalse);
    });
  });

  group('Manifeste — sérialisation', () {
    test('canonicalPayload() respecte exactement le format attendu par le backend', () {
      final manifeste = Manifeste(
        id: 'abc-123',
        plaqueImmatriculation: 'ML-4521-AB',
        transporteurNom: 'STMB Transport',
        chauffeurNom: 'Amadou Traoré',
        chauffeurPieceIdentite: 'CNI-99887',
        posteFrontiereId: 'poste-1',
        depotDestinationId: 'depot-1',
        typeCargaison: Cargaison.gazButane,
        quantiteDeclaree: 12.5,
        unite: Unite.kg,
        numeroScelle: 'SC-1',
        agentFrontiereId: 'agent-1',
        signatureNumerique: '',
        dateCreation: DateTime.utc(2026, 1, 2, 3, 4, 5),
      );

      expect(
        manifeste.canonicalPayload(),
        'abc-123|ML-4521-AB|STMB Transport|Amadou Traoré|gaz_butane|12.500|kg|SC-1|poste-1|depot-1|2026-01-02T03:04:05.000Z',
      );
    });

    test('toQrPayload() puis fromQrJson() restitue un manifeste identique', () {
      final original = Manifeste(
        id: 'xyz-789',
        plaqueImmatriculation: 'ML-1000-ZZ',
        transporteurNom: 'Sahel Logistique',
        chauffeurNom: 'Fatoumata Coulibaly',
        chauffeurPieceIdentite: 'CNI-1',
        posteFrontiereId: 'poste-2',
        depotDestinationId: 'depot-2',
        typeCargaison: Cargaison.gasoil,
        quantiteDeclaree: 28000,
        unite: Unite.litres,
        numeroScelle: 'SC-2',
        agentFrontiereId: 'agent-2',
        signatureNumerique: 'signature-test',
        dateCreation: DateTime.utc(2026, 3, 4, 5, 6, 7),
      );

      final restaure = Manifeste.fromQrJson(original.toQrPayload());

      expect(restaure.id, original.id);
      expect(restaure.plaqueImmatriculation, original.plaqueImmatriculation);
      expect(restaure.typeCargaison, original.typeCargaison);
      expect(restaure.quantiteDeclaree, original.quantiteDeclaree);
      expect(restaure.signatureNumerique, original.signatureNumerique);
      expect(restaure.canonicalPayload(), original.canonicalPayload());
    });
  });
}
