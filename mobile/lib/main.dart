import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme.dart';
import 'routes/app_router.dart';

void main() {
  runApp(const ProviderScope(child: SgtAcademyApp()));
}

class SgtAcademyApp extends ConsumerWidget {
  const SgtAcademyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'SGT Academy',
      debugShowCheckedModeBanner: false,
      theme: buildSgtTheme(),
      routerConfig: router,
    );
  }
}
