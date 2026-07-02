#!/usr/bin/env python3
"""Contre-expertise CROISE Écart 4 / Risque 1 — « 47% de seniors (45 ans et +) ».

Recalcul indépendant à partir de data/01_entreprises.xlsx, colonnes Q4.1.1 à
Q4.1.8 (pyramide des âges en têtes, 8 cases sexe x tranche).

Trois bases calculées :
  A. Base brute : toutes les lignes avec au moins une case Q4.1 renseignée.
  B. Base « nettoyée » : exclusion des lignes de pyramide incohérentes
     (valeurs fractionnaires, ou somme des 8 cases s'écartant fortement de
     l'effectif inscrit Q1.4).
  C. Base nettoyée sans le plus gros employeur.

Aucune donnée en dur ; sorties agrégées et anonymisées (E01, E02, ...).
"""
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

F = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"
df = pd.read_excel(F, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

cols = list(df.columns)
# Colonnes pyramide Q4.1.1..Q4.1.8 (indices 42..49) et effectif inscrit Q1.4 (14)
pyr_cols = [c for c in cols if c.strip().startswith("Q4.1.")]
assert len(pyr_cols) == 8, pyr_cols
eff_col = [c for c in cols if c.strip().startswith("Q1.4")][0]
print("Colonnes pyramide :", [c.split("—")[0].strip() for c in pyr_cols])
print("Colonne effectif  :", eff_col.split("—")[0].strip())

pyr = df[pyr_cols].apply(pd.to_numeric, errors="coerce")
eff = pd.to_numeric(df[eff_col], errors="coerce")

# Tranches : <30 = Q4.1.1/2 ; 31-44 = Q4.1.3/4 ; 45-59 = Q4.1.5/6 ; 60+ = Q4.1.7/8
c_lt30 = pyr_cols[0:2]
c_3144 = pyr_cols[2:4]
c_4559 = pyr_cols[4:6]
c_60p = pyr_cols[6:8]

row_tot = pyr.sum(axis=1, skipna=True)
row_sen = pyr[c_4559 + c_60p].sum(axis=1, skipna=True)
answered = pyr.notna().any(axis=1)

def pct(num, den):
    if den == 0:
        return None
    return Decimal(str(100 * num / den)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

def pct_int(num, den):
    return Decimal(str(100 * num / den)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

print("\n--- Diagnostic ligne par ligne (anonymisé) ---")
frac_rows, incoh_rows = [], []
for i in df.index:
    if not answered[i]:
        print(f"E{i+1:02d} : aucune case Q4.1 renseignee")
        continue
    vals = pyr.loc[i]
    has_frac = any(pd.notna(v) and float(v) != int(v) for v in vals)
    tot = row_tot[i]
    e = eff[i]
    ratio = (tot / e) if pd.notna(e) and e > 0 else None
    incoh = ratio is not None and (ratio < 0.5 or ratio > 1.5)
    flags = []
    if has_frac:
        flags.append("valeurs fractionnaires")
        frac_rows.append(i)
    if incoh:
        flags.append(f"somme pyramide = {tot:.1f} vs effectif Q1.4 = {e:.0f} (ratio {ratio:.2f})")
        incoh_rows.append(i)
    print(f"E{i+1:02d} : somme={tot:.1f}  seniors={row_sen[i]:.1f}  "
          f"{'ANOMALIE: ' + ' ; '.join(flags) if flags else 'ok'}")

excl = sorted(set(frac_rows) | set(incoh_rows))
print(f"\nLignes avec pyramide renseignee : {int(answered.sum())} / {len(df)}")
print(f"Lignes anormales (fractionnaires ou ratio hors [0.5;1.5]) : {len(excl)}")

def bilan(label, mask):
    tot = row_tot[mask].sum()
    sen = row_sen[mask].sum()
    lt30 = pyr.loc[mask, c_lt30].sum().sum()
    a3144 = pyr.loc[mask, c_3144].sum().sum()
    a4559 = pyr.loc[mask, c_4559].sum().sum()
    a60 = pyr.loc[mask, c_60p].sum().sum()
    print(f"\n{label}")
    print(f"  n lignes = {int(mask.sum())} ; tetes = {tot:.1f}")
    print(f"  <30 : {pct(lt30, tot)}%  |  31-44 : {pct(a3144, tot)}%  |  "
          f"45-59 : {pct(a4559, tot)}%  |  60+ : {pct(a60, tot)}%")
    print(f"  Seniors 45+ = {sen:.1f} tetes  ->  {pct(sen, tot)}%  "
          f"(arrondi entier : {pct_int(sen, tot)}%)")
    return tot, sen

mask_brut = answered
mask_clean = answered & ~df.index.isin(excl)

bilan("A. BASE BRUTE (toutes lignes renseignees)", mask_brut)
tot_c, sen_c = bilan("B. BASE NETTOYEE (lignes anormales exclues)", mask_clean)

# C. Sans le plus gros employeur (identifie par l'effectif max, ~1550)
big = eff.idxmax()
mask_nobig = mask_clean & (df.index != big)
bilan("C. BASE NETTOYEE SANS LE PLUS GROS EMPLOYEUR", mask_nobig)

print("\nRappel dashboard : 47% seniors ; table ENT : 3 031 tetes avec, 1 506 sans.")
