"""Calculs partagés : semaines, comparaison avec la fiche précédente, récapitulatif."""

import unicodedata
from datetime import date, timedelta

from django.conf import settings


def debut_semaine(jour=None):
    """Premier jour de la semaine de suivi contenant `jour`."""
    jour = jour or date.today()
    return jour - timedelta(days=(jour.weekday() - settings.SEMAINE_JOUR_DEBUT) % 7)


def cle(libelle):
    """Clé de comparaison d'un libellé : insensible aux accents, à la casse et aux espaces."""
    s = unicodedata.normalize("NFD", libelle or "").encode("ascii", "ignore").decode()
    return " ".join(s.lower().split())


def est_mortalite(libelle):
    return "mort" in cle(libelle)


def evolution(precedent, actuel, inverse=False):
    """Décrit l'écart entre deux valeurs. `inverse` : une hausse est mauvaise (mortalités)."""
    if actuel is None:
        return None
    if precedent is None:
        return {"etat": "nouveau", "ecart": None, "pct": None}
    ecart = actuel - precedent
    if ecart == 0:
        etat = "stable"
    else:
        bon = ecart < 0 if inverse else ecart > 0
        etat = "hausse" if bon else "baisse"
    pct = round(ecart / precedent * 100, 1) if precedent else None
    return {"etat": etat, "ecart": ecart, "pct": pct, "monte": ecart > 0}


def comparer_lignes(actuelles, precedentes, attr):
    """Associe chaque ligne actuelle à la ligne de même libellé de la fiche précédente."""
    prec = {cle(l.libelle): getattr(l, attr) for l in precedentes} if precedentes is not None else None
    lignes, vues = [], set()
    for l in actuelles:
        k = cle(l.libelle)
        vues.add(k)
        p = prec.get(k) if prec is not None else None
        a = getattr(l, attr)
        if prec is not None and k not in prec:
            evo = {"etat": "nouveau", "ecart": None, "pct": None}
        else:
            evo = evolution(p, a, inverse=est_mortalite(l.libelle))
        lignes.append({"libelle": l.libelle, "precedent": p, "actuel": a, "evo": evo})
    for l in precedentes or []:
        if cle(l.libelle) not in vues:
            lignes.append({"libelle": l.libelle, "precedent": getattr(l, attr), "actuel": None,
                           "evo": {"etat": "absent"}})
    return lignes


def recapitulatif(semaine, producteurs):
    """Une ligne par producteur pour la semaine donnée, plus les totaux."""
    from .models import Fiche

    fiches = {f.producteur_id: f for f in Fiche.objects.filter(semaine=semaine)
              .prefetch_related("valeurs", "depenses", "ventes")}
    lignes = []
    tot = {"precedent": 0, "actuel": 0, "depenses": 0, "ventes": 0, "prets": 0, "a_precedent": False}
    for p in producteurs:
        f = fiches.get(p.id)
        pf = p.fiche_precedente(semaine)
        ligne = {
            "producteur": p,
            "fiche": f,
            "precedent": pf.total_valeurs if pf else None,
            "actuel": f.total_valeurs if f else None,
            "depenses": f.total_depenses if f else None,
            "ventes": f.total_ventes if f else None,
            "resultat": f.resultat_net if f else None,
            "prets": p.prets_en_cours(jusqu_au=semaine + timedelta(days=6)),
        }
        ligne["evo"] = evolution(ligne["precedent"], ligne["actuel"]) if f else None
        if f:
            tot["actuel"] += ligne["actuel"]
            tot["depenses"] += ligne["depenses"]
            tot["ventes"] += ligne["ventes"]
        if pf:
            tot["precedent"] += ligne["precedent"]
            tot["a_precedent"] = True
        tot["prets"] += ligne["prets"]
        lignes.append(ligne)
    tot["resultat"] = tot["ventes"] - tot["depenses"]
    tot["evo"] = evolution(tot["precedent"] if tot["a_precedent"] else None, tot["actuel"])
    return lignes, tot
