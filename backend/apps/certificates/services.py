from io import BytesIO

import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone

from .models import Certificate


def _course_code(course) -> str:
    slug_part = course.slug.split("-")[0] if course.slug else "COURS"
    return slug_part.upper()[:10]


def generate_unique_code(course) -> str:
    year = timezone.now().year
    prefix = _course_code(course)
    sequence = Certificate.objects.filter(course=course).count() + 1
    return f"SGT-{year}-{prefix}-{sequence:06d}"


def issue_certificate(user, course) -> Certificate:
    """
    Émet le certificat d'un apprenant pour une formation (§19), de façon
    idempotente : si un certificat existe déjà pour ce couple (utilisateur,
    formation), il est renvoyé tel quel plutôt que dupliqué.
    """
    existing = Certificate.objects.filter(user=user, course=course).first()
    if existing:
        return existing

    instructor = course.instructors.first()
    certificate = Certificate.objects.create(
        user=user,
        course=course,
        code=generate_unique_code(course),
        learner_name_snapshot=user.get_full_name(),
        course_title_snapshot=course.title,
        instructor_name_snapshot=instructor.user.get_full_name() if instructor else "",
        duration_hours_snapshot=course.duration_hours,
    )
    _generate_qr_code(certificate)

    # NOTE (§53) : la génération du PDF officiel (mise en page, logo, signature)
    # n'est pas implémentée ici — elle nécessite un template graphique validé
    # par Safe Green Tech et le choix d'un moteur de rendu (WeasyPrint/ReportLab).
    # `pdf_storage_key` reste volontairement vide tant que ce n'est pas fait.
    return certificate


def _generate_qr_code(certificate: Certificate) -> None:
    verify_path = f"/verify/{certificate.code}"
    target = f"{settings.PUBLIC_SITE_URL}{verify_path}" if settings.PUBLIC_SITE_URL else verify_path

    img = qrcode.make(target)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    storage_key = default_storage.save(
        f"certificates/qr/{certificate.code}.png", ContentFile(buffer.getvalue())
    )
    certificate.qr_code_storage_key = storage_key
    certificate.save(update_fields=["qr_code_storage_key", "updated_at"])
