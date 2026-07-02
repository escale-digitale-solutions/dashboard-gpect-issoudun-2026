#!/usr/bin/env python3
"""Contre-expertise ENT Q3.3 — moyenne « Déficit d'image du métier ou du secteur ».

Recalcul indépendant depuis data/01_entreprises.xlsx (export 30/06/2026).
La colonne est identifiée par son intitulé (pas par index en dur), et la
moyenne est arrondie selon la convention dashboard : 1 décimale, round half up.
Sort aussi toutes les autres sous-échelles de Q3.3 pour contrôle de cohérence.
Aucune donnée individuelle n'est affichée (agrégats seulement).
"""
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data" / "01_entreprises.xlsx"

def round_half_up(x: float, decimals: int = 1) -> Decimal:
    q = Decimal(1).scaleb(-decimals)
    return Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP)

def main() -> None:
    df = pd.read_excel(DATA, engine="openpyxl")
    print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

    # Toutes les sous-colonnes de la batterie Q3.3
    q33_cols = [c for c in df.columns if str(c).startswith("Q3.3")]
    print(f"\nSous-échelles Q3.3 trouvées : {len(q33_cols)}")

    target = None
    for c in q33_cols:
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        n = int(s.notna().sum())
        # Contrôle : valeurs bien dans l'échelle 1-5
        assert s.between(1, 5).all(), f"Valeur hors échelle 1-5 dans {c!r}"
        mean_raw = float(s.mean())
        label = str(c).split("[")[-1].rstrip("]")
        print(f"  - {label:<55} n={n:<3} moyenne brute={mean_raw:.6f} "
              f"-> arrondi half-up 1 déc. = {round_half_up(mean_raw)}")
        if "image" in str(c).lower():
            target = (label, n, mean_raw)

    if target is None:
        raise SystemExit("Colonne « Déficit d'image » introuvable dans Q3.3")

    label, n, mean_raw = target
    print("\n=== CIBLE : Déficit d'image du métier ou du secteur (Q3.3) ===")
    print(f"n (réponses non vides) = {n}")
    print(f"Moyenne brute           = {mean_raw!r}")
    print(f"Arrondi half-up 2 déc.  = {round_half_up(mean_raw, 2)}")
    print(f"Arrondi half-up 1 déc.  = {round_half_up(mean_raw, 1)}")
    print(f"Valeur dashboard        = 3.1")

if __name__ == "__main__":
    main()
