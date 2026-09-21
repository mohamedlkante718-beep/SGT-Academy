import 'dart:convert';

/// Décodage (sans vérification de signature) du contenu d'un token
/// JWT, uniquement pour lire le `sub` (id utilisateur) côté client et
/// le mettre en cache localement. La vérification d'authenticité du
/// token se fait toujours côté serveur à chaque appel API.
Map<String, dynamic> decodeJwtPayload(String token) {
  final parts = token.split('.');
  if (parts.length != 3) {
    throw const FormatException('Token JWT invalide');
  }
  return jsonDecode(_base64UrlDecode(parts[1])) as Map<String, dynamic>;
}

String _base64UrlDecode(String input) {
  var output = input.replaceAll('-', '+').replaceAll('_', '/');
  switch (output.length % 4) {
    case 2:
      output += '==';
    case 3:
      output += '=';
  }
  return utf8.decode(base64.decode(output));
}
