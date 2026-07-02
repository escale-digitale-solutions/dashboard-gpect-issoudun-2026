# -*- coding: utf-8 -*-
"""
Contre-expertise ENT Q4.1 — pyramide des âges + KPI seniors 47%.

Objectif : vérifier si les chiffres du dashboard
  Avec plus gros employeur : 3 031 têtes | <30 18,0% | 31-44 35,0% | 45-59 41,7%
                             | 60+ 5,3% | seniors 47,0% | femmes 36,5%
  Sans plus gros employeur : 1 506 têtes | <30 20,9% | 31-44 33,5% | 45-59 39,5%
                             | 60+ 6,1% | seniors 45,6% | femmes 46,5%
se calculent sur la base brute des 21 répondants, ou seulement sur une base
nettoyée (exclusion de réponses incohérentes pyramide vs effectif Q1.4),
comme l'affirme le premier auditeur.

Aucune donnée nominative n'est lue ni affichée : identifiants E01..E21
(ordre des lignes du fichier), valeurs numériques agrégées uniquement.

Usage : python3 scripts/verif_ENT-Q4.1-1_refutation.py
(depuis la racine du repo ; données dans data/01_entreprises.xlsx)
"""
from decimal import Decimal, ROUND_HALF_UP
from itertools import combinations

import pandas as pd

XLSX = "data/01_entreprises.xlsx"

# Valeurs affichées par le dashboard (index.html v12, tableau Q4.1 + KPI)
DASH = {
    "avec": {"tetes": 3031, "m30": "18.0", "a3144": "35.0", "a4559": "41.7",
             "a60": "5.3", "seniors": "47.0", "femmes": "36.5"},
    "sans": {"tetes": 1506, "m30": "20.9", "a3144": "33.5", "a4559": "39.5",
             "a60": "6.1", "seniors": "45.6", "femmes": "46.5"},
}
DASH_KPI_SENIORS = "47"  # KPI arrondi à l'entier

# Valeurs annoncées par le premier auditeur sur la base brute (21 lignes)
AUDIT_BRUT = {"tetes": 3155, "seniors": "46.3"}

PYR_IDX = list(range(42, 50))      # Q4.1.1 .. Q4.1.8
FEM_IDX = [43, 45, 47, 49]         # colonnes Femmes
EFF_Q14_IDX = 14                   # Q1.4 effectif inscrit


