enum Cargaison { essence, gasoil, gazButane }

extension CargaisonApi on Cargaison {
  String get apiValue => switch (this) {
        Cargaison.essence => 'essence',
        Cargaison.gasoil => 'gasoil',
        Cargaison.gazButane => 'gaz_butane',
      };

  String get label => switch (this) {
        Cargaison.essence => 'Essence',
        Cargaison.gasoil => 'Gasoil',
        Cargaison.gazButane => 'Gaz butane',
      };
}

enum Unite { litres, kg }

extension UniteApi on Unite {
  String get apiValue => name;
}

enum ManifesteStatut { genere, enRoute, controleDepot, valide, anomalie }

enum SyncStatus { localOnly, synced, conflict }

/// Un contrôle créé au poste frontière : les champs déclarés par
/// l'agent, plus la signature numérique calculée par [CryptoService]
/// sur le contenu canonique (voir `docs/DB-SCHEMA.md`).
class Manifeste {
  final String id;
  final String plaqueImmatriculation;
  final String? typeCiterne;
  final String transporteurNom;
  final String? transporteurTelephone;
  final String chauffeurNom;
  final String chauffeurPieceIdentite;
  final String? chauffeurTelephone;
  final String posteFrontiereId;
  final String depotDestinationId;
  final Cargaison typeCargaison;
  final double quantiteDeclaree;
  final Unite unite;
  final String numeroScelle;
  final String? photoPath;
  final String agentFrontiereId;
  final String signatureNumerique;
  final DateTime dateCreation;
  final ManifesteStatut statut;
  final SyncStatus syncStatus;

  const Manifeste({
    required this.id,
    required this.plaqueImmatriculation,
    this.typeCiterne,
    required this.transporteurNom,
    this.transporteurTelephone,
    required this.chauffeurNom,
    required this.chauffeurPieceIdentite,
    this.chauffeurTelephone,
    required this.posteFrontiereId,
    required this.depotDestinationId,
    required this.typeCargaison,
    required this.quantiteDeclaree,
    required this.unite,
    required this.numeroScelle,
    this.photoPath,
    required this.agentFrontiereId,
    required this.signatureNumerique,
    required this.dateCreation,
    this.statut = ManifesteStatut.genere,
    this.syncStatus = SyncStatus.localOnly,
  });

  /// Champs et ordre EXACTS qui doivent être signés — identiques à
  /// `build_manifeste_payload` côté backend (app/security.py).
  String canonicalPayload() {
    final quantite = quantiteDeclaree.toStringAsFixed(3);
    return [
      id,
      plaqueImmatriculation,
      transporteurNom,
      chauffeurNom,
      typeCargaison.apiValue,
      quantite,
      unite.apiValue,
      numeroScelle,
      posteFrontiereId,
      depotDestinationId,
      dateCreation.toUtc().toIso8601String(),
    ].join('|');
  }

  Map<String, Object?> toSyncJson() => {
        'id': id,
        'plaque_immatriculation': plaqueImmatriculation,
        'type_citerne': typeCiterne,
        'transporteur_nom': transporteurNom,
        'transporteur_telephone': transporteurTelephone,
        'chauffeur_nom': chauffeurNom,
        'chauffeur_piece_identite': chauffeurPieceIdentite,
        'chauffeur_telephone': chauffeurTelephone,
        'poste_frontiere_id': posteFrontiereId,
        'depot_destination_id': depotDestinationId,
        'type_cargaison': typeCargaison.apiValue,
        'quantite_declaree': quantiteDeclaree,
        'unite': unite.apiValue,
        'numero_scelle': numeroScelle,
        'photo_path': photoPath,
        'agent_frontiere_id': agentFrontiereId,
        'signature_numerique': signatureNumerique,
        'date_creation': dateCreation.toUtc().toIso8601String(),
      };

  /// Contenu encodé dans le QR remis au chauffeur : le manifeste
  /// complet + sa signature, pour une vérification hors ligne au
  /// dépôt sans dépendre du serveur.
  Map<String, Object?> toQrPayload() => toSyncJson();

