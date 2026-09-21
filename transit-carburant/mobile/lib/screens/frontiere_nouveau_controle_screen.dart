import 'dart:async';

import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';

import '../app_theme.dart';
import '../db/local_repository.dart';
import '../models/app_user.dart';
import '../models/manifeste.dart';
import '../models/poste.dart';
import '../services/crypto_service.dart';
import '../services/session_service.dart';
import '../services/sync_service.dart';
import '../widgets/status_pill.dart';
import 'frontiere_manifeste_screen.dart';

class FrontiereNouveauControleScreen extends StatefulWidget {
  const FrontiereNouveauControleScreen({super.key});

  @override
  State<FrontiereNouveauControleScreen> createState() => _FrontiereNouveauControleScreenState();
}

class _FrontiereNouveauControleScreenState extends State<FrontiereNouveauControleScreen> {
  final _repository = LocalRepository();
  final _sessionService = SessionService();
  final _cryptoService = CryptoService();
  final _syncService = SyncService();

  final _plaqueCtrl = TextEditingController();
  final _transporteurCtrl = TextEditingController();
  final _chauffeurNomCtrl = TextEditingController();
  final _chauffeurPieceCtrl = TextEditingController();
  final _quantiteCtrl = TextEditingController();
  final _scelleCtrl = TextEditingController();

  Cargaison _cargaison = Cargaison.essence;
  Unite _unite = Unite.litres;
  Poste? _depotSelectionne;

  AppUser? _agent;
  List<Poste> _depots = [];
  int _enAttente = 0;
  bool _enCours = false;
  String? _erreur;

  @override
  void initState() {
    super.initState();
    _charger();
  }

  Future<void> _charger() async {
    final user = await _sessionService.utilisateurCourant();
    final postes = await _repository.postesLocaux();
    final depots = postes.where((p) => p.type == PosteType.depot).toList();
    final enAttente = (await _repository.manifestesNonSynchronises()).length;
    if (!mounted) return;
    setState(() {
      _agent = user;
      _depots = depots;
      _depotSelectionne = depots.isNotEmpty ? depots.first : null;
      _enAttente = enAttente;
    });
  }

  @override
  void dispose() {
    _plaqueCtrl.dispose();
    _transporteurCtrl.dispose();
    _chauffeurNomCtrl.dispose();
    _chauffeurPieceCtrl.dispose();
    _quantiteCtrl.dispose();
    _scelleCtrl.dispose();
    super.dispose();
  }

