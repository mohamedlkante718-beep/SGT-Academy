import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Palette identique au site public (voir frontend-web/src/app/globals.css)
/// et au concept d'identité visuelle — un seul système partagé.
class SgtColors {
  static const primary = Color(0xFF1E7A46);
  static const primaryDark = Color(0xFF145C34);
  static const primaryLight = Color(0xFFEAF6EE);
  static const ink = Color(0xFF16201A);
  static const muted = Color(0xFF5B6B63);
  static const border = Color(0xFFE2E8E4);
}

ThemeData buildSgtTheme() {
  final textTheme = GoogleFonts.interTextTheme().copyWith(
    headlineMedium: GoogleFonts.sora(fontWeight: FontWeight.w800, color: SgtColors.ink),
    headlineSmall: GoogleFonts.sora(fontWeight: FontWeight.w700, color: SgtColors.ink),
    titleLarge: GoogleFonts.sora(fontWeight: FontWeight.w700, color: SgtColors.ink),
    titleMedium: GoogleFonts.sora(fontWeight: FontWeight.w600, color: SgtColors.ink),
  );

  return ThemeData(
    useMaterial3: true,
    scaffoldBackgroundColor: Colors.white,
    colorScheme: ColorScheme.fromSeed(
      seedColor: SgtColors.primary,
      primary: SgtColors.primary,
      surface: Colors.white,
    ),
    textTheme: textTheme,
    appBarTheme: const AppBarTheme(
      backgroundColor: Colors.white,
      foregroundColor: SgtColors.ink,
      elevation: 0,
      surfaceTintColor: Colors.white,
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: SgtColors.primary,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        textStyle: GoogleFonts.inter(fontWeight: FontWeight.w600, fontSize: 15),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: SgtColors.border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: SgtColors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: SgtColors.primary, width: 1.5),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    ),
    cardTheme: CardThemeData(
      color: Colors.white,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: const BorderSide(color: SgtColors.border),
      ),
    ),
  );
}
