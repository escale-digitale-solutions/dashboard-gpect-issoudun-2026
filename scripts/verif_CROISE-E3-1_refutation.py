# -*- coding: utf-8 -*-
"""
Contre-expertise CROISE / Écart 3 (gapBars mobilité).
Dashboard : Syndicats 4,3/5 ("86% => équiv. ~4,3/5") > Acteurs 3,7 > Entreprises 2,5.
Auditeur 1 : la vraie échelle 1-5 syndicats (col 18) donne 3,3/5 (n=7) ; le 86% (6/7)
est une fréquence de citation en choix multiple, pas une note.

Vérifications :
  A. SYN col 18 (échelle 1-5 mobilité) : n, valeurs distinctes, moyenne (round half up, 1 déc.)
  B. SYN col 17 (choix multiple freins) : inspection des cellules brutes, comptage
     de l'option "mobilité rurale", % base répondants (round half up, entier)
  C. ACT col 36 (Q4.1 frein mobilité/transports) : moyenne
  D. ENT col 31 (Q3.3 contraintes Transport) : moyenne
  E. Test de la "conversion" 86% -> 4,3/5 (0.857*5 = 4.29)
Aucune donnée brute nominative n'est imprimée (les cellules de la question choix
multiple col 17 ne contiennent pas d'information nominative : on n'imprime que
les libellés d'options agrégés).
"""
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

DATA = "/home/user/dashboard-gpect-issoudun-2026/data/"

def rhu(x, nd):
    q = Decimal("1") if nd == 0 else Decimal("0." + "0"*(nd-1) + "1")
    return float(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP))

syn = pd.read_excel(DATA + "04_syndicats.xlsx", engine="openpyxl")
act = pd.read_excel(DATA + "03_acteurs_emploi.xlsx", engine="openpyxl")
ent = pd.read_excel(DATA + "01_entreprises.xlsx", engine="openpyxl")
print(f"SYN {syn.shape} | ACT {act.shape} | ENT {ent.shape}")

# --- A. SYN col 18 : échelle 1-5 mobilité ---
c18 = syn.columns[18]
print("\n[A] SYN col 18 :", c18)
s18 = pd.to_numeric(syn.iloc[:, 18], errors="coerce").dropna()
print("  n =", len(s18), "| valeurs triées =", sorted(s18.tolist()),
      "| moyenne brute =", s18.mean(), "| arrondi 1 déc. =", rhu(s18.mean(), 1),
      "| médiane =", s18.median())

# --- B. SYN col 17 : choix multiple freins structurants ---
c17 = syn.columns[17]
print("\n[B] SYN col 17 :", c17)
cells = syn.iloc[:, 17].dropna().astype(str)
n_rep = len(cells)
print("  n répondants non vides =", n_rep)
# inventaire des options (split ', ' brut, pour inspection des virgules internes)
from collections import Counter
frag = Counter()
for c in cells:
    for p in c.split(", "):
        frag[p.strip()] += 1
print("  Fragments (split ', ') et effectifs :")
for k, v in frag.most_common():
    print(f"    {v} x {k!r}")
# comptage par sous-chaîne "mobilité" (insensible casse)
n_mob = sum(1 for c in cells if "mobilit" in c.lower())
pct = rhu(100 * n_mob / n_rep, 0)
print(f"  Répondants citant une option contenant 'mobilit' : {n_mob}/{n_rep} = {pct}%")

# --- C. ACT col 36 : Q4.1 mobilité/transports ---
c36 = act.columns[36]
print("\n[C] ACT col 36 :", c36)
a36 = pd.to_numeric(act.iloc[:, 36], errors="coerce").dropna()
print("  n =", len(a36), "| moyenne brute =", a36.mean(),
      "| arrondi 1 déc. =", rhu(a36.mean(), 1))

# --- D. ENT col 31 : Q3.3 contraintes Transport ---
c31 = ent.columns[31]
print("\n[D] ENT col 31 :", c31)
e31 = pd.to_numeric(ent.iloc[:, 31], errors="coerce").dropna()
print("  n =", len(e31), "| moyenne brute =", e31.mean(),
      "| arrondi 1 déc. =", rhu(e31.mean(), 1))

# --- E. la "conversion" du dashboard ---
print("\n[E] Conversion testée par le dashboard : 6/7 * 5 =", rhu(6/7*5, 1),
      " (86% * 5 = 4,3) -> c'est bien une conversion de fréquence, pas une moyenne Likert")
print("    Moyenne réelle échelle 1-5 SYN =", rhu(s18.mean(), 1),
      "vs ACT", rhu(a36.mean(), 1), "vs ENT", rhu(e31.mean(), 1))
