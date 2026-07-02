#!/usr/bin/env python3
"""
Contre-expertise ENT Q3.3 — "Causes des tensions de recrutement" (échelle 1-5).

Écart signalé par le premier auditeur :
  - dashboard : n=20 unique pour le bloc (10 items)
  - auditeur  : n=20 pour 8 items, mais n=19 pour "Logement" et "Garde d'enfant"
    (moyennes affichées 1,7 et 1,5 jugées exactes sur n=19)

Objectif : tenter de RÉFUTER cet écart.
  H1 : mauvaise colonne prise par l'auditeur -> on liste TOUTES les colonnes Q3.3
       avec leur n et leur moyenne, et on les rapproche des libellés du dashboard.
  H2 : mauvaise base (n collège=21 vs n question) -> on affiche les deux.
  H3 : convention d'arrondi -> moyennes recalculées avec round half up à 1 décimale,
       comparées aux valeurs du dashboard, sur n_item ET sur d'autres bases.
  H4 : valeurs non numériques / 0 / chaînes vides déguisées -> inventaire des
       valeurs distinctes (uniquement des notes 1-5, jamais de verbatim).

Aucune donnée nominative n'est lue ni écrite. Sortie : agrégats seulement.
"""
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
XLSX = REPO / "data" / "01_entreprises.xlsx"
OUT = REPO / "resultats" / "verif_ENT-Q3.3-2_refutation.txt"

# Valeurs affichées par le dashboard (bloc scale Q3.3, n=20) — libellé court -> moyenne
DASHBOARD = {
    "Pénurie de candidats sur le marché local": 4.5,
    "Concurrence salariale autres entreprises/secteurs": 3.7,
    "Inadéquation des compétences / diplômes": 3.1,
    "Déficit d'image du métier / secteur": 3.1,
    "Localisation de l'entreprise": 2.8,
    "Transport": 2.5,
    "Délais de formation initiale trop longs": 2.4,
    "Logement": 1.7,
    "Emploi du conjoint": 1.6,
    "Garde d'enfant": 1.5,
}

# Rapprochement libellé dashboard -> fragment discriminant de l'intitulé xlsx
MATCH = {
    "Pénurie de candidats sur le marché local": "Pénurie de candidats",
    "Concurrence salariale autres entreprises/secteurs": "Concurrence salariale",
    "Inadéquation des compétences / diplômes": "Inadéquation des compétences",
    "Déficit d'image du métier / secteur": "Déficit d'image",
    "Localisation de l'entreprise": "Localisation de l'entreprise",
    "Transport": "liées au Transport",
    "Délais de formation initiale trop longs": "Délais de formation",
    "Logement": "liées au Logement",
    "Emploi du conjoint": "Emploi du conjoint",
    "Garde d'enfant": "Garde d'enfant",
}


def half_up(x: float, nd: int) -> float:
    q = Decimal(1).scaleb(-nd)
    return float(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP))


def main() -> None:
    df = pd.read_excel(XLSX, engine="openpyxl")
    lines = []
    lines.append(f"Fichier : {XLSX.name} — {df.shape[0]} lignes x {df.shape[1]} colonnes")
    n_college = df.shape[0]
    lines.append(f"n collège (H2) = {n_college}")

    q33_cols = [c for c in df.columns if str(c).startswith("Q3.3")]
    lines.append(f"Colonnes Q3.3 détectées : {len(q33_cols)}")
    lines.append("")

    # Inventaire item par item
    header = (
        f"{'Item (dashboard)':52s} {'n_item':>6s} {'moy(n_item)':>11s} "
        f"{'dash':>5s} {'égal?':>6s} {'moy(n=20)':>9s} {'moy(n=21)':>9s} {'valeurs':>18s}"
    )
    lines.append(header)
    lines.append("-" * len(header))

    ns = {}
    for label, dash_mean in DASHBOARD.items():
        frag = MATCH[label]
        cols = [c for c in q33_cols if frag in str(c)]
        assert len(cols) == 1, f"Ambiguïté colonne pour '{label}' : {cols}"
        s = pd.to_numeric(df[cols[0]], errors="coerce")
        n_raw_nonempty = df[cols[0]].notna().sum()  # non vide brut
        n_item = int(s.notna().count() - s.isna().sum())  # numériques valides
        ns[label] = n_item
        mean_item = half_up(s.mean(), 1) if n_item else float("nan")
        # H2/H3 : moyennes sur bases alternatives (somme / 20 et somme / 21)
        total = s.sum()
        mean_b20 = half_up(total / 20, 1)
        mean_b21 = half_up(total / n_college, 1)
        vals = sorted(s.dropna().unique().tolist())
        ok = "OUI" if mean_item == dash_mean else "NON"
        lines.append(
            f"{label:52s} {n_item:>6d} {mean_item:>11.1f} {dash_mean:>5.1f} {ok:>6s} "
            f"{mean_b20:>9.1f} {mean_b21:>9.1f} {str(vals):>18s}"
        )
        if n_raw_nonempty != n_item:
            lines.append(
                f"   !! {label} : {n_raw_nonempty} cellules non vides mais "
                f"{n_item} valeurs numériques (H4 : contenu non numérique)"
            )

    lines.append("")
    distinct_ns = sorted(set(ns.values()))
    lines.append(f"n par item : {ns}")
    lines.append(f"Valeurs distinctes de n sur les 10 items : {distinct_ns}")
    n20 = [l for l, v in ns.items() if v == 20]
    n_autres = {l: v for l, v in ns.items() if v != 20}
    lines.append(f"Items à n=20 : {len(n20)}")
    lines.append(f"Items à n != 20 : {n_autres if n_autres else 'aucun'}")

    # Ligne(s) incomplète(s) : combien de répondants ont < 10 items notés
    # (comptage agrégé, aucun identifiant individuel écrit)
    per_row = df[q33_cols].notna().sum(axis=1)
    completude = per_row.value_counts().sort_index()
    lines.append("")
    lines.append("Complétude par répondant (nb d'items Q3.3 notés -> nb de répondants) :")
    for k, v in completude.items():
        lines.append(f"  {int(k)} items notés : {int(v)} répondant(s)")

    OUT.parent.mkdir(exist_ok=True)
    text = "\n".join(lines) + "\n"
    OUT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
