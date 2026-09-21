import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../app_theme.dart';
import '../db/local_repository.dart';
import '../models/controle_depot.dart';
import '../models/manifeste.dart';

class HistoriqueDepotScreen extends StatefulWidget {
  const HistoriqueDepotScreen({super.key});

  @override
  State<HistoriqueDepotScreen> createState() => _HistoriqueDepotScreenState();
}

class _HistoriqueDepotScreenState extends State<HistoriqueDepotScreen> {
  final _repository = LocalRepository();
  late Future<List<(ControleDepot, Manifeste?)>> _futureControles;

  @override
  void initState() {
    super.initState();
    _futureControles = _charger();
  }

  Future<List<(ControleDepot, Manifeste?)>> _charger() async {
    final controles = await _repository.controlesRecents();
    final resultats = <(ControleDepot, Manifeste?)>[];
    for (final controle in controles) {
      final manifeste = await _repository.manifesteParId(controle.manifesteId);
      resultats.add((controle, manifeste));
    }
    return resultats;
  }

  Future<void> _rafraichir() async {
    setState(() => _futureControles = _charger());
    await _futureControles;
  }

  @override
  Widget build(BuildContext context) {
    final dateFormat = DateFormat('dd/MM — HH:mm');

    return Scaffold(
      appBar: AppBar(title: const Text('Historique')),
      body: FutureBuilder<List<(ControleDepot, Manifeste?)>>(
        future: _futureControles,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          final entries = snapshot.data ?? [];
          if (entries.isEmpty) {
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
              itemCount: entries.length,
              separatorBuilder: (context, index) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final (controle, manifeste) = entries[index];
                final valide = controle.resultat == ControleResultat.valide;
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
                            Text(
                              manifeste?.plaqueImmatriculation ?? 'Manifeste ${controle.manifesteId.substring(0, 8)}',
                              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14.5),
                            ),
                            if (manifeste != null) ...[
                              const SizedBox(height: 3),
                              Text(
                                '${manifeste.typeCargaison.label} · ${manifeste.quantiteDeclaree.toStringAsFixed(0)} ${manifeste.unite.apiValue}',
                                style: const TextStyle(fontSize: 12.5, color: AppColors.muted),
                              ),
                            ],
                            const SizedBox(height: 3),
                            Text(dateFormat.format(controle.dateControle.toLocal()), style: const TextStyle(fontSize: 11.5, color: AppColors.muted)),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: (valide ? AppColors.green : AppColors.red).withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          valide ? 'Validé' : 'Anomalie',
                          style: TextStyle(
                            color: valide ? AppColors.green : AppColors.red,
                            fontSize: 10.5,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
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
}
