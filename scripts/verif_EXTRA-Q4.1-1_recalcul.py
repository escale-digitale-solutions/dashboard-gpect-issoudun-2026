# Contre-expertise : part des seniors (45 ans et +) dans la pyramide des ages (ENT Q4.1)
# Dashboard : 47% (table interne : 3 031 tetes, 47,0% avec plus gros employeur ; 45,6% sans)
# Premier auditeur : 46% (1 460 / 3 155)
# Ce script recalcule tout depuis l'export du 30/06, sans rien supposer.

import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

PATH = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"
df = pd.read_excel(PATH, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

# Colonnes Q4.1.1 a Q4.1.8 (indices 42..49 d'apres colonnes_ENT.txt)
cols = list(df.columns[42:50])
print("\nColonnes pyramide des ages :")
for i, c in enumerate(cols):
    print(f"  [{42+i}] {c}")

sub = df[cols].copy()

# Inspection des valeurs brutes (types, non-numeriques, NaN) — sans rien d'identifiant
print("\nValeurs brutes par colonne (dtype, nb NaN, min, max) :")
for c in cols:
    s = pd.to_numeric(sub[c], errors="coerce")
    raw_nonnum = sub[c].notna() & s.isna()
    print(f"  {c[:40]:42s} dtype={sub[c].dtype} NaN={int(sub[c].isna().sum())} "
          f"non-num={int(raw_nonnum.sum())} min={s.min()} max={s.max()}")

num = sub.apply(pd.to_numeric, errors="coerce")

# Repondants ayant renseigne au moins une case de la pyramide
answered = num.notna().any(axis=1)
print(f"\nRepondants avec au moins une case Q4.1 renseignee : n={int(answered.sum())} / {len(df)}")
print(f"Repondants avec les 8 cases renseignees : n={int(num.notna().all(axis=1).sum())}")

filled = num.fillna(0)

# Seniors = 45-59 (H+F) + 60+ (H+F) = colonnes indices 4,5,6,7 dans cols
senior_cols = cols[4:8]
junior_cols = cols[0:4]

tot_par_rep = filled.sum(axis=1)
sen_par_rep = filled[senior_cols].sum(axis=1)

def pct(a, b):
    return Decimal(str(100 * a / b)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

def pct_int(a, b):
    return Decimal(str(100 * a / b)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

total = tot_par_rep.sum()
seniors = sen_par_rep.sum()
print("\n=== PONDERE (somme des effectifs declares dans la pyramide) ===")
print(f"Total tetes pyramide  : {int(total)}")
print(f"Seniors 45 ans et +   : {int(seniors)}")
print(f"Part seniors          : {pct(seniors, total)}% -> arrondi entier : {pct_int(seniors, total)}%")

# Detail par tranche pour comparer a la table du dashboard
m30 = filled[junior_cols[0:2]].sum().sum()
a3144 = filled[junior_cols[2:4]].sum().sum()
a4559 = filled[senior_cols[0:2]].sum().sum()
a60 = filled[senior_cols[2:4]].sum().sum()
femmes = filled[[cols[1], cols[3], cols[5], cols[7]]].sum().sum()
print(f"\nDetail : <30={int(m30)} ({pct(m30,total)}%) | 31-44={int(a3144)} ({pct(a3144,total)}%) | "
      f"45-59={int(a4559)} ({pct(a4559,total)}%) | 60+={int(a60)} ({pct(a60,total)}%) | "
      f"%femmes={pct(femmes,total)}%")

# Sans le plus gros employeur = ligne avec le plus grand total pyramide
idx_max = tot_par_rep.idxmax()
print(f"\nPlus gros employeur (pyramide) : total pyramide = {int(tot_par_rep[idx_max])} tetes "
      f"(identifiant ligne masque)")
mask = df.index != idx_max
t2 = tot_par_rep[mask].sum()
s2 = sen_par_rep[mask].sum()
print("=== PONDERE SANS PLUS GROS EMPLOYEUR ===")
print(f"Total={int(t2)} | Seniors={int(s2)} | Part={pct(s2,t2)}% -> {pct_int(s2,t2)}%")

# Variantes de convention
print("\n=== VARIANTES ===")
ratios = (sen_par_rep[answered & (tot_par_rep > 0)] / tot_par_rep[answered & (tot_par_rep > 0)])
moy = Decimal(str(100 * ratios.mean())).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
med = Decimal(str(100 * ratios.median())).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
print(f"Moyenne non ponderee des parts par entreprise : {moy}% (n={len(ratios)})")
print(f"Mediane des parts par entreprise              : {med}%")

# Base 'effectif inscrit' (Q1.3) — colonne possiblement textuelle : nettoyage prudent
eff_col = None
for c in df.columns:
    cl = str(c).lower()
    if "effectif" in cl and ("total" in cl or "inscrit" in cl or "salari" in cl):
        eff_col = c
        break
if eff_col is not None:
    raw = df[eff_col].astype(str).str.replace(r"[^\d]", "", regex=True)
    eff = pd.to_numeric(raw, errors="coerce")
    print(f"\nColonne effectif trouvee : '{str(eff_col)[:60]}'")
    print(f"Valeurs numeriques extraites : n={int(eff.notna().sum())}, somme={eff.sum()}")
    if eff.notna().sum() > 0 and eff.sum() > 0:
        print(f"Part seniors sur base effectif declare : {pct(seniors, eff.sum())}% -> {pct_int(seniors, eff.sum())}%")
else:
    print("\nAucune colonne effectif total identifiee automatiquement.")

# Totaux par repondant vs table dashboard (3 031 / 1 506)
print(f"\nRappel table dashboard : avec PGE total=3 031 seniors 47,0% ; sans PGE total=1 506 seniors 45,6%")
print(f"Recalcul               : avec PGE total={int(total)} ; sans PGE total={int(t2)}")
print(f"Ecart de base avec PGE : {int(total) - 3031} tetes ; sans PGE : {int(t2) - 1506} tetes")

# Hypothese : le dashboard a ete calcule sans un repondant (~123 tetes)
diff = int(total) - 3031
cand = tot_par_rep[tot_par_rep.round(0).astype(int) == diff]
print(f"\nRepondant(s) dont le total pyramide = {diff} : {len(cand)}")
for i in cand.index:
    s_i = int(sen_par_rep[i])
    f_i = int(filled.loc[i, [cols[1], cols[3], cols[5], cols[7]]].sum())
    t3 = total - tot_par_rep[i]
    s3 = seniors - s_i
    fem3 = femmes - f_i
    t4 = t2 - tot_par_rep[i]
    s4 = s2 - s_i
    print(f"  Ligne anonyme : total={int(tot_par_rep[i])}, seniors={s_i}, femmes={f_i}")
    print(f"  Base 21 moins cette ligne (avec PGE) : total={int(t3)}, seniors={int(s3)}, "
          f"part={pct(s3,t3)}% -> {pct_int(s3,t3)}%, femmes={pct(fem3,t3)}%")
    print(f"  Base 21 moins cette ligne (sans PGE) : total={int(t4)}, seniors={int(s4)}, "
          f"part={pct(s4,t4)}% -> {pct_int(s4,t4)}%")

# CONCLUSION DE LA CONTRE-EXPERTISE (02/07/2026) :
# Sur l'export du 30/06 (n=21, pyramide remplie par les 21) :
#   seniors 45+ = 1 460 / 3 154 = 46,3% -> 46% (half-up)
#   sans plus gros employeur : 722 / 1 629 = 44,3% -> 44%
# Le 47,0% du dashboard (et toute sa table : 3 031 tetes, 18,0/35,0/41,7/5,3/36,5 ;
# sans PGE 1 506 tetes, 45,6/46,5) est reproduit EXACTEMENT en excluant 3 repondants
# dont les pyramides totalisent 123 tetes (98+1+24) : le dashboard a ete calcule sur
# une base anterieure de 18 entreprises, pas sur la base validee de 21.
# -> ECART CONFIRME : corriger 47% en 46% (4 pages) et recalculer toute la table Q4.1.