  Future<void> _genererManifeste() async {
    setState(() => _erreur = null);

    final agent = _agent;
    final depot = _depotSelectionne;
    final quantite = double.tryParse(_quantiteCtrl.text.replaceAll(',', '.'));

    if (agent?.posteId == null ||
        depot == null ||
        _plaqueCtrl.text.trim().isEmpty ||
        _transporteurCtrl.text.trim().isEmpty ||
        _chauffeurNomCtrl.text.trim().isEmpty ||
        _chauffeurPieceCtrl.text.trim().isEmpty ||
        _scelleCtrl.text.trim().isEmpty ||
        quantite == null) {
      setState(() => _erreur = 'Merci de renseigner tous les champs obligatoires.');
      return;
    }

    final clePrivee = await _sessionService.clePriveePoste(agent!.posteId!);
    if (clePrivee == null) {
      setState(() {
        _erreur = "Aucune clé de signature n'est provisionnée sur cet appareil pour ce poste. "
            "Contactez l'administrateur.";
      });
      return;
    }

    setState(() => _enCours = true);

    try {
      final id = const Uuid().v4();
      final dateCreation = DateTime.now().toUtc();

      final brouillon = Manifeste(
        id: id,
        plaqueImmatriculation: _plaqueCtrl.text.trim(),
        transporteurNom: _transporteurCtrl.text.trim(),
        chauffeurNom: _chauffeurNomCtrl.text.trim(),
        chauffeurPieceIdentite: _chauffeurPieceCtrl.text.trim(),
        posteFrontiereId: agent.posteId!,
        depotDestinationId: depot.id,
        typeCargaison: _cargaison,
        quantiteDeclaree: quantite,
        unite: _unite,
        numeroScelle: _scelleCtrl.text.trim(),
        agentFrontiereId: agent.id,
        signatureNumerique: '',
        dateCreation: dateCreation,
      );

      final signature = await _cryptoService.signerPayload(
        payload: brouillon.canonicalPayload(),
        clePriveeBase64: clePrivee,
      );

      final manifeste = Manifeste(
        id: brouillon.id,
        plaqueImmatriculation: brouillon.plaqueImmatriculation,
        transporteurNom: brouillon.transporteurNom,
        chauffeurNom: brouillon.chauffeurNom,
        chauffeurPieceIdentite: brouillon.chauffeurPieceIdentite,
        posteFrontiereId: brouillon.posteFrontiereId,
        depotDestinationId: brouillon.depotDestinationId,
        typeCargaison: brouillon.typeCargaison,
        quantiteDeclaree: brouillon.quantiteDeclaree,
        unite: brouillon.unite,
        numeroScelle: brouillon.numeroScelle,
        agentFrontiereId: brouillon.agentFrontiereId,
        signatureNumerique: signature,
        dateCreation: brouillon.dateCreation,
        statut: ManifesteStatut.genere,
      );

      await _repository.insertManifeste(manifeste);

      // Tentative de synchronisation immédiate, sans jamais bloquer :
      // si le réseau est indisponible, le manifeste reste "en attente"
      // et sera renvoyé plus tard.
      unawaited(_syncService.synchroniser());

      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => FrontiereManifesteScreen(manifeste: manifeste)),
      );
      _reinitialiserFormulaire();
      _charger();
    } finally {
      if (mounted) setState(() => _enCours = false);
    }
  }

  void _reinitialiserFormulaire() {
    _plaqueCtrl.clear();
    _transporteurCtrl.clear();
    _chauffeurNomCtrl.clear();
    _chauffeurPieceCtrl.clear();
    _quantiteCtrl.clear();
    _scelleCtrl.clear();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Nouveau contrôle'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Center(child: StatusPill(label: '$_enAttente en attente', color: AppColors.orange)),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_erreur != null) ...[
              Text(_erreur!, style: const TextStyle(color: AppColors.red, fontSize: 13)),
              const SizedBox(height: 12),
            ],
            TextField(
              controller: _plaqueCtrl,
              decoration: const InputDecoration(labelText: "Plaque d'immatriculation"),
              textCapitalization: TextCapitalization.characters,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _transporteurCtrl,
              decoration: const InputDecoration(labelText: 'Société de transport'),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _chauffeurNomCtrl,
                    decoration: const InputDecoration(labelText: 'Nom du chauffeur'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: _chauffeurPieceCtrl,
                    decoration: const InputDecoration(labelText: "N° pièce d'identité"),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<Cargaison>(
                    initialValue: _cargaison,
                    decoration: const InputDecoration(labelText: 'Cargaison'),
                    items: Cargaison.values
                        .map((c) => DropdownMenuItem(value: c, child: Text(c.label)))
                        .toList(),
                    onChanged: (value) => setState(() {
                      _cargaison = value ?? _cargaison;
                      _unite = _cargaison == Cargaison.gazButane ? Unite.kg : Unite.litres;
                    }),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: _quantiteCtrl,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: InputDecoration(labelText: 'Quantité (${_unite.apiValue})'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _scelleCtrl,
              decoration: const InputDecoration(labelText: 'N° de scellé'),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<Poste>(
              initialValue: _depotSelectionne,
              decoration: const InputDecoration(labelText: 'Dépôt de destination'),
              items: _depots.map((p) => DropdownMenuItem(value: p, child: Text('${p.nom} — ${p.ville}'))).toList(),
              onChanged: (value) => setState(() => _depotSelectionne = value),
            ),
            if (_depots.isEmpty) ...[
              const SizedBox(height: 6),
              const Text(
                'Aucun dépôt en cache local : connectez-vous une première fois en ligne '
                'pour synchroniser la liste des postes.',
                style: TextStyle(fontSize: 12, color: AppColors.muted),
              ),
            ],
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _enCours ? null : _genererManifeste,
              child: _enCours
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Text('Générer le manifeste QR'),
            ),
          ],
        ),
      ),
    );
  }
}
