#!/usr/bin/env python3
"""
Contre-expertise ENT Q3.3 — Causes des tensions de recrutement (grille 1-5).
Recalcule de zéro, pour chacun des 10 items de la grille Q3.3 :
  - n = nombre de réponses non vides
  - moyenne (arrondi half-up, 1 décimale)
et les compare aux valeurs affichées par le dashboard (bloc scale Q3.3, n=20).

Source : data/01_entreprises.xlsx (export 30/06/2026, 21 répondants).
Aucune donnée individuelle n'est affichée : uniquement des agrégats (n, moyennes).
"""
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
XLSX = REPO / "data" / "01_entreprises.xlsx"

# Index (0-based) des 10 colonnes de la grille Q3.3 dans l'export entreprises,
# et libellés courts tels qu'affichés sur le dashboard.
Q33_COLS = {
    26: "Pénurie de candidats sur le marché local",
    27: "Inadéquation des compétences / diplômes",
    28: "Déficit d'image du métier / secteur",
    29: "Concurrence salariale autres entreprises/secteurs",
    30: "Logement",
    31: "Transport",
    32: "Emploi du conjoint",
    33: "Garde d'enfant",
    34: "Localisation de l'entreprise",
    35: "Délais de formation initiale trop longs",
}

# Valeurs affichées par le dashboard (bloc scale Q3.3, n global affiché = 20).
DASHBOARD_N_BLOC = 20
DASHBOARD_MEANS = {
    "Pénurie de candidats sur le marché local": Decimal("4.5"),
    "Concurrence salariale autres entreprises/secteurs": Decimal("3.7"),
    "Inadéquation des compétences / diplômes": Decimal("3.1"),
    "Déficit d'image du métier / secteur": Decimal("3.1"),
    "Localisation de l'entreprise": Decimal("2.8"),
    "Transport": Decimal("2.5"),
    "Délais de formation initiale trop longs": Decimal("2.4"),
    "Logement": Decimal("1.7"),
    "Emploi du conjoint": Decimal("1.6"),
    "Garde d'enfant": Decimal("1.5"),
}


def mean_1dec_half_up(series: pd.Series) -> Decimal | None:
    """Moyenne des valeurs non vides, arrondie half-up à 1 décimale."""
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if len(vals) == 0:
        return None
    m = Decimal(str(vals.sum())) / Decimal(len(vals))
    return m.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def main() -> None:
    df = pd.read_excel(XLSX, engine="openpyxl")
    print(f"Fichier : {XLSX.name} — {df.shape[0]} lignes x {df.shape[1]} colonnes")
    print()

    # Contrôle : les intitulés des colonnes ciblées appartiennent bien à Q3.3
    for idx in Q33_COLS:
        header = str(df.columns[idx])
        assert header.startswith("Q3.3"), f"Colonne {idx} inattendue : {header!r}"

    print(f"{'Item':<52} {'n':>3} {'moyenne':>8} {'dash.':>6} {'écart n vs 20':>14}")
    ns = {}
    for idx, label in Q33_COLS.items():
        col = df.iloc[:, idx]
        # Vide = NaN ou chaîne blanche ; toute valeur numérique 1-5 compte
        non_empty = col.dropna()
        non_empty = non_empty[non_empty.astype(str).str.strip() != ""]
        n = len(non_empty)
        ns[label] = n
        mean = mean_1dec_half_up(col)
        dash = DASHBOARD_MEANS[label]
        flag_mean = "OK" if mean == dash else f"ECART (dash {dash})"
        flag_n = "" if n == DASHBOARD_N_BLOC else f"n={n} != {DASHBOARD_N_BLOC}"
        print(f"{label:<52} {n:>3} {str(mean):>8} {str(dash):>6} {flag_n:>14}  {flag_mean}")

    print()
    # Contrôle de cohérence des moyennes sur les items où n diffère de 20 :
    # moyenne recalculée sur les seules réponses présentes (déjà le cas ci-dessus).
    n_distincts = sorted(set(ns.values()))
    print(f"n par item : {ns}")
    print(f"Valeurs de n observées sur le bloc : {n_distincts}")
    print(f"n global affiché par le dashboard : {DASHBOARD_N_BLOC}")

    # Nombre de répondants ayant répondu à au moins un item de la grille
    sub = df.iloc[:, list(Q33_COLS)]
    au_moins_un = int(sub.notna().any(axis=1).sum())
    tous = int(sub.notna().all(axis=1).sum())
    print(f"Répondants avec >=1 item renseigné : {au_moins_un}")
    print(f"Répondants avec les 10 items renseignés : {tous}")


if __name__ == "__main__":
    main()
