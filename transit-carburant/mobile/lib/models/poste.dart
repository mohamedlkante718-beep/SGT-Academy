enum PosteType { frontiere, depot }

class Poste {
  final String id;
  final String nom;
  final PosteType type;
  final String ville;
  final String? clePublique;

  const Poste({
    required this.id,
    required this.nom,
    required this.type,
    required this.ville,
    this.clePublique,
  });

  Map<String, Object?> toMap() => {
        'id': id,
        'nom': nom,
        'type': type.name,
        'ville': ville,
        'cle_publique': clePublique,
      };

  factory Poste.fromMap(Map<String, Object?> map) => Poste(
        id: map['id'] as String,
        nom: map['nom'] as String,
        type: PosteType.values.byName(map['type'] as String),
        ville: map['ville'] as String,
        clePublique: map['cle_publique'] as String?,
      );
}
