#!/usr/bin/env python3
"""
Contre-expertise ENT Q9.3 — thème « Attractivité / image / com » (verbatims).

Dashboard : 38% (8/21). Premier auditeur : 9/21 (43%) par mots-clés.
Ce script recalcule de zéro, sans donnée en dur, et compare deux grilles
de codage pour objectiver la frontière :
  - Grille LARGE (lexicale) : toute mention d'attractivité / image /
    visibilité / communication / vidéo / atouts, quel que soit l'objet
    (territoire, métier, entreprise).
  - Grille STRICTE (attractivité TERRITORIALE) : mêmes mots-clés, mais on
    exclut les réponses dont l'objet est l'image de marque de l'ENTREPRISE
    elle-même (marque employeur individuelle, pas action territoriale).

Sorties : agrégats uniquement (n=, effectifs, %). Aucun verbatim imprimé.
Usage : python3 scripts/verif_ENT-Q9.3-2_recalcul.py
"""
import unicodedata

import pandas as pd

XLSX = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"
COL_IDX = 122  # Q9.3 — Si une seule action concrète devait sortir de cette démarche GPECT...

KEYWORDS = ["attractivite", "image", "visibilite", "communication", "video", "atouts"]
# Marqueurs d'un objet « entreprise » (marque employeur individuelle) :
# la réponse parle de l'image/visibilité DE L'ENTREPRISE, pas du territoire/métier.
ENTREPRISE_MARKERS = ["notre entreprise", "de l'entreprise", "image de marque"]
TERRITOIRE_MARKERS = ["territoire", "ville", "bassin d'issoudun", "issoudun", "metier", "usinage", "hors territoire"]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower()


def pct(k: int, n: int) -> int:
    # round half up, arrondi à l'entier (convention dashboard)
    import decimal
    return int((decimal.Decimal(k) * 100 / decimal.Decimal(n))
               .quantize(decimal.Decimal(1), rounding=decimal.ROUND_HALF_UP))


def main() -> None:
    df = pd.read_excel(XLSX, engine="openpyxl")
    print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")
    col = df.columns[COL_IDX]
    print(f"Colonne source [{COL_IDX}] : {col[:80]}...")

    serie = df[col].dropna().astype(str).str.strip()
    serie = serie[serie != ""]
    n = len(serie)
    print(f"n (réponses non vides) = {n}")

    large, stricte = [], []
    for pos, (_, v) in enumerate(serie.items(), start=1):
        t = norm(v)
        hits = [k for k in KEYWORDS if k in t]
        if not hits:
            continue
        rid = f"E{pos:02d}"
        large.append((rid, hits))
        obj_entreprise = any(m in t for m in (norm(x) for x in ENTREPRISE_MARKERS))
        obj_territoire = any(m in t for m in (norm(x) for x in TERRITOIRE_MARKERS))
        # Grille stricte : on exclut si l'objet est l'entreprise elle-même
        # SANS dimension territoriale explicite.
        if obj_entreprise and not ("territoire" in t or "ville" in t):
            continue
        stricte.append((rid, hits))

    for label, lst in (("LARGE (lexicale, = grille auditeur)", large),
                       ("STRICTE (attractivité territoriale/métiers)", stricte)):
        k = len(lst)
        print(f"\nGrille {label} : {k}/{n} = {pct(k, n)}%")
        for rid, hits in lst:
            print(f"  {rid} <- mots-clés : {', '.join(hits)}")

    print("\nRappel dashboard : 38% (soit 8/21) — auditeur : 9/21 (43%).")
    print(f"round_half_up(8/21)  = {pct(8, n)}%")
    print(f"round_half_up(9/21)  = {pct(9, n)}%")


if __name__ == "__main__":
    main()
