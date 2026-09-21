import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../app_theme.dart';
import '../db/local_repository.dart';
import '../models/manifeste.dart';

/// Historique local des manifestes créés sur cet appareil. Comme
/// chaque téléphone frontière ne crée que ses propres manifestes, la
/// liste locale complète suffit : pas besoin d'un filtre par agent.
class HistoriqueFrontiereScreen extends StatefulWidget {
  const HistoriqueFrontiereScreen({super.key});

  @override
  State<HistoriqueFrontiereScreen> createState() => _HistoriqueFrontiereScreenState();
}

class _HistoriqueFrontiereScreenState extends State<HistoriqueFrontiereScreen> {
  final _repository = LocalRepository();
  late Future<List<Manifeste>> _futureManifestes;

  @override
  void initState() {
    super.initState();
    _futureManifestes = _repository.manifestesRecents();
  }

  Future<void> _rafraichir() async {
    setState(() => _futureManifestes = _repository.manifestesRecents());
    await _futureManifestes;
  }

  @override
  Widget build(BuildContext context) {
    final dateFormat = DateFormat('dd/MM — HH:mm');

    return Scaffold(
      appBar: AppBar(title: const Text('Historique')),
      body: FutureBuilder<List<Manifeste>>(
        future: _futureManifestes,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          final manifestes = snapshot.data ?? [];
          if (manifestes.isEmpty) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text('Aucun contrôle enregistré sur cet appareil pour le moment.'),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: _rafraichir,
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: manifestes.length,
              separatorBuilder: (context, index) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final m = manifestes[index];
                return Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    border: Border.all(color: AppColors.border),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(m.plaqueImmatriculation, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14.5)),
                            const SizedBox(height: 3),
                            Text(
                              '${m.typeCargaison.label} · ${m.quantiteDeclaree.toStringAsFixed(0)} ${m.unite.apiValue}',
                              style: const TextStyle(fontSize: 12.5, color: AppColors.muted),
                            ),
                            const SizedBox(height: 3),
                            Text(dateFormat.format(m.dateCreation.toLocal()), style: const TextStyle(fontSize: 11.5, color: AppColors.muted)),
                          ],
                        ),
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          _badgeStatut(m.statut),
                          const SizedBox(height: 6),
                          _badgeSync(m.syncStatus),
                        ],
                      ),
                    ],
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }

  Widget _badgeStatut(ManifesteStatut statut) {
    final (label, color) = switch (statut) {
      ManifesteStatut.genere => ('Généré', AppColors.muted),
      ManifesteStatut.enRoute => ('En route', AppColors.teal),
      ManifesteStatut.controleDepot => ('Au dépôt', AppColors.navy),
      ManifesteStatut.valide => ('Validé', AppColors.green),
      ManifesteStatut.anomalie => ('Anomalie', AppColors.red),
    };
    return _badge(label, color);
  }

  Widget _badgeSync(SyncStatus statut) {
    final (label, color) = switch (statut) {
      SyncStatus.localOnly => ('En attente', AppColors.orange),
      SyncStatus.synced => ('Synchronisé', AppColors.green),
      SyncStatus.conflict => ('Conflit', AppColors.red),
    };
    return _badge(label, color);
  }

  Widget _badge(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(20)),
      child: Text(label, style: TextStyle(color: color, fontSize: 10.5, fontWeight: FontWeight.w600)),
    );
  }
}
