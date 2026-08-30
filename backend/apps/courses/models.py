from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.common.models import SoftDeleteModel, TimeStampedModel


class Category(TimeStampedModel):
    name = models.CharField(max_length=100, verbose_name="nom")
    slug = models.SlugField(max_length=120, unique=True, blank=True, verbose_name="slug")
    description = models.TextField(blank=True, verbose_name="description")
    icon = models.CharField(
        max_length=50, blank=True, help_text="Nom d'icône (ex: map, leaf, laptop)", verbose_name="icône"
    )

    class Meta:
        verbose_name = "catégorie"
        verbose_name_plural = "catégories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Instructor(TimeStampedModel):
    """Profil formateur : un utilisateur avec le rôle INSTRUCTOR peut avoir ce profil étendu."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="instructor_profile",
        verbose_name="utilisateur",
    )
    headline = models.CharField(
        max_length=255, blank=True, help_text="Ex: Expert SIG & télédétection", verbose_name="accroche"
    )
    bio = models.TextField(blank=True, verbose_name="biographie")
    is_verified = models.BooleanField(default=False, verbose_name="vérifié")

    class Meta:
        verbose_name = "formateur"
        verbose_name_plural = "formateurs"

    def __str__(self):
        return self.user.get_full_name() or str(self.user)


class Course(SoftDeleteModel):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    STATUS_CHOICES = [
        (DRAFT, "Brouillon"),
        (PENDING_REVIEW, "En attente de validation"),
        (PUBLISHED, "Publiée"),
        (ARCHIVED, "Archivée"),
    ]

    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    LEVEL_CHOICES = [
        (BEGINNER, "Débutant"),
        (INTERMEDIATE, "Intermédiaire"),
        (ADVANCED, "Avancé"),
    ]

    title = models.CharField(max_length=200, verbose_name="titre")
    slug = models.SlugField(max_length=220, unique=True, blank=True, verbose_name="slug")
    short_description = models.CharField(max_length=300, blank=True, verbose_name="description courte")
    description = models.TextField(blank=True, verbose_name="description")
    objectives = models.JSONField(
        default=list, blank=True, help_text="Liste des objectifs pédagogiques", verbose_name="objectifs"
    )
    skills_acquired = models.JSONField(default=list, blank=True, verbose_name="compétences acquises")
    prerequisites = models.JSONField(default=list, blank=True, verbose_name="prérequis")

    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default=BEGINNER, verbose_name="niveau")
    duration_hours = models.PositiveIntegerField(default=0, verbose_name="durée (heures)")

    price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="prix")
    promo_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="prix promotionnel"
    )
    currency = models.CharField(
        max_length=3, default="XOF", help_text="XOF, XAF, EUR, USD... (§36)", verbose_name="devise"
    )

    cover_image = models.ImageField(
        upload_to="courses/covers/", null=True, blank=True, verbose_name="image de couverture"
    )
    certificate_available = models.BooleanField(default=True, verbose_name="certificat disponible")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT, verbose_name="statut")

    # SEO (§38)
    seo_title = models.CharField(max_length=70, blank=True, verbose_name="titre SEO")
    seo_description = models.CharField(max_length=160, blank=True, verbose_name="description SEO")

    language = models.CharField(max_length=5, default="fr", verbose_name="langue")

    categories = models.ManyToManyField(
        Category, through="CourseCategory", related_name="courses", verbose_name="catégories"
    )
    instructors = models.ManyToManyField(
        Instructor, through="InstructorCourse", related_name="courses", verbose_name="formateurs"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["slug"])]
        verbose_name = "formation"
        verbose_name_plural = "formations"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class CourseCategory(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="formation")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="catégorie")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["course", "category"], name="unique_course_category"),
        ]
        verbose_name = "catégorie de formation"
        verbose_name_plural = "catégories de formation"


class InstructorCourse(TimeStampedModel):
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, verbose_name="formateur")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="formation")
    is_primary = models.BooleanField(default=True, verbose_name="principal")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["instructor", "course"], name="unique_instructor_course"),
        ]
        verbose_name = "formateur de formation"
        verbose_name_plural = "formateurs de formation"


class Module(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules", verbose_name="formation")
    title = models.CharField(max_length=200, verbose_name="titre")
    description = models.TextField(blank=True, verbose_name="description")
    order = models.PositiveIntegerField(default=0, verbose_name="ordre")

    class Meta:
        ordering = ["course", "order"]
        constraints = [
            models.UniqueConstraint(fields=["course", "order"], name="unique_module_order_per_course"),
        ]
        verbose_name = "module"
        verbose_name_plural = "modules"

    def __str__(self):
        return f"{self.course.title} — Module {self.order}: {self.title}"


class Lesson(TimeStampedModel):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons", verbose_name="module")
    title = models.CharField(max_length=200, verbose_name="titre")
    description = models.TextField(blank=True, verbose_name="description")

    # Clé de stockage objet (jamais une URL publique permanente — §15/§16).
    video_storage_key = models.CharField(max_length=500, blank=True, verbose_name="clé de stockage vidéo")
    duration_seconds = models.PositiveIntegerField(default=0, verbose_name="durée (secondes)")

    order = models.PositiveIntegerField(default=0, verbose_name="ordre")
    is_preview = models.BooleanField(
        default=False, help_text="Visible gratuitement avant achat (§9)", verbose_name="aperçu gratuit"
    )

    class Meta:
        ordering = ["module", "order"]
        constraints = [
            models.UniqueConstraint(fields=["module", "order"], name="unique_lesson_order_per_module"),
        ]
        verbose_name = "leçon"
        verbose_name_plural = "leçons"

    def __str__(self):
        return self.title


class LessonResource(TimeStampedModel):
    PDF = "PDF"
    FILE = "FILE"
    LINK = "LINK"
    TYPE_CHOICES = [(PDF, "PDF"), (FILE, "Fichier"), (LINK, "Lien")]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="resources", verbose_name="leçon")
    title = models.CharField(max_length=200, verbose_name="titre")
    resource_type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default=PDF, verbose_name="type de ressource"
    )
    storage_key = models.CharField(max_length=500, blank=True, verbose_name="clé de stockage")
    external_url = models.URLField(blank=True, verbose_name="URL externe")
    order = models.PositiveIntegerField(default=0, verbose_name="ordre")

    class Meta:
        ordering = ["lesson", "order"]
        verbose_name = "ressource de leçon"
        verbose_name_plural = "ressources de leçon"

    def __str__(self):
        return self.title
