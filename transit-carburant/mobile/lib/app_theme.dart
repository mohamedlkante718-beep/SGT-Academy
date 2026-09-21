import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Palette et typographie reprises des maquettes (voir l'artefact de
/// conception) : navy institutionnel, teal pour les actions positives,
/// orange pour les états "en attente", rouge pour les anomalies.
class AppColors {
  static const navy = Color(0xFF0F2A43);
  static const teal = Color(0xFF0E7C86);
  static const orange = Color(0xFFD97706);
  static const green = Color(0xFF15803D);
  static const red = Color(0xFFB91C1C);
  static const background = Color(0xFFF4F6F8);
  static const border = Color(0xFFE2E6EA);
  static const text = Color(0xFF10151B);
  static const muted = Color(0xFF5B6472);
}

ThemeData buildAppTheme() {
  final textTheme = GoogleFonts.ibmPlexSansTextTheme().copyWith(
    headlineSmall: GoogleFonts.spaceGrotesk(fontWeight: FontWeight.w700, fontSize: 20),
    titleLarge: GoogleFonts.spaceGrotesk(fontWeight: FontWeight.w600, fontSize: 17),
    titleMedium: GoogleFonts.spaceGrotesk(fontWeight: FontWeight.w600, fontSize: 15),
  );

  return ThemeData(
    useMaterial3: true,
    scaffoldBackgroundColor: AppColors.background,
    colorScheme: ColorScheme.fromSeed(
      seedColor: AppColors.teal,
      primary: AppColors.teal,
      secondary: AppColors.navy,
      error: AppColors.red,
    ),
    textTheme: textTheme,
    appBarTheme: AppBarTheme(
      backgroundColor: AppColors.navy,
      foregroundColor: Colors.white,
      titleTextStyle: textTheme.titleLarge?.copyWith(color: Colors.white),
      elevation: 0,
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.teal,
        foregroundColor: Colors.white,
        minimumSize: const Size.fromHeight(50),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: AppColors.border),
      ),
    ),
  );
}
