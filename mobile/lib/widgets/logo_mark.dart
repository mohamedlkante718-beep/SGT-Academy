import 'package:flutter/material.dart';
import '../core/theme.dart';

/// Monogramme SGT Academy (identité retenue) — badge arrondi, "SGT" en blanc.
class LogoMark extends StatelessWidget {
  final double size;
  const LogoMark({super.key, this.size = 40});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: SgtColors.primary,
        borderRadius: BorderRadius.circular(size * 0.22),
      ),
      alignment: Alignment.center,
      child: Text(
        'SGT',
        style: TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.w800,
          fontSize: size * 0.32,
          letterSpacing: -0.5,
        ),
      ),
    );
  }
}
