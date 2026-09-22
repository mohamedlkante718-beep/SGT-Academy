import 'dart:io';

import '../db/local_repository.dart';
import 'api_client.dart';
import 'session_service.dart';

/// Synchronisation différée : envoie ce qui a été créé hors ligne dès
/// qu'une connexion est disponible. Jamais appelée en attente
/// bloquante d'un écran — un échec réseau ici laisse simplement les
/// enregistrements en `sync_status = localOnly` pour un prochain essai.
class SyncService {
  SyncService({
    LocalRepository? repository,
    ApiClient? apiClient,
    SessionService? sessionService,
  })  : _repository = repository ?? LocalRepository(),
        _apiClient = apiClient ?? ApiClient(),
        _sessionService = sessionService ?? SessionService();

  final LocalRepository _repository;
  final ApiClient _apiClient;
  final SessionService _sessionService;

  /// Retourne le nombre d'enregistrements synchronisés avec succès.
  /// Ne lève jamais d'exception : une synchronisation qui échoue est
  /// silencieuse pour l'utilisateur (l'indicateur "en attente" reste
  /// affiché, voir les maquettes) et sera retentée plus tard.
  Future<int> synchroniser() async {
    final token = await _sessionService.token();
    if (token == null) return 0;

    var total = 0;

    try {
      final manifestes = await _repository.manifestesNonSynchronises();
      if (manifestes.isNotEmpty) {
        final resultats = await _apiClient.envoyerManifestes(
          token: token,
          manifestes: manifestes.map((m) => m.toSyncJson()).toList(),
        );
        for (final resultat in resultats) {
          await _repository.marquerManifesteSynchronise(resultat['id'] as String);
          total++;
        }
      }
    } catch (_) {
      // Pas de réseau ou serveur injoignable : on retentera à la
      // prochaine synchronisation, aucune donnée locale n'est perdue.
    }

    try {
      final controles = await _repository.controlesNonSynchronises();
      if (controles.isNotEmpty) {
        final resultats = await _apiClient.envoyerControles(
          token: token,
          controles: controles.map((c) => c.toSyncJson()).toList(),
        );
        for (final resultat in resultats) {
          await _repository.marquerControleSynchronise(resultat['id'] as String);
          total++;
        }
      }
    } catch (_) {
      // Idem : échec silencieux, nouvelle tentative plus tard.
    }

    try {
      final manifestesAvecPhoto = await _repository.manifestesAvecPhotoAEnvoyer();
      for (final manifeste in manifestesAvecPhoto) {
        final chemin = manifeste.photoPath;
        if (chemin == null) continue;
        if (!await File(chemin).exists()) {
          // Photo supprimée du cache de l'appareil entre-temps : on ne
          // pourra plus jamais l'envoyer, on arrête d'essayer.
          await _repository.marquerPhotoSynchronisee(manifeste.id);
          continue;
        }
        await _apiClient.envoyerPhoto(token: token, manifesteId: manifeste.id, cheminFichier: chemin);
        await _repository.marquerPhotoSynchronisee(manifeste.id);
        total++;
      }
    } catch (_) {
      // Pas de réseau : nouvelle tentative à la prochaine synchronisation.
    }

    return total;
  }
}
