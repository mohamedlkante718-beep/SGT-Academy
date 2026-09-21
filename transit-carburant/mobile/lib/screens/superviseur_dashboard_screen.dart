import 'package:flutter/material.dart';

import '../app_theme.dart';
import '../services/api_client.dart';
import '../services/session_service.dart';
import 'login_screen.dart';

/// Tableau de bord du superviseur. Contrairement aux écrans agents,
/// il a besoin du réseau (il agrège des données de plusieurs
/// appareils) : ce n'est pas une fonction critique du parcours
/// hors-ligne, donc on ne la duplique pas en local.
class SuperviseurDashboardScreen extends StatefulWidget {
  const SuperviseurDashboardScreen({super.key});

  @override
  State<SuperviseurDashboardScreen> createState() => _SuperviseurDashboardScreenState();
}

class _SuperviseurDashboardScreenState extends State<SuperviseurDashboardScreen> {
  final _apiClient = ApiClient();
  final _sessionService = SessionService();
  late Future<_DonneesTableauDeBord> _futureDonnees;

  @override
  void initState() {
    super.initState();
    _futureDonnees = _charger();
  }

  Future<_DonneesTableauDeBord> _charger() async {
    final token = await _sessionService.token();
    if (token == null) throw StateError('Session expirée');

    final resume = await _apiClient.tableauDeBordResume(token: token);
    final manifestes = await _apiClient.tableauDeBordManifestes(token: token);
    final alertes = await _apiClient.tableauDeBordAlertes(token: token);
    return _DonneesTableauDeBord(resume: resume, manifestes: manifestes, alertes: alertes);
  }

  Future<void> _rafraichir() async {
    setState(() => _futureDonnees = _charger());
    await _futureDonnees;
  }

  Future<void> _seDeconnecter() async {
    await _sessionService.deconnecter();
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Supervision'),
        actions: [
          IconButton(onPressed: _rafraichir, icon: const Icon(Icons.refresh)),
          IconButton(onPressed: _seDeconnecter, icon: const Icon(Icons.logout)),
        ],
      ),
      body: FutureBuilder<_DonneesTableauDeBord>(
        future: _futureDonnees,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  "Impossible de charger le tableau de bord. Vérifiez la connexion et réessayez.\n${snapshot.error}",
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }

          final donnees = snapshot.data!;
          final resume = donnees.resume;

          return RefreshIndicator(
            onRefresh: _rafraichir,
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: [
                GridView.count(
                  crossAxisCount: 2,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  childAspectRatio: 1.7,
                  children: [
                    _kpi('Camions en transit', '${resume['camions_en_transit']}', AppColors.teal),
                    _kpi('Au dépôt aujourd\'hui', '${resume['camions_au_depot_aujourdhui']}', AppColors.green),
                    _kpi('Alertes actives', '${resume['alertes_actives']}', AppColors.red),
                    _kpi(
                      'Volume aujourd\'hui',
                      '${(resume['volume_total_aujourdhui'] as num).toStringAsFixed(0)} L',
                      AppColors.navy,
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                const Text('ALERTES RÉCENTES', style: TextStyle(color: AppColors.muted, fontSize: 12.5)),
                const SizedBox(height: 8),
                if (donnees.alertes.isEmpty)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 12),
                    child: Text('Aucune alerte ouverte.'),
                  )
                else
                  ...donnees.alertes.map(
                    (a) => Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        leading: Icon(
                          a['gravite'] == 'haute' ? Icons.error : Icons.warning_amber,
                          color: a['gravite'] == 'haute' ? AppColors.red : AppColors.orange,
                        ),
                        title: Text(a['description'] as String? ?? ''),
                        subtitle: Text(a['type'] as String? ?? ''),
                      ),
                    ),
                  ),
                const SizedBox(height: 20),
                const Text('CAMIONS EN TRANSIT / RÉCENTS', style: TextStyle(color: AppColors.muted, fontSize: 12.5)),
                const SizedBox(height: 8),
                ...donnees.manifestes.take(30).map(
                      (m) => Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          title: Text('${m['type_cargaison']} — ${m['quantite_declaree']} ${m['unite']}'),
                          subtitle: Text('Statut : ${m['statut']}'),
                          trailing: Icon(
                            m['signature_valide'] == true ? Icons.verified : Icons.error_outline,
                            color: m['signature_valide'] == true ? AppColors.green : AppColors.red,
                          ),
                        ),
                      ),
                    ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _kpi(String label, String valeur, Color couleur) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppColors.border),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(label, style: const TextStyle(color: AppColors.muted, fontSize: 11.5)),
          const SizedBox(height: 4),
          Text(valeur, style: TextStyle(color: couleur, fontSize: 20, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

class _DonneesTableauDeBord {
  final Map<String, Object?> resume;
  final List<Map<String, Object?>> manifestes;
  final List<Map<String, Object?>> alertes;

  _DonneesTableauDeBord({required this.resume, required this.manifestes, required this.alertes});
}
