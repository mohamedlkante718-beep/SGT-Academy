import 'dart:convert';

import 'package:flutter/material.dart';

import '../app_theme.dart';
import '../db/local_repository.dart';
import '../models/manifeste.dart';
import '../services/crypto_service.dart';
import 'depot_verification_screen.dart';

/// Écran de scan au dépôt.
///
/// NOTE D'IMPLÉMENTATION : la lecture QR par caméra n'est pas encore
/// câblée ici (à intégrer avec un package comme `mobile_scanner`,
/// dont l'API évolue souvent d'une version à l'autre — à valider avec
/// la version réellement utilisée dans le projet). La saisie manuelle
/// ci-dessous, elle, est pleinement fonctionnelle : c'est le chemin
/// de secours déjà prévu au cahier des charges et il couvre aussi le
/// cas où la caméra ou le QR imprimé est illisible.
class DepotScannerScreen extends StatefulWidget {
  const DepotScannerScreen({super.key});

  @override
  State<DepotScannerScreen> createState() => _DepotScannerScreenState();
}

class _DepotScannerScreenState extends State<DepotScannerScreen> {
  final _repository = LocalRepository();
  final _cryptoService = CryptoService();
  final _codeCtrl = TextEditingController();
  bool _saisieManuelleVisible = false;
  String? _erreur;
  bool _enCours = false;

  @override
  void dispose() {
    _codeCtrl.dispose();
    super.dispose();
  }

  Future<void> _verifierCode(String contenu) async {
    setState(() {
      _erreur = null;
      _enCours = true;
    });

    try {
      final json = jsonDecode(contenu) as Map<String, Object?>;
      final manifeste = Manifeste.fromQrJson(json);

      final poste = await _repository.posteParId(manifeste.posteFrontiereId);
      var signatureValide = false;
      if (poste?.clePublique != null) {
        signatureValide = await _cryptoService.verifierSignature(
          payload: manifeste.canonicalPayload(),
          signatureBase64: manifeste.signatureNumerique,
          clePubliqueBase64: poste!.clePublique!,
        );
      }

      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => DepotVerificationScreen(manifeste: manifeste, signatureValide: signatureValide),
        ),
      );
      _codeCtrl.clear();
    } catch (_) {
      setState(() => _erreur = 'Code illisible ou manifeste mal formé. Vérifiez la saisie ou réessayez le scan.');
    } finally {
      if (mounted) setState(() => _enCours = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Poste dépôt'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            GestureDetector(
              onTap: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text(
                      "Scan caméra à intégrer. En attendant, utilisez la saisie manuelle ci-dessous.",
                    ),
                  ),
                );
              },
              child: Container(
                height: 260,
                decoration: BoxDecoration(
                  color: const Color(0xFF0B1116),
                  borderRadius: BorderRadius.circular(18),
                ),
                child: const Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.qr_code_scanner, color: Colors.white54, size: 40),
                      SizedBox(height: 10),
                      Text('Scannez le QR du camion', style: TextStyle(color: Color(0xFFB9C4CE), fontSize: 13.5)),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: () => setState(() => _saisieManuelleVisible = !_saisieManuelleVisible),
              child: const Text('Ou saisir le code manuellement'),
            ),
            if (_saisieManuelleVisible) ...[
              TextField(
                controller: _codeCtrl,
                maxLines: 4,
                decoration: const InputDecoration(
                  labelText: 'Contenu du manifeste (collé ou saisi)',
                ),
              ),
              const SizedBox(height: 12),
              if (_erreur != null) ...[
                Text(_erreur!, style: const TextStyle(color: AppColors.red, fontSize: 13)),
                const SizedBox(height: 12),
              ],
              ElevatedButton(
                onPressed: _enCours ? null : () => _verifierCode(_codeCtrl.text.trim()),
                child: _enCours
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('Vérifier'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
