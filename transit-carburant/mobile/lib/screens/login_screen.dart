import 'package:flutter/material.dart';

import '../app_theme.dart';
import '../db/local_repository.dart';
import '../models/app_user.dart';
import '../services/api_client.dart';
import '../services/jwt_util.dart';
import '../services/session_service.dart';
import 'depot_scanner_screen.dart';
import 'frontiere_nouveau_controle_screen.dart';
import 'provisioning_screen.dart';
import 'superviseur_dashboard_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _matriculeCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _apiClient = ApiClient();
  final _sessionService = SessionService();
  final _repository = LocalRepository();

  bool _loading = false;
  String? _erreur;

  @override
  void dispose() {
    _matriculeCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _seConnecter() async {
    setState(() {
      _loading = true;
      _erreur = null;
    });

    try {
      final result = await _apiClient.login(
        matricule: _matriculeCtrl.text.trim(),
        password: _passwordCtrl.text,
      );
      final token = result['access_token'] as String;
      final roleApi = result['role'] as String;
      final posteId = result['poste_id'] as String?;
      final payload = decodeJwtPayload(token);

      final user = AppUser(
        id: payload['sub'] as String,
        matricule: _matriculeCtrl.text.trim(),
        nomComplet: _matriculeCtrl.text.trim(),
        role: UserRoleApi.fromApi(roleApi),
        posteId: posteId,
      );
      await _sessionService.enregistrerSession(token: token, user: user);

      // Best-effort : met à jour le cache local des postes (utile pour
      // choisir le dépôt de destination hors ligne ensuite). Un échec
      // ici ne bloque jamais la connexion.
      try {
        final postes = await _apiClient.recupererPostes(token: token);
        await _repository.enregistrerPostes(postes);
      } catch (_) {
        // Pas de réseau : on continue avec le cache local existant.
      }

      if (!mounted) return;
      _naviguerSelonRole(user.role);
    } catch (_) {
      setState(() {
        _erreur = 'Connexion impossible. Vérifiez le matricule et le mot de passe, '
            'ou réessayez lorsque le réseau sera disponible.';
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _naviguerSelonRole(UserRole role) {
    final Widget destination = switch (role) {
      UserRole.agentFrontiere => const FrontiereNouveauControleScreen(),
      UserRole.agentDepot => const DepotScannerScreen(),
      UserRole.superviseur || UserRole.admin => const SuperviseurDashboardScreen(),
    };
    Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => destination));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.navy,
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.all(32),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 68,
                        height: 68,
                        decoration: BoxDecoration(
                          color: AppColors.teal,
                          borderRadius: BorderRadius.circular(18),
                        ),
                        child: const Icon(Icons.local_shipping_outlined, color: Colors.white, size: 34),
                      ),
                      const SizedBox(height: 14),
                      Text(
                        'TransitCarburant',
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: Colors.white),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Contrôle numérique des citernes, de la frontière au dépôt',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Color(0xFFB9C4CE), fontSize: 14),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            Container(
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
              ),
              padding: const EdgeInsets.fromLTRB(24, 28, 24, 36),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (_erreur != null) ...[
                    Text(_erreur!, style: const TextStyle(color: AppColors.red, fontSize: 13)),
                    const SizedBox(height: 12),
                  ],
                  TextField(
                    controller: _matriculeCtrl,
                    decoration: const InputDecoration(labelText: 'Matricule agent'),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _passwordCtrl,
                    obscureText: true,
                    decoration: const InputDecoration(labelText: 'Mot de passe'),
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton(
                    onPressed: _loading ? null : _seConnecter,
                    child: _loading
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Se connecter'),
                  ),
                  const SizedBox(height: 8),
                  TextButton(
                    onPressed: () => Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const ProvisioningScreen()),
                    ),
                    child: const Text('Provisionner une clé de poste (admin)'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