  Map<String, Object?> toDbMap() => {
        ...toSyncJson(),
        'statut': statut.name,
        'sync_status': syncStatus.name,
      };

  /// Reconstruit un manifeste à partir du contenu décodé d'un QR
  /// scanné au dépôt (mêmes clés que [toSyncJson]).
  factory Manifeste.fromQrJson(Map<String, Object?> json) => Manifeste(
        id: json['id'] as String,
        plaqueImmatriculation: json['plaque_immatriculation'] as String,
        typeCiterne: json['type_citerne'] as String?,
        transporteurNom: json['transporteur_nom'] as String,
        transporteurTelephone: json['transporteur_telephone'] as String?,
        chauffeurNom: json['chauffeur_nom'] as String,
        chauffeurPieceIdentite: json['chauffeur_piece_identite'] as String,
        chauffeurTelephone: json['chauffeur_telephone'] as String?,
        posteFrontiereId: json['poste_frontiere_id'] as String,
        depotDestinationId: json['depot_destination_id'] as String,
        typeCargaison: Cargaison.values.firstWhere((c) => c.apiValue == json['type_cargaison']),
        quantiteDeclaree: (json['quantite_declaree'] as num).toDouble(),
        unite: Unite.values.byName(json['unite'] as String),
        numeroScelle: json['numero_scelle'] as String,
        photoPath: json['photo_path'] as String?,
        agentFrontiereId: json['agent_frontiere_id'] as String,
        signatureNumerique: json['signature_numerique'] as String,
        dateCreation: DateTime.parse(json['date_creation'] as String),
      );

  factory Manifeste.fromDbMap(Map<String, Object?> map) => Manifeste(
        id: map['id'] as String,
        plaqueImmatriculation: map['plaque_immatriculation'] as String,
        typeCiterne: map['type_citerne'] as String?,
        transporteurNom: map['transporteur_nom'] as String,
        transporteurTelephone: map['transporteur_telephone'] as String?,
        chauffeurNom: map['chauffeur_nom'] as String,
        chauffeurPieceIdentite: map['chauffeur_piece_identite'] as String,
        chauffeurTelephone: map['chauffeur_telephone'] as String?,
        posteFrontiereId: map['poste_frontiere_id'] as String,
        depotDestinationId: map['depot_destination_id'] as String,
        typeCargaison: Cargaison.values.firstWhere(
          (c) => c.apiValue == map['type_cargaison'],
        ),
        quantiteDeclaree: (map['quantite_declaree'] as num).toDouble(),
        unite: Unite.values.byName(map['unite'] as String),
        numeroScelle: map['numero_scelle'] as String,
        photoPath: map['photo_path'] as String?,
        agentFrontiereId: map['agent_frontiere_id'] as String,
        signatureNumerique: map['signature_numerique'] as String,
        dateCreation: DateTime.parse(map['date_creation'] as String),
        statut: ManifesteStatut.values.byName(map['statut'] as String),
        syncStatus: SyncStatus.values.byName(map['sync_status'] as String),
      );

  Manifeste copyWith({ManifesteStatut? statut, SyncStatus? syncStatus}) => Manifeste(
        id: id,
        plaqueImmatriculation: plaqueImmatriculation,
        typeCiterne: typeCiterne,
        transporteurNom: transporteurNom,
        transporteurTelephone: transporteurTelephone,
        chauffeurNom: chauffeurNom,
        chauffeurPieceIdentite: chauffeurPieceIdentite,
        chauffeurTelephone: chauffeurTelephone,
        posteFrontiereId: posteFrontiereId,
        depotDestinationId: depotDestinationId,
        typeCargaison: typeCargaison,
        quantiteDeclaree: quantiteDeclaree,
        unite: unite,
        numeroScelle: numeroScelle,
        photoPath: photoPath,
        agentFrontiereId: agentFrontiereId,
        signatureNumerique: signatureNumerique,
        dateCreation: dateCreation,
        statut: statut ?? this.statut,
        syncStatus: syncStatus ?? this.syncStatus,
      );
}
