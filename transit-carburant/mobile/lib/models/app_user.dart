enum UserRole { agentFrontiere, agentDepot, superviseur, admin }

extension UserRoleApi on UserRole {
  static UserRole fromApi(String value) {
    switch (value) {
      case 'agent_frontiere':
        return UserRole.agentFrontiere;
      case 'agent_depot':
        return UserRole.agentDepot;
      case 'superviseur':
        return UserRole.superviseur;
      default:
        return UserRole.admin;
    }
  }
}

class AppUser {
  final String id;
  final String matricule;
  final String nomComplet;
  final UserRole role;
  final String? posteId;

  const AppUser({
    required this.id,
    required this.matricule,
    required this.nomComplet,
    required this.role,
    this.posteId,
  });
}
