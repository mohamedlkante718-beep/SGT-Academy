import 'package:flutter/material.dart';

import 'app_theme.dart';
import 'models/app_user.dart';
import 'screens/depot_scanner_screen.dart';
import 'screens/frontiere_nouveau_controle_screen.dart';
import 'screens/login_screen.dart';
import 'screens/superviseur_dashboard_screen.dart';
import 'services/session_service.dart';

class TransitCarburantApp extends StatelessWidget {
  const TransitCarburantApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TransitCarburant',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(),
      home: const _RootRouter(),
    );
  }
}

/// Une session déjà ouverte sur cet appareil reste valable même sans
/// réseau (voir le cahier des charges) : on saute l'écran de
/// connexion tant qu'une session locale existe.
class _RootRouter extends StatelessWidget {
  const _RootRouter();

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<AppUser?>(
      future: SessionService().utilisateurCourant(),
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Scaffold(body: Center(child: CircularProgressIndicator()));
        }

        final user = snapshot.data;
        if (user == null) return const LoginScreen();

        return switch (user.role) {
          UserRole.agentFrontiere => const FrontiereNouveauControleScreen(),
          UserRole.agentDepot => const DepotScannerScreen(),
          UserRole.superviseur || UserRole.admin => const SuperviseurDashboardScreen(),
        };
      },
    );
  }
}
