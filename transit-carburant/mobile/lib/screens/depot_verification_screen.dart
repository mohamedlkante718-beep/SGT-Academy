import 'dart:async';

import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';

import '../app_theme.dart';
import '../db/local_repository.dart';
import '../models/controle_depot.dart';
import '../models/manifeste.dart';
import '../services/session_service.dart';
import '../services/sync_service.dart';

class DepotVerificationScreen extends StatefulWidget {
  const DepotVerificationScreen({
    super.key,
    required this.manifeste,
    required this.signatureValide,
  });

  final Manifeste manifeste;
  final bool signatureValide;

  @override
  State<DepotVerificationScreen> createState() => _DepotVerificationScreenState();
}

class _DepotVerificationScreenState extends State<DepotVerificationScreen> {
  final _repository = LocalRepository();
  final _sessionService = SessionService();
  final _syncService = SyncService();
  final _remarqueCtrl = TextEditingController();

  bool? _scelleIntact;
  bool? _quantiteConforme;
  bool _enCours = false;

  @override
  void dispose() {
    _remarqueCtrl.dispose();
    super.dispose();
  }

  Future<void> _enregistrer(ControleResultat forcerResultat) async {
    final agent = await _sessionService.utilisateurCourant();
    if (agent == null) return;

    final scelleIntact = _scelleIntact ?? false;
    final quantiteConforme = _quantiteConforme ?? false;

    final resultat = forcerResultat == ControleResultat.anomalie
        ? ControleResultat.anomalie
        : (scelleIntact && quantiteConforme ? ControleResultat.valide : ControleResultat.anomalie);

    setState(() => _enCours = true);
    try {
      final controle = ControleDepot(
        id: const Uuid().v4(),
        manifesteId: widget.manifeste.id,
        agentDepotId: agent.id,
        scelleIntact: scelleIntact,
        quantiteConforme: quantiteConforme,
        remarque: _remarqueCtrl.text.trim().isEmpty ? null : _remarqueCtrl.text.trim(),
        resultat: resultat,
        dateControle: DateTime.now().toUtc(),
      );
      await _repository.insertControleDepot(controle);
      unawaited(_syncService.synchroniser());

      if (!mounted) return;
      Navigator.of(context).pop();
    } finally {
      if (mounted) setState(() => _enCours = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final m = widget.manifeste;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Vérification du camion'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
              decoration: BoxDecoration(
                color: widget.signatureValide ? const Color(0xFFE8F5EC) : const Color(0xFFFBEAEA),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    widget.signatureValide ? Icons.check_circle : Icons.error,
                    color: widget.signatureValide ? AppColors.green : AppColors.red,
                    size: 16,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    widget.signatureValide
                        ? 'Signature du manifeste valide (hors ligne)'
                        : 'Signature invalide — poste inconnu ou manifeste altéré',
                    style: TextStyle(
                      color: widget.signatureValide ? AppColors.green : AppColors.red,
                      fontWeight: FontWeight.w600,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: Colors.white,
                border: Border.all(color: AppColors.border),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Column(
                children: [
                  _ligne('Plaque', m.plaqueImmatriculation),
                  _ligne('Transporteur', m.transporteurNom),
                  _ligne('Cargaison', m.typeCargaison.label),
                  _ligne('Quantité déclarée', '${m.quantiteDeclaree.toStringAsFixed(0)} ${m.unite.apiValue}'),
                  _ligne('N° scellé attendu', m.numeroScelle),
                ],
              ),
            ),
            const SizedBox(height: 16),
            const Text('VÉRIFICATION PHYSIQUE', style: TextStyle(color: AppColors.muted, fontSize: 12.5)),
            const SizedBox(height: 8),
            _bascule('Scellé intact ?', _scelleIntact, (v) => setState(() => _scelleIntact = v)),
            const SizedBox(height: 12),
            _bascule('Quantité conforme ?', _quantiteConforme, (v) => setState(() => _quantiteConforme = v)),
            const SizedBox(height: 12),
            TextField(
              controller: _remarqueCtrl,
              maxLines: 2,
              decoration: const InputDecoration(labelText: 'Remarque (optionnel)'),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _enCours || _scelleIntact == null || _quantiteConforme == null
                  ? null
                  : () => _enregistrer(ControleResultat.valide),
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.green),
              child: const Text("Valider l'entrée"),
            ),
            const SizedBox(height: 10),
            OutlinedButton(
              onPressed: _enCours ? null : () => _enregistrer(ControleResultat.anomalie),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.red,
                side: const BorderSide(color: AppColors.red),
                minimumSize: const Size.fromHeight(46),
              ),
              child: const Text('Signaler une anomalie'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _bascule(String label, bool? valeur, ValueChanged<bool> onChanged) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13.5)),
        const SizedBox(height: 6),
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: () => onChanged(true),
                style: OutlinedButton.styleFrom(
                  backgroundColor: valeur == true ? const Color(0xFFE8F5EC) : Colors.white,
                  foregroundColor: valeur == true ? AppColors.green : AppColors.text,
                  side: BorderSide(color: valeur == true ? AppColors.green : AppColors.border),
                ),
                child: const Text('Oui'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton(
                onPressed: () => onChanged(false),
                style: OutlinedButton.styleFrom(
                  backgroundColor: valeur == false ? const Color(0xFFFBEAEA) : Colors.white,
                  foregroundColor: valeur == false ? AppColors.red : AppColors.text,
                  side: BorderSide(color: valeur == false ? AppColors.red : AppColors.border),
                ),
                child: const Text('Non'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _ligne(String label, String valeur) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppColors.muted, fontSize: 12.5)),
          Text(valeur, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12.5)),
        ],
      ),
    );
  }
}
