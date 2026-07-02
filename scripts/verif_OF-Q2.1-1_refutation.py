#!/usr/bin/env python3
"""Contre-expertise OF Q2.1 — Niveau de l'offre par domaine.

Vérifie :
1. Le nombre de sous-items (domaines) de la matrice Q2.1 dans l'export OF.
2. La moyenne (1 décimale, round half up) et le n= de chaque domaine.
3. La comparaison avec les 10 items affichés par le dashboard.
Aucune donnée brute individuelle n'est imprimée : uniquement moyennes, n, min/max.
"""
import re
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

SRC = "/home/user/dashboard-gpect-issoudun-2026/data/02_organismes_formation.xlsx"

# Items affichés par le dashboard (label -> valeur affichée)
DASHBOARD = [
    ("Maintenance industrielle", 3.9),
    ("Management et gestion d'équipe", 3.9),
    ("Usinage, mécanique", 3.7),
    ("Logistique, supply chain", 3.7),
    ("Programmation de machines", 3.4),
    ("CAO / DAO", 3.3),
    ("Compétences commerciales", 3.3),
    ("Sécurité et prévention", 3.1),
    ("Qualité, contrôle et métrologie", 2.7),
    ("Numérique industriel", 2.7),
]


def mean_1dec(series):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) == 0:
        return None, 0
    m = Decimal(str(s.sum() / len(s))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return float(m), len(s)


def main():
    df = pd.read_excel(SRC, engine="openpyxl")
    print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

    q21_cols = [c for c in df.columns if "évaluez le niveau de votre offre" in str(c)]
    print(f"\nNombre de sous-items Q2.1 dans le questionnaire : {len(q21_cols)}")

    results = []
    for c in q21_cols:
        label = re.search(r"\[(.+)\]\s*$", str(c))
        label = label.group(1) if label else str(c)
        m, n = mean_1dec(df[c])
        vals = pd.to_numeric(df[c], errors="coerce").dropna()
        results.append((label, m, n, vals.min() if n else None, vals.max() if n else None))

    results.sort(key=lambda r: (-(r[1] if r[1] is not None else -99), r[0]))
    print("\nClassement complet des 12 domaines (moyenne, n, min, max) :")
    for label, m, n, lo, hi in results:
        print(f"  {m:>4} (n={n}, min={lo:.0f}, max={hi:.0f})  {label}")

    print("\nComparaison avec les 10 items du dashboard :")
    matched = set()
    for dlabel, dval in DASHBOARD:
        key = dlabel.split()[0].lower()
        hit = next((r for r in results if key in r[0].lower()), None)
        if hit is None:
            print(f"  DASHBOARD '{dlabel}' = {dval} : AUCUNE colonne correspondante")
            continue
        matched.add(hit[0])
        ok = "OK" if hit[1] == dval else f"ECART (calc {hit[1]})"
        print(f"  {ok:>18}  dashboard {dval} | {dlabel} -> [{hit[0]}]")

    print("\nDomaines du questionnaire ABSENTS du dashboard :")
    for label, m, n, lo, hi in results:
        if label not in matched:
            print(f"  {m} (n={n})  {label}")

    print("\nRang qu'occuperaient les absents dans le classement complet :")
    for i, (label, m, n, *_ ) in enumerate(results, 1):
        marker = "  <-- OMIS" if label not in matched else ""
        print(f"  {i:>2}. {m} {label}{marker}")


if __name__ == "__main__":
    main()
