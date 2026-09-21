enum ControleResultat { valide, anomalie }

class ControleDepot {
  final String id;
  final String manifesteId;
  final String agentDepotId;
  final bool scelleIntact;
  final bool quantiteConforme;
  final String? remarque;
  final ControleResultat resultat;
  final DateTime dateControle;

  const ControleDepot({
    required this.id,
    required this.manifesteId,
    required this.agentDepotId,
    required this.scelleIntact,
    required this.quantiteConforme,
    this.remarque,
    required this.resultat,
    required this.dateControle,
  });

  Map<String, Object?> toSyncJson() => {
        'id': id,
        'manifeste_id': manifesteId,
        'agent_depot_id': agentDepotId,
        'scelle_intact': scelleIntact,
        'quantite_conforme': quantiteConforme,
        'remarque': remarque,
        'resultat': resultat.name,
        'date_controle': dateControle.toUtc().toIso8601String(),
      };

  Map<String, Object?> toDbMap() => {
        ...toSyncJson(),
        'sync_status': 'localOnly',
      };

  factory ControleDepot.fromDbMap(Map<String, Object?> map) => ControleDepot(
        id: map['id'] as String,
        manifesteId: map['manifeste_id'] as String,
        agentDepotId: map['agent_depot_id'] as String,
        scelleIntact: (map['scelle_intact'] as int) == 1,
        quantiteConforme: (map['quantite_conforme'] as int) == 1,
        remarque: map['remarque'] as String?,
        resultat: ControleResultat.values.byName(map['resultat'] as String),
        dateControle: DateTime.parse(map['date_controle'] as String),
      );
}