def r1(x):
    """Arrondi half-up à 1 décimale, rendu str (convention dashboard)."""
    return str(Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def r0(x):
    """Arrondi half-up à l'entier."""
    return str(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def table_row(sub):
    """Calcule la ligne du tableau (têtes + 6 %) sur un sous-ensemble de lignes."""
    p = sub.iloc[:, PYR_IDX].fillna(0)
    tot = float(p.to_numpy().sum())
    if tot == 0:
        return None
    m30 = float(p.iloc[:, [0, 1]].to_numpy().sum())
    a3144 = float(p.iloc[:, [2, 3]].to_numpy().sum())
    a4559 = float(p.iloc[:, [4, 5]].to_numpy().sum())
    a60 = float(p.iloc[:, [6, 7]].to_numpy().sum())
    fem = float(sub.iloc[:, FEM_IDX].fillna(0).to_numpy().sum())
    return {
        "tetes": tot,
        "m30": r1(100 * m30 / tot), "a3144": r1(100 * a3144 / tot),
        "a4559": r1(100 * a4559 / tot), "a60": r1(100 * a60 / tot),
        "seniors": r1(100 * (a4559 + a60) / tot),
        "seniors_kpi": r0(100 * (a4559 + a60) / tot),
        "femmes": r1(100 * fem / tot),
    }


def match(row, dash):
    """Compare une ligne calculée aux 7 cellules du dashboard."""
    if row is None:
        return False, ["(base vide)"]
    diffs = []
    if int(round(row["tetes"])) != dash["tetes"]:
        diffs.append(f"tetes {row['tetes']:.2f} vs {dash['tetes']}")
    for k in ("m30", "a3144", "a4559", "a60", "seniors", "femmes"):
        if row[k] != dash[k]:
            diffs.append(f"{k} {row[k]} vs {dash[k]}")
    return len(diffs) == 0, diffs


def show(label, row):
    if row is None:
        print(f"  {label}: base vide")
        return
    print(f"  {label}: têtes={row['tetes']:.2f}  <30={row['m30']}%  "
          f"31-44={row['a3144']}%  45-59={row['a4559']}%  60+={row['a60']}%  "
          f"seniors={row['seniors']}% (KPI {row['seniors_kpi']}%)  "
          f"femmes={row['femmes']}%")


def main():
    df = pd.read_excel(XLSX, engine="openpyxl")
    n, c = df.shape
    print(f"Fichier lu : {XLSX} -> {n} répondants x {c} colonnes")
    assert (n, c) == (21, 124), "Structure inattendue"

    pyr = df.iloc[:, PYR_IDX]
    eff = pd.to_numeric(df.iloc[:, EFF_Q14_IDX], errors="coerce")

    # --- 1. Inspection ligne à ligne (anonyme) : somme pyramide vs Q1.4 ---
    print("\n[1] Contrôle de cohérence par répondant (E01..E21)")
    pyr_sum = pyr.fillna(0).sum(axis=1)
    all_nan = pyr.isna().all(axis=1)
    has_frac = pyr.apply(
        lambda s: s.dropna().apply(lambda v: float(v) != int(float(v))).any(), axis=1)
    n_q41 = int((~all_nan).sum())
    print(f"    n= répondants ayant renseigné au moins une case Q4.1 : {n_q41}")
    suspects = []
    for i in range(n):
        e, s = eff.iloc[i], float(pyr_sum.iloc[i])
        tag = ""
        if all_nan.iloc[i]:
            tag = "PYRAMIDE VIDE (tout NaN)"
        elif has_frac.iloc[i]:
            tag = "VALEURS FRACTIONNAIRES"
        elif s == 0:
            tag = "PYRAMIDE TOUTE A ZERO"
        elif pd.notna(e) and e > 0 and not (0.5 <= s / e <= 2.0):
            tag = "SOMME PYRAMIDE INCOHERENTE vs Q1.4"
        line = f"    E{i+1:02d}: somme pyramide={s:g}  effectif Q1.4={'' if pd.isna(e) else int(e)}"
        if tag:
            suspects.append(i)
            line += f"   << {tag}"
        print(line)
    print(f"    Lignes suspectes : {['E%02d' % (i+1) for i in suspects]}")

    # --- 2. Plus gros employeur (jamais nommé) ---
    big = int(eff.idxmax())
    print(f"\n[2] Plus gros employeur = E{big+1:02d} (Q1.4={int(eff.max())}), traité à part.")

    # --- 3. Hypothèse 'dashboard juste' : base brute 21 répondants ---
    print("\n[3] Base BRUTE (21 répondants, NaN=0)")
    brut_avec = table_row(df)
    brut_sans = table_row(df.drop(index=big))
    show("Avec", brut_avec)
    show("Sans", brut_sans)
    ok_b, diff_b = match(brut_avec, DASH["avec"])
    print(f"    Reproduit la ligne 'Avec' du dashboard ? {ok_b}"
          + ("" if ok_b else f"  écarts: {diff_b}"))
    print(f"    Conforme aux chiffres du 1er auditeur "
          f"(3 155 têtes / seniors 46,3%) ? "
          f"{int(round(brut_avec['tetes'])) == AUDIT_BRUT['tetes'] and brut_avec['seniors'] == AUDIT_BRUT['seniors']}")

    # --- 4. Hypothèse du 1er auditeur : exclusion des lignes incohérentes ---
    print("\n[4] Recherche du sous-ensemble d'exclusions reproduisant EXACTEMENT")
    print("    les 14 cellules du tableau du dashboard (parmi les lignes suspectes)")
    found = []
    cand = suspects
    for k in range(0, len(cand) + 1):
        for combo in combinations(cand, k):
            keep = df.drop(index=list(combo))
            ra = table_row(keep)
            rs = table_row(keep.drop(index=big, errors="ignore"))
            oa, _ = match(ra, DASH["avec"])
            os_, _ = match(rs, DASH["sans"])
            if oa and os_:
                found.append(combo)
    if found:
        for combo in found:
            ex = ["E%02d" % (i + 1) for i in combo]
            keep = df.drop(index=list(combo))
            ra = table_row(keep)
            rs = table_row(keep.drop(index=big, errors="ignore"))
            nb_avec = int((~keep.iloc[:, PYR_IDX].isna().all(axis=1)).sum())
            print(f"    MATCH EXACT 14/14 cellules en excluant {ex} "
                  f"(base restante {len(keep)} lignes, dont {nb_avec} pyramides renseignées)")
            show("      Avec", ra)
            show("      Sans", rs)
    else:
        print("    Aucun sous-ensemble de lignes suspectes ne reproduit le tableau.")

    # --- 5. Contre-hypothèses de réfutation ---
    print("\n[5] Contre-hypothèses (pour tenter de sauver le dashboard)")
    # 5a. NaN non remplacés (identique car somme ignore NaN) — déjà couvert.
    # 5b. Base = lignes pyramide non vide uniquement (exclut tout-NaN)
    sub = df[~all_nan]
    show("5b  pyramides non vides seulement (Avec)", table_row(sub))
    # 5c. Arrondi banker's (round half even) au lieu de half-up
    ra = table_row(df)
    print(f"    5c  brut, seniors round-half-even à 1 déc.: "
          f"{round(100*0.463, 1) if ra else ''} (sans objet si base brute ne matche pas les têtes)")
    # 5d. seniors = 45-59 seulement (sans 60+)
    p = df.iloc[:, PYR_IDX].fillna(0)
    tot = float(p.to_numpy().sum())
    s4559 = float(p.iloc[:, [4, 5]].to_numpy().sum())
    print(f"    5d  brut, seniors=45-59 seulement : {r1(100*s4559/tot)}%")
    # 5e. le total 'Avec' du dashboard peut-il venir d'une autre colonne (Q1.4) ?
    print(f"    5e  somme Q1.4 sur 21 répondants : {int(eff.sum())} "
          f"(vs 3 031 affiché) ; somme Q1.4 sans plus gros employeur : "
          f"{int(eff.drop(index=big).sum())} (vs 1 506)")

    print("\nConclusion : voir sections [3] (base brute) et [4] (base nettoyée).")


if __name__ == "__main__":
    main()
