# -*- coding: utf-8 -*-
"""
Contre-expertise CROISE Écart 4 + Risque 1 — « 47% de seniors (45 ans et +) »
Vérifie le % de seniors dans la pyramide des âges (Q4.1, colonnes 42-49 du
fichier entreprises) selon plusieurs bases de calcul :
  A. base brute : toutes les lignes avec au moins une valeur pyramide
  B. base « nettoyée » : exclusion des lignes à valeurs fractionnaires ou
     dont la somme pyramide s'écarte fortement de l'effectif Q1.4
  C. bases A et B sans le plus gros employeur
Aucune donnée nominative n'est affichée (identifiants E01..E21).
Arrondi : round half up.
"""
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

def rhu(x, nd=0):
    q = Decimal(1).scaleb(-nd)
    return float(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP))

F = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"
df = pd.read_excel(F, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

pyr_cols = df.columns[42:50]   # Q4.1.1 .. Q4.1.8
senior_cols = df.columns[46:50]  # 45-59 H/F + 60+ H/F
eff_col = df.columns[14]       # Q1.4 effectif inscrit
print("Colonnes pyramide :", [c[:22] for c in pyr_cols])
print("Colonne effectif  :", eff_col[:40])

pyr = df[pyr_cols].apply(pd.to_numeric, errors="coerce")
eff = pd.to_numeric(df[eff_col], errors="coerce")

# --- inspection ligne à ligne (anonyme) ---
print("\n--- Détail par répondant (anonyme) ---")
print(f"{'id':<4}{'somme pyr':>10}{'seniors':>9}{'eff Q1.4':>10}{'fraction?':>10}{'ecart%':>8}")
flags = []
for i in range(len(df)):
    row = pyr.iloc[i]
    if row.notna().sum() == 0:
        print(f"E{i+1:02d}  (pyramide vide)")
        flags.append(None)
        continue
    s = row.sum()
    sen = row[senior_cols].sum()
    frac = bool(((row.dropna() % 1) != 0).any())
    e = eff.iloc[i]
    ecart = abs(s - e) / e * 100 if pd.notna(e) and e > 0 else float("nan")
    print(f"E{i+1:02d} {s:>10.2f}{sen:>9.2f}{e:>10.1f}{str(frac):>10}{ecart:>8.1f}")
    flags.append({"sum": s, "sen": sen, "frac": frac, "ecart": ecart})

def stats(mask, label):
    sub = pyr[mask]
    tot = sub.sum().sum()
    sen = sub[senior_cols].sum().sum()
    m30 = sub[pyr_cols[0:2]].sum().sum()
    m3144 = sub[pyr_cols[2:4]].sum().sum()
    m4559 = sub[pyr_cols[4:6]].sum().sum()
    m60 = sub[pyr_cols[6:8]].sum().sum()
    fem = sub[[pyr_cols[1], pyr_cols[3], pyr_cols[5], pyr_cols[7]]].sum().sum()
    print(f"\n{label}")
    print(f"  n lignes = {mask.sum()} · têtes = {tot:.0f}"
          f" · seniors 45+ = {sen:.0f}")
    print(f"  % seniors brut = {sen/tot*100:.2f}%  -> arrondi entier = {rhu(sen/tot*100):.0f}%  -> 1 déc. = {rhu(sen/tot*100,1)}")
    print(f"  <30 {m30/tot*100:.1f}% · 31-44 {m3144/tot*100:.1f}% · 45-59 {m4559/tot*100:.1f}% · 60+ {m60/tot*100:.1f}% · femmes {fem/tot*100:.1f}%")
    return tot, sen

has_pyr = pyr.notna().any(axis=1)

# A. base brute
stats(has_pyr, "A. BASE BRUTE (toutes lignes avec pyramide renseignée)")

# B. base nettoyée : exclut fractionnaires OU écart somme/effectif > 20 %
bad = pd.Series(False, index=df.index)
for i, f in enumerate(flags):
    if f is None:
        continue
    if f["frac"] or (pd.notna(f["ecart"]) and f["ecart"] > 20):
        bad.iloc[i] = True
print(f"\nLignes signalées incohérentes (fraction ou écart>20% vs Q1.4) : {int(bad.sum())}")
clean = has_pyr & ~bad
stats(clean, "B. BASE NETTOYÉE (exclusion lignes incohérentes)")

# C. sans le plus gros employeur (ligne à somme pyramide maximale)
sums = pyr.sum(axis=1)
big = sums.idxmax()
print(f"\nPlus gros employeur = E{big+1:02d} (somme pyramide = {sums[big]:.0f} têtes) — non nommé")
stats(has_pyr & (df.index != big), "A'. BASE BRUTE sans plus gros employeur")
stats(clean & (df.index != big), "B'. BASE NETTOYÉE sans plus gros employeur")

print("\nRappel dashboard : avec = 3 031 têtes / 47,0% seniors ; sans = 1 506 têtes / 45,6% ; KPI '47% de seniors'.")
