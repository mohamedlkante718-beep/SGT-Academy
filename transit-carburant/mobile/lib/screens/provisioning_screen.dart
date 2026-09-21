import 'package:flutter/material.dart';

import '../services/session_service.dart';

/// Écran de provisionnement : après avoir créé un poste frontière via
/// l'API (`POST /postes`), l'administrateur récupère une clé privée
/// affichée UNE SEULE FOIS et doit la copier ici, sur l'appareil de
/// l'agent affecté à ce poste. Le serveur ne la stocke jamais.
class ProvisioningScreen extends StatefulWidget {
  const ProvisioningScreen({super.key});

  @override
  State<ProvisioningScreen> createState() => _ProvisioningScreenState();
}

class _ProvisioningScreenState extends State<ProvisioningScreen> {
  final _posteIdCtrl = TextEditingController();
  final _clePriveeCtrl = TextEditingController();
  final _sessionService = SessionService();
  String? _message;

  @override
  void dispose() {
    _posteIdCtrl.dispose();
    _clePriveeCtrl.dispose();
    super.dispose();
  }

  Future<void> _enregistrer() async {
    if (_posteIdCtrl.text.trim().isEmpty || _clePriveeCtrl.text.trim().isEmpty) {
      setState(() => _message = 'Renseignez l\'identifiant du poste et la clé privée.');
      return;
    }
    await _sessionService.provisionnerClePriveePoste(
      _posteIdCtrl.text.trim(),
      _clePriveeCtrl.text.trim(),
    );
    if (!mounted) return;
    setState(() => _message = 'Clé enregistrée sur cet appareil pour ce poste.');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Provisionner une clé de poste')),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'À faire une seule fois par appareil, par un administrateur, '
              'juste après la création du poste frontière.',
              style: TextStyle(fontSize: 13, color: Colors.black54),
            ),
            const SizedBox(height: 20),
            TextField(
              controller: _posteIdCtrl,
              decoration: const InputDecoration(labelText: 'Identifiant du poste frontière'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _clePriveeCtrl,
              maxLines: 3,
              decoration: const InputDecoration(labelText: 'Clé privée (base64, fournie une seule fois)'),
            ),
            const SizedBox(height: 20),
            ElevatedButton(onPressed: _enregistrer, child: const Text('Enregistrer sur cet appareil')),
            if (_message != null) ...[
              const SizedBox(height: 12),
              Text(_message!, style: const TextStyle(color: Colors.black87)),
            ],
          ],
        ),
      ),
    );
  }
}
