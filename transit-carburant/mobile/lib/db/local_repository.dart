import 'package:sqflite/sqflite.dart';

import '../models/controle_depot.dart';
import '../models/manifeste.dart';
import '../models/poste.dart';
import 'database_helper.dart';

/// Accès aux données locales : c'est la seule dépendance des écrans
/// pour lire/écrire des manifestes et des contrôles. Le service de
/// synchronisation lit ce même repository pour savoir quoi envoyer.
class LocalRepository {
  Future<Database> get _db => DatabaseHelper.instance.database;

  Future<void> insertManifeste(Manifeste manifeste) async {
    final db = await _db;
    await db.insert(
      'manifestes',
      manifeste.toDbMap(),
      conflictAlgorithm: ConflictAlgorithm.abort,
    );
  }

  Future<List<Manifeste>> manifestesNonSynchronises() async {
    final db = await _db;
    final rows = await db.query(
      'manifestes',
      where: 'sync_status = ?',
      whereArgs: ['localOnly'],
      orderBy: 'date_creation ASC',
    );
    return rows.map(Manifeste.fromDbMap).toList();
  }

  Future<List<Manifeste>> manifestesRecents({int limit = 50}) async {
    final db = await _db;
    final rows = await db.query('manifestes', orderBy: 'date_creation DESC', limit: limit);
    return rows.map(Manifeste.fromDbMap).toList();
  }

  Future<Manifeste?> manifesteParId(String id) async {
    final db = await _db;
    final rows = await db.query('manifestes', where: 'id = ?', whereArgs: [id], limit: 1);
    if (rows.isEmpty) return null;
    return Manifeste.fromDbMap(rows.first);
  }

  Future<void> marquerManifesteSynchronise(String id) async {
    final db = await _db;
    await db.update(
      'manifestes',
      {'sync_status': 'synced'},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> insertControleDepot(ControleDepot controle) async {
    final db = await _db;
    await db.insert('controles_depot', controle.toDbMap());
    await db.update(
      'manifestes',
      {
        'statut': controle.resultat == ControleResultat.valide ? 'valide' : 'anomalie',
      },
      where: 'id = ?',
      whereArgs: [controle.manifesteId],
    );
  }

  Future<List<ControleDepot>> controlesRecents({int limit = 50}) async {
    final db = await _db;
    final rows = await db.query('controles_depot', orderBy: 'date_controle DESC', limit: limit);
    return rows.map(ControleDepot.fromDbMap).toList();
  }

  Future<List<ControleDepot>> controlesNonSynchronises() async {
    final db = await _db;
    final rows = await db.query(
      'controles_depot',
      where: 'sync_status = ?',
      whereArgs: ['localOnly'],
    );
    return rows.map(ControleDepot.fromDbMap).toList();
  }

  Future<void> marquerControleSynchronise(String id) async {
    final db = await _db;
    await db.update(
      'controles_depot',
      {'sync_status': 'synced'},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> enregistrerPostes(List<Poste> postes) async {
    final db = await _db;
    final batch = db.batch();
    for (final poste in postes) {
      batch.insert('postes', poste.toMap(), conflictAlgorithm: ConflictAlgorithm.replace);
    }
    await batch.commit(noResult: true);
  }

  Future<List<Poste>> postesLocaux() async {
    final db = await _db;
    final rows = await db.query('postes');
    return rows.map(Poste.fromMap).toList();
  }

  Future<Poste?> posteParId(String id) async {
    final db = await _db;
    final rows = await db.query('postes', where: 'id = ?', whereArgs: [id], limit: 1);
    if (rows.isEmpty) return null;
    return Poste.fromMap(rows.first);
  }
}
