import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../app_theme.dart';
import '../models/manifeste.dart';

class FrontiereManifesteScreen extends StatelessWidget {
  const FrontiereManifesteScreen({super.key, required this.manifeste});

  final Manifeste manifeste;

  @override
  Widget build(BuildContext context) {
    // Le QR embarque le manifeste ET sa signature : il reste
    // vérifiable au dépôt sans connexion, sans dépendre du serveur.
    final qrData = jsonEncode(manifeste.toQrPayload());

    return Scaffold(
      appBar: AppBar(title: const Text('Manifeste généré')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              decoration: BoxDecoration(
                color: const Color(0xFFE8F5EC),
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.check_circle, color: AppColors.green, size: 16),
                  SizedBox(width: 8),
                  Text(
                    'Manifeste signé numériquement',
                    style: TextStyle(color: AppColors.green, fontWeight: FontWeight.w600, fontSize: 12.5),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                border: Border.all(color: AppColors.border),
                borderRadius: BorderRadius.circular(16),
              ),
              child: QrImageView(data: qrData, version: QrVersions.auto, size: 220),
            ),
            const SizedBox(height: 20),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: Colors.white,
                border: Border.all(color: AppColors.border),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Column(
                children: [
                  _ligne('Plaque', manifeste.plaqueImmatriculation),
                  _ligne('Transporteur', manifeste.transporteurNom),
                  _ligne('Cargaison', '${manifeste.typeCargaison.label} — ${manifeste.quantiteDeclaree.toStringAsFixed(0)} ${manifeste.unite.apiValue}'),
                  _ligne('N° de scellé', manifeste.numeroScelle),
                  _ligne('Date / heure', manifeste.dateCreation.toLocal().toString().substring(0, 16)),
                ],
              ),
            ),
            const SizedBox(height: 20),
            OutlinedButton(
              onPressed: () {},
              style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(46)),
              child: const Text('Imprimer le ticket'),
            ),
            const SizedBox(height: 10),
            ElevatedButton(
              onPressed: () {},
              child: const Text('Envoyer par SMS au chauffeur'),
            ),
            const SizedBox(height: 16),
            const Text(
              'Ce manifeste reste vérifiable hors connexion jusqu\'à l\'arrivée au dépôt.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.muted, fontSize: 11.5),
            ),
            const SizedBox(height: 20),
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Terminer'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _ligne(String label, String valeur) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppColors.muted, fontSize: 13)),
          Flexible(
            child: Text(
              valeur,
              textAlign: TextAlign.right,
              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}
