import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import '../app_theme.dart';
import '../db/local_repository.dart';
import '../models/manifeste.dart';
import '../services/crypto_service.dart';
import '../services/session_service.dart';
import 'depot_verification_screen.dart';
import 'historique_depot_screen.dart';
import 'login_screen.dart';

/// Écran de scan au dépôt.
///
/// La caméra (`mobile_scanner`) est le chemin principal ; la saisie
/// manuelle reste disponible en dessous, pleinement fonctionnelle,
/// pour le cas où la caméra est indisponible (permission refusée,
/// appareil sans caméra utilisable) ou le QR imprimé illisible.
class DepotScannerScreen extends StatefulWidget {
  const DepotScannerScreen({super.key});

  @override
  State<DepotScannerScreen> createState() => _DepotScannerScreenState();
}

class _DepotScannerScreenState extends State<DepotScannerScreen> {
  final _repository = LocalRepository();
  final _cryptoService = CryptoService();
  final _sessionService = SessionService();
  final _codeCtrl = TextEditingController();
  final _controller = MobileScannerController(
    detectionSpeed: DetectionSpeed.noDuplicates,
  );

  bool _saisieManuelleVisible = false;
  String? _erreur;
  bool _enCours = false;
  bool _torcheActive = false;

  @override
  void dispose() {
    _codeCtrl.dispose();
    _controller.dispose();
    super.dispose();
  }

  Future<void> _seDeconnecter() async {
    await _sessionService.deconnecter();
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (route) => false,
    );
  }

  Future<void> _onDetect(BarcodeCapture capture) async {
    if (_enCours) return;
    final contenu = capture.barcodes.firstOrNull?.rawValue;
    if (contenu == null || contenu.isEmpty) return;

    // On met la caméra en pause pendant le traitement pour éviter de
    // relancer une vérification sur chaque frame tant que le premier
    // scan n'est pas encore traité.
    await _controller.stop();
    await _verifierCode(contenu);
    if (mounted) {
      await _controller.start();
    }
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
        actions: [
          IconButton(
            tooltip: 'Torche',
            icon: Icon(_torcheActive ? Icons.flash_on : Icons.flash_off),
            onPressed: () async {
              await _controller.toggleTorch();
              if (mounted) setState(() => _torcheActive = !_torcheActive);
            },
          ),
          IconButton(
            tooltip: 'Se déconnecter',
            icon: const Icon(Icons.logout),
            onPressed: _seDeconnecter,
          ),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: 0,
        onDestinationSelected: (index) {
          if (index == 1) {
            Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const HistoriqueDepotScreen()),
            );
          }
        },
        destinations: const [
          NavigationDestination(icon: Icon(Icons.qr_code_scanner), label: 'Scanner'),
          NavigationDestination(icon: Icon(Icons.history), label: 'Historique'),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(18),
              child: SizedBox(
                height: 300,
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    MobileScanner(
                      controller: _controller,
                      onDetect: _onDetect,
                      errorBuilder: (context, error, child) => _erreurCamera(error),
                    ),
                    IgnorePointer(child: _viseur()),
                    if (_enCours)
                      Container(
                        color: Colors.black54,
                        child: const Center(
                          child: CircularProgressIndicator(color: Colors.white),
                        ),
                      ),
                  ],
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
            ],
            if (_erreur != null) ...[
              Text(_erreur!, style: const TextStyle(color: AppColors.red, fontSize: 13)),
              const SizedBox(height: 12),
            ],
            if (_saisieManuelleVisible)
              ElevatedButton(
                onPressed: _enCours ? null : () => _verifierCode(_codeCtrl.text.trim()),
                child: const Text('Vérifier'),
              ),
          ],
        ),
      ),
    );
  }

  Widget _viseur() {
    return Stack(
      children: [
        Positioned(
          top: 18,
          left: 18,
          child: _coin(top: true, left: true),
        ),
        Positioned(
          top: 18,
          right: 18,
          child: _coin(top: true, left: false),
        ),
        Positioned(
          bottom: 18,
          left: 18,
          child: _coin(top: false, left: true),
        ),
        Positioned(
          bottom: 18,
          right: 18,
          child: _coin(top: false, left: false),
        ),
        const Align(
          alignment: Alignment.bottomCenter,
          child: Padding(
            padding: EdgeInsets.only(bottom: 16),
            child: Text(
              'Scannez le QR du camion',
              style: TextStyle(color: Color(0xFFE7ECEF), fontSize: 13.5, fontWeight: FontWeight.w600),
            ),
          ),
        ),
      ],
    );
  }

  Widget _coin({required bool top, required bool left}) {
    return Container(
      width: 32,
      height: 32,
      decoration: BoxDecoration(
        border: Border(
          top: top ? const BorderSide(color: AppColors.teal, width: 3) : BorderSide.none,
          bottom: !top ? const BorderSide(color: AppColors.teal, width: 3) : BorderSide.none,
          left: left ? const BorderSide(color: AppColors.teal, width: 3) : BorderSide.none,
          right: !left ? const BorderSide(color: AppColors.teal, width: 3) : BorderSide.none,
        ),
      ),
    );
  }

  Widget _erreurCamera(MobileScannerException error) {
    final message = switch (error.errorCode) {
      MobileScannerErrorCode.permissionDenied =>
        "Accès à la caméra refusé. Autorisez-le dans les réglages du téléphone, ou utilisez la saisie manuelle ci-dessous.",
      _ => "Caméra indisponible. Utilisez la saisie manuelle ci-dessous.",
    };
    return Container(
      color: const Color(0xFF0B1116),
      padding: const EdgeInsets.all(20),
      alignment: Alignment.center,
      child: Text(
        message,
        textAlign: TextAlign.center,
        style: const TextStyle(color: Color(0xFFE7ECEF), fontSize: 13.5),
      ),
    );
  }
}
