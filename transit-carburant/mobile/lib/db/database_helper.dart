import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

/// Base SQLite locale de l'appareil.
///
/// Toutes les écritures critiques (créer un manifeste, enregistrer un
/// contrôle dépôt) passent par ici et fonctionnent sans réseau. La
/// synchronisation (voir `services/sync_service.dart`) ne fait que
/// pousser vers le serveur ce qui est déjà écrit ici, jamais l'inverse
/// pour les données créées sur cet appareil.
class DatabaseHelper {
  DatabaseHelper._();
  static final DatabaseHelper instance = DatabaseHelper._();

  Database? _db;

  Future<Database> get database async {
    _db ??= await _open();
    return _db!;
  }

  Future<Database> _open() async {
    final path = join(await getDatabasesPath(), 'transit_carburant.db');
    return openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE postes (
            id TEXT PRIMARY KEY,
            nom TEXT NOT NULL,
            type TEXT NOT NULL,
            ville TEXT NOT NULL,
            cle_publique TEXT
          )
        ''');

        await db.execute('''
          CREATE TABLE manifestes (
            id TEXT PRIMARY KEY,
            plaque_immatriculation TEXT NOT NULL,
            type_citerne TEXT,
            transporteur_nom TEXT NOT NULL,
            transporteur_telephone TEXT,
            chauffeur_nom TEXT NOT NULL,
            chauffeur_piece_identite TEXT NOT NULL,
            chauffeur_telephone TEXT,
            poste_frontiere_id TEXT NOT NULL,
            depot_destination_id TEXT NOT NULL,
            type_cargaison TEXT NOT NULL,
            quantite_declaree REAL NOT NULL,
            unite TEXT NOT NULL,
            numero_scelle TEXT NOT NULL,
            photo_path TEXT,
            agent_frontiere_id TEXT NOT NULL,
            signature_numerique TEXT NOT NULL,
            date_creation TEXT NOT NULL,
            statut TEXT NOT NULL DEFAULT 'genere',
            sync_status TEXT NOT NULL DEFAULT 'localOnly'
          )
        ''');

        await db.execute('''
          CREATE TABLE controles_depot (
            id TEXT PRIMARY KEY,
            manifeste_id TEXT NOT NULL,
            agent_depot_id TEXT NOT NULL,
            scelle_intact INTEGER NOT NULL,
            quantite_conforme INTEGER NOT NULL,
            remarque TEXT,
            resultat TEXT NOT NULL,
            date_controle TEXT NOT NULL,
            sync_status TEXT NOT NULL DEFAULT 'localOnly'
          )
        ''');
      },
    );
  }

  Future<void> close() async {
    final db = _db;
    if (db != null) {
      await db.close();
      _db = null;
    }
  }
}
