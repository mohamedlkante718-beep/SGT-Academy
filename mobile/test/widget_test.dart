import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:sgt_academy/main.dart';

void main() {
  testWidgets('Affiche l\'écran de connexion au démarrage', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: SgtAcademyApp()));
    await tester.pumpAndSettle();

    expect(find.text('SGT Academy'), findsOneWidget);
    expect(find.text('Se connecter'), findsOneWidget);
  });
}
