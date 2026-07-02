#!/usr/bin/env python3
"""Contre-expertise KPI accueil : part de seniors (45 ans et +) — ENT Q4.1.

Dashboard : 47% (table : 3 031 têtes, 47,0% avec plus gros employeur ; 1 506 / 45,6% sans).
Premier auditeur : 46% (1 460,5 / 3 155).

Recalcul de zéro, sans donnée en dur : colonnes Q4.1.1 à Q4.1.8 (indices 42-49)
du fichier data/01_entreprises.xlsx. Sorties strictement agrégées/anonymisées.
"""
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

PATH = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"
df = pd.read_excel(PATH, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

cols = list(df.columns[42:50])
print("\nColonnes Q4.1 retenues (indices 42-49) :")
for i, c in enumerate(cols, 42):
    print(f"  [{i}] {c}")

sub = df[cols].copy()

# Inspection anonymisée : pour chaque ligne, uniquement le total et des drapeaux
print("\nInspection par ligne (anonymisée, E01..E21) :")
print(f"{'id':<4}{'nb rempli':<11}{'total':<10}{'seniors':<10}{'part':<8}{'remarque'}")
for idx in range(len(sub)):
    row = pd.to_numeric(sub.iloc[idx], errors="coerce")
    n_filled = row.notna().sum()
    tot = row.sum()
    sen = row.iloc[4:8].sum()  # Q4.1.5..Q4.1.8 = 45-59 H/F + 60+ H/F
    rem = ""
    if n_filled == 0:
        rem = "aucune donnee"
    elif tot <= 1.5:
        rem = "saisie en proportions (somme ~1)"
    elif tot <= 110 and abs(tot - 100) < 10:
        rem = "possiblement saisie en % (somme ~100)"
    if (row.dropna() % 1 != 0).any():
        rem += " | valeurs non entieres"
    part = f"{sen/tot*100:.1f}%" if tot > 0 else "-"
    print(f"E{idx+1:02d} {n_filled:<11}{tot:<10g}{sen:<10g}{part:<8}{rem}")

num = sub.apply(pd.to_numeric, errors="coerce")
totals_row = num.sum(axis=1)


def pct(sen, tot):
    raw = sen / tot * 100
    return raw, int(Decimal(str(raw)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def bilan(label, mask):
    d = num[mask]
    tot = d.sum().sum()
    sen = d[cols[4:8]].sum().sum()
    raw, arrondi = pct(sen, tot)
    n = int(mask.sum())
    print(f"\n{label}")
    print(f"  n lignes = {n} | tetes = {tot:g} | seniors 45+ = {sen:g}")
    print(f"  part seniors = {raw:.2f}% -> arrondi entier (half up) = {arrondi}%")
    return tot, sen, raw


has_data = num.notna().any(axis=1)

# Variante A : toutes les lignes renseignées, somme brute
bilan("A. Somme brute, toutes lignes renseignees", has_data)

# Variante B : exclusion des lignes saisies en proportions/pourcentages (somme <= 1.5)
prop_mask = (totals_row > 0) & (totals_row <= 1.5)
print(f"\nLignes detectees comme saisies en proportions (somme <=1,5) : {int(prop_mask.sum())}")
bilan("B. Somme brute SANS la/les lignes en proportions", has_data & ~prop_mask)

# Variante C : sans le plus gros employeur (ligne au plus grand total)
big_idx = totals_row.idxmax()
print(f"\nPlus gros employeur = ligne au total max ({totals_row.max():g} tetes)")
bilan("C. Sans le plus gros employeur", has_data & (num.index != big_idx))

# Variante D : sans plus gros employeur NI ligne(s) en proportions
bilan("D. Sans plus gros employeur ni lignes en proportions",
      has_data & (num.index != big_idx) & ~prop_mask)

# Variante E : moyenne non ponderee des parts par entreprise (lignes total>1.5 + lignes proportions)
parts = []
for idx in range(len(num)):
    row = num.iloc[idx]
    t = row.sum()
    if t and t > 0:
        parts.append(row.iloc[4:8].sum() / t * 100)
m = sum(parts) / len(parts)
print(f"\nE. Moyenne non ponderee des parts par entreprise : n={len(parts)}, {m:.2f}%")

# Verification des repartitions par tranche affichees dans la table du dashboard
def tranches(label, mask):
    d = num[mask]
    tot = d.sum().sum()
    t30 = d[cols[0:2]].sum().sum()
    t3144 = d[cols[2:4]].sum().sum()
    t4559 = d[cols[4:6]].sum().sum()
    t60 = d[cols[6:8]].sum().sum()
    fem = d[[cols[1], cols[3], cols[5], cols[7]]].sum().sum()
    print(f"\n{label} : tetes={tot:g} | <30 {t30/tot*100:.1f}% | 31-44 {t3144/tot*100:.1f}% | "
          f"45-59 {t4559/tot*100:.1f}% | 60+ {t60/tot*100:.1f}% | femmes {fem/tot*100:.1f}%")


tranches("Tranches (toutes lignes)", has_data)
tranches("Tranches (sans lignes proportions)", has_data & ~prop_mask)
tranches("Tranches (sans plus gros employeur, avec proportions)", has_data & (num.index != big_idx))
tranches("Tranches (sans plus gros employeur ni proportions)",
         has_data & (num.index != big_idx) & ~prop_mask)

# --- Perimetre du dashboard : lignes "exploitables" uniquement.
# Regle de nettoyage reconstituee (aucune ligne codee en dur) :
#   (a) exclusion des lignes saisies en unites non-effectifs
#       (valeurs fractionnaires : proportions), et
#   (b) exclusion des lignes dont le total pyramide est incoherent
#       avec la tranche d'effectif declaree en Q1.3.
print("\n" + "=" * 60)
RANGES = {
    "Moins de 10 salariés": (1, 9),
    "10 à 49 salariés": (10, 49),
    "50 à 249 salariés": (50, 249),
    "250 salariés et plus": (250, float("inf")),
}
q13 = df.iloc[:, 13].astype(str)  # Q1.3 tranche d'effectif
print("\nRegle de nettoyage — lignes ecartees :")
keep = []
for idx in range(len(num)):
    t = totals_row.iloc[idx]
    lo, hi = RANGES[q13.iloc[idx]]
    frac = (num.iloc[idx].dropna() % 1 != 0).any()
    incoh = not (lo <= t <= hi)
    if frac or incoh:
        why = []
        if frac:
            why.append("valeurs fractionnaires (saisie en proportions)")
        if incoh:
            why.append(f"total {t:g} hors tranche Q1.3 [{lo};{hi}]")
        print(f"  E{idx+1:02d} : " + " ; ".join(why))
    else:
        keep.append(idx)

mask_dash = num.index.isin(keep)
bilan(f"F. Perimetre nettoye ({len(keep)} lignes exploitables)", mask_dash)
tranches("Tranches (perimetre nettoye, avec plus gros employeur)", mask_dash)
mask_dash_sans = mask_dash & (num.index != big_idx)
bilan("G. Perimetre nettoye SANS plus gros employeur", mask_dash_sans)
tranches("Tranches (perimetre nettoye, sans plus gros employeur)", mask_dash_sans)

print("""
Rappel table dashboard (Q4.1) a reproduire :
  Avec plus gros employeur : 3 031 tetes | <30 18,0% | 31-44 35,0% | 45-59 41,7% | 60+ 5,3% | seniors 47,0% | femmes 36,5%
  Sans plus gros employeur : 1 506 tetes | <30 20,9% | 31-44 33,5% | 45-59 39,5% | 60+ 6,1% | seniors 45,6% | femmes 46,5%""")
