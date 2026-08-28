class SgtUser {
  final String id;
  final String email;
  final String firstName;
  final String lastName;
  final List<String> roles;

  SgtUser({
    required this.id,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.roles,
  });

  factory SgtUser.fromJson(Map<String, dynamic> json) {
    return SgtUser(
      id: json['id'] as String,
      email: json['email'] as String,
      firstName: json['first_name'] as String,
      lastName: json['last_name'] as String,
      roles: (json['roles'] as List).map((r) => r.toString()).toList(),
    );
  }

  String get fullName => '$firstName $lastName';
}
