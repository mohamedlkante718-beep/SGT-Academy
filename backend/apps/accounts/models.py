import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.common.models import SoftDeleteModel, TimeStampedModel


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un superuser doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superuser doit avoir is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, SoftDeleteModel):
    """
    Utilisateur de la plateforme. La connexion se fait par email (§10).
    Les rôles métier (SUPER_ADMIN, ADMIN, FORMATEUR, APPRENANT, ADMIN_ENTREPRISE)
    sont gérés via le modèle Role/UserRole, pas via is_staff/is_superuser seuls
    (qui restent réservés à l'admin Django).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="identifiant")
    email = models.EmailField(unique=True, verbose_name="adresse email")
    phone = models.CharField(max_length=32, unique=True, null=True, blank=True, verbose_name="téléphone")
    first_name = models.CharField(max_length=150, verbose_name="prénom")
    last_name = models.CharField(max_length=150, verbose_name="nom")
    country = models.CharField(
        max_length=2, default="ML", help_text="Code pays ISO 3166-1 alpha-2", verbose_name="pays"
    )

    is_active = models.BooleanField(default=True, verbose_name="actif")
    is_staff = models.BooleanField(default=False, verbose_name="membre du personnel")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="date d'inscription")

    # Vérification de l'adresse email par code à l'inscription. Le code n'est
    # jamais comparé globalement : on retrouve d'abord LE compte par son email,
    # puis on compare le code uniquement sur cette fiche précise — le code
    # d'un compte ne peut donc jamais valider un autre compte.
    email_verified = models.BooleanField(default=False, verbose_name="email vérifié")
    email_verification_code = models.CharField(
        max_length=6, blank=True, null=True, verbose_name="code de vérification"
    )
    email_verification_expires_at = models.DateTimeField(
        blank=True, null=True, verbose_name="expiration du code"
    )

    roles = models.ManyToManyField("Role", through="UserRole", related_name="users", verbose_name="rôles")

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        indexes = [models.Index(fields=["phone"])]
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def has_role(self, role_name: str) -> bool:
        return self.roles.filter(name=role_name).exists()

    def generate_email_verification_code(self) -> str:
        """Génère un nouveau code à 6 chiffres, valable 30 minutes, et l'enregistre."""
        import secrets

        from django.utils import timezone

        code = f"{secrets.randbelow(1_000_000):06d}"
        self.email_verification_code = code
        self.email_verification_expires_at = timezone.now() + timezone.timedelta(minutes=30)
        self.save(update_fields=["email_verification_code", "email_verification_expires_at"])
        return code


class Role(models.Model):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    INSTRUCTOR = "INSTRUCTOR"
    LEARNER = "LEARNER"
    COMPANY_ADMIN = "COMPANY_ADMIN"

    NAME_CHOICES = [
        (SUPER_ADMIN, "Super administrateur"),
        (ADMIN, "Administrateur"),
        (INSTRUCTOR, "Formateur"),
        (LEARNER, "Apprenant"),
        (COMPANY_ADMIN, "Administrateur entreprise"),
    ]

    name = models.CharField(max_length=50, choices=NAME_CHOICES, unique=True, verbose_name="nom")
    description = models.CharField(max_length=255, blank=True, verbose_name="description")
    permissions = models.ManyToManyField(
        "Permission", blank=True, related_name="roles", verbose_name="permissions"
    )

    class Meta:
        verbose_name = "rôle"
        verbose_name_plural = "rôles"

    def __str__(self):
        return self.get_name_display()


class Permission(models.Model):
    """Permission fine (distincte de auth.Permission de Django), ex: 'course.publish'."""

    codename = models.CharField(max_length=100, unique=True, verbose_name="code")
    description = models.CharField(max_length=255, blank=True, verbose_name="description")

    class Meta:
        verbose_name = "permission"
        verbose_name_plural = "permissions"

    def __str__(self):
        return self.codename


class UserRole(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles", verbose_name="utilisateur")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles", verbose_name="rôle")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="unique_user_role"),
        ]
        verbose_name = "rôle utilisateur"
        verbose_name_plural = "rôles utilisateur"

    def __str__(self):
        return f"{self.user} — {self.role}"


class Profile(TimeStampedModel):
    """Informations complémentaires, non liées à l'authentification."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile", verbose_name="utilisateur")
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True, verbose_name="avatar")
    bio = models.TextField(blank=True, verbose_name="biographie")
    birth_date = models.DateField(null=True, blank=True, verbose_name="date de naissance")
    preferred_language = models.CharField(max_length=5, default="fr", verbose_name="langue préférée")
    timezone = models.CharField(max_length=64, default="Africa/Bamako", verbose_name="fuseau horaire")

    class Meta:
        verbose_name = "profil"
        verbose_name_plural = "profils"

    def __str__(self):
        return f"Profil de {self.user}"
