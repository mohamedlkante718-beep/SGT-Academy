import logging

from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_verification_code_email(user, code: str) -> None:
    """
    Envoie le code de vérification à l'apprenant. Ne doit jamais faire
    échouer l'inscription si l'envoi rate (même logique que pour l'email
    de confirmation de paiement) — l'utilisateur peut toujours redemander
    un code via /auth/resend-verification/.
    """
    try:
        send_mail(
            subject="Votre code de vérification SGT Academy",
            message=(
                f"Bonjour {user.first_name or ''},\n\n"
                f"Voici votre code de vérification : {code}\n"
                f"Ce code est valable 30 minutes.\n\n"
                f"Si vous n'êtes pas à l'origine de cette inscription, ignorez cet email.\n\n"
                f"L'équipe SGT Academy"
            ),
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Échec de l'envoi du code de vérification (utilisateur=%s)", user.email
        )
