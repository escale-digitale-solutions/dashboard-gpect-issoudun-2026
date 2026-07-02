# -*- coding: utf-8 -*-
"""
Contre-expertise OF-INS-1 — insight section 3-4 du collège OF :
« Écart de 1 à 1,7 point » entre l'auto-évaluation OF (Q4.1) et les
notes des utilisateurs (ENT Q7.6, ACT Q6.1).

Recalcul indépendant depuis les xlsx du 30/06/2026 :
- OF  data/02_organismes_formation.xlsx, col idx 55 : Q4.1
- ENT data/01_entreprises.xlsx,          col idx 94 : Q7.6
- ACT data/03_acteurs_emploi.xlsx,       col idx 53 : Q6.1
Convention dashboard : moyennes à 1 décimale (round half up),
n = réponses non vides.
"""
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

BASE = "/home/user/dashboard-gpect-issoudun-2026/data"

def r1(x):
    return Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

def moyenne(fichier, idx, label):
    df = pd.read_excel(f"{BASE}/{fichier}", engine="openpyxl")
    col = df.columns[idx]
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    m = s.mean()
    print(f"{label}")
    print(f"  fichier   : {fichier} ({df.shape[0]} lignes x {df.shape[1]} colonnes)")
    print(f"  colonne   : [{idx}] {col}")
    print(f"  n non vide: {len(s)} | valeurs distinctes: {sorted(s.unique().tolist())}")
    print(f"  moyenne brute = {m:.6f} -> affichee (1 dec, half up) = {r1(m)}")
    print()
    return m, r1(m), len(s)

of_raw, of_disp, of_n = moyenne("02_organismes_formation.xlsx", 55,
                                "OF Q4.1 - auto-evaluation couverture des besoins")
ent_raw, ent_disp, ent_n = moyenne("01_entreprises.xlsx", 94,
                                   "ENT Q7.6 - offre de formation adaptee aux besoins")
act_raw, act_disp, act_n = moyenne("03_acteurs_emploi.xlsx", 53,
                                   "ACT Q6.1 - offre locale repond aux besoins")

print("=== ECARTS ===")
print(f"Ecart brut OF - ENT : {of_raw - ent_raw:.6f} -> arrondi 1 dec = {r1(of_raw - ent_raw)}")
print(f"Ecart brut OF - ACT : {of_raw - act_raw:.6f} -> arrondi 1 dec = {r1(of_raw - act_raw)}")
print(f"Ecart sur valeurs affichees OF - ENT : {of_disp - ent_disp}")
print(f"Ecart sur valeurs affichees OF - ACT : {of_disp - act_disp}")
print()
print(f"Dashboard (insight 3-4 OF) : 'Ecart de 1 a 1,7 point'")
print(f"Recalcul : ecart de {r1(of_raw - ent_raw)} (vs entreprises, n={ent_n}) "
      f"a {r1(of_raw - act_raw)} (vs acteurs emploi, n={act_n})")
