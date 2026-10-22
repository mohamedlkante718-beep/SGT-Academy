from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter
def nombre(v):
    """1234567 → « 1 234 567 » ; None → « — »."""
    if v is None or v == "":
        return "—"
    try:
        n = round(float(v))
    except (TypeError, ValueError):
        return v
    return f"{n:,}".replace(",", " ")


@register.filter
def get(d, k):
    return d.get(k) if d else None


@register.simple_tag
def pastille(evo, unite=""):
    """Pastille d'évolution : ▲ hausse (vert), ▼ baisse (rouge), = stable, ou 1re saisie."""
    if not evo:
        return format_html('<span class="muted">—</span>')
    etat = evo["etat"]
    if etat == "nouveau":
        return format_html('<span class="pill new">{}</span>', "1re saisie" if evo.get("ecart") is None else "nouveau")
    if etat == "absent":
        return format_html('<span class="pill flat">non renseigné</span>')
    if etat == "stable":
        return format_html('<span class="pill flat">= stable</span>')
    ecart = evo["ecart"]
    fleche = "▲ +" if ecart > 0 else "▼ "
    pct = f" ({'+' if ecart > 0 else ''}{str(evo['pct']).replace('.', ',')} %)" if evo.get("pct") is not None else ""
    classe = "up" if etat == "hausse" else "down"
    return format_html('<span class="pill {}">{}{}{}{}</span>', classe, fleche, nombre(ecart), unite, pct)
