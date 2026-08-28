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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    country = models.CharField(max_length=2, default="ML", help_text="Code pays ISO 3166-1 alpha-2")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    roles = models.ManyToManyField("Role", through="UserRole", related_name="users")

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

    name = models.CharField(max_length=50, choices=NAME_CHOICES, unique=True)
    description = models.CharField(max_length=255, blank=True)
    permissions = models.ManyToManyField("Permission", blank=True, related_name="roles")

    class Meta:
        verbose_name = "rôle"
        verbose_name_plural = "rôles"

    def __str__(self):
        return self.get_name_display()


class Permission(models.Model):
    """Permission fine (distincte de auth.Permission de Django), ex: 'course.publish'."""

    codename = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "permission"
        verbose_name_plural = "permissions"

    def __str__(self):
        return self.codename


class UserRole(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")

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

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    preferred_language = models.CharField(max_length=5, default="fr")
    timezone = models.CharField(max_length=64, default="Africa/Bamako")

    class Meta:
        verbose_name = "profil"
        verbose_name_plural = "profils"

    def __str__(self):
        return f"Profil de {self.user}"
