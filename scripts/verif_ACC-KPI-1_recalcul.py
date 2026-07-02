# Contre-expertise KPI accueil "2,3/5 Image du bassin — note la plus basse du diagnostic"
# Recalcul indépendant :
#   - ENT Q8.2 (image du bassin, col index 111 de data/01_entreprises.xlsx)
#   - ENT Q4.8 AFEST (col index 66) — comparaison "note la plus basse"
#   - OF Q2.2 Cybersécurité industrielle (col index 39 de data/02_organismes_formation.xlsx)
# Aucune donnée individuelle n'est écrite : uniquement moyennes, n, min/max agrégés.
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

def moy1(s):
    s = pd.to_numeric(s, errors="coerce").dropna()
    n = len(s)
    if n == 0:
        return None, 0
    m = Decimal(str(s.mean())).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return m, n

ent = pd.read_excel("data/01_entreprises.xlsx", engine="openpyxl")
of = pd.read_excel("data/02_organismes_formation.xlsx", engine="openpyxl")
print(f"ENT : {ent.shape[0]} lignes x {ent.shape[1]} colonnes")
print(f"OF  : {of.shape[0]} lignes x {of.shape[1]} colonnes")

col_img = ent.columns[111]
col_afest = ent.columns[66]
col_cyber = of.columns[39]
print(f"\nColonne image  : {col_img[:90]}")
print(f"Colonne AFEST  : {col_afest[:90]}")
print(f"Colonne cyber  : {col_cyber[:90]}")

for lbl, df, col in [("ENT Q8.2 image bassin", ent, col_img),
                     ("ENT Q4.8 AFEST", ent, col_afest),
                     ("OF Q2.2 cybersécurité", of, col_cyber)]:
    vals = pd.to_numeric(df[col], errors="coerce").dropna()
    m, n = moy1(df[col])
    print(f"\n{lbl} : moyenne = {m}/5 (brute {vals.mean():.4f}), n={n}, "
          f"min={vals.min():.0f}, max={vals.max():.0f}")

# Balayage : existe-t-il d'autres moyennes /5 plus basses que Q8.2 dans ces deux fichiers ?
print("\n--- Balayage : colonnes numériques échelle 1-5 avec moyenne < moyenne Q8.2 ---")
ref = pd.to_numeric(ent[col_img], errors="coerce").dropna().mean()
for name, df in [("ENT", ent), ("OF", of)]:
    for i, c in enumerate(df.columns):
        v = pd.to_numeric(df[c], errors="coerce").dropna()
        if len(v) >= 3 and v.min() >= 1 and v.max() <= 5 and v.mean() < ref:
            print(f"  {name}[{i}] moy={v.mean():.2f} n={len(v)} : {str(c)[:80]}")
