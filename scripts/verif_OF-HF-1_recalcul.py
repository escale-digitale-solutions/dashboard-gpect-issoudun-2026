# -*- coding: utf-8 -*-
"""
Contre-expertise OF-HF-1 — Double affichage « ensemble (n=7) vs hors financeur (n=6) »
sur Q2.2 (8 items), Q3.1, Q4.1, Q5.2 du collège Organismes de formation.

Vérifie :
1) que les moyennes n=7 et n=6 (hors financeur) affichées par le dashboard sont exactes ;
2) si la note individuelle du financeur se reconstitue par 7*m7 - 6*m6
   (à partir des moyennes ARRONDIES affichées, comme le ferait un lecteur).

Aucune donnée brute n'est écrite : le résultat ne contient que moyennes agrégées,
écarts et booléens de reconstitution (jamais la note individuelle elle-même).

Sortie : resultats/verif_OF-HF-1_recalcul.txt
"""
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

SRC = "data/02_organismes_formation.xlsx"
OUT = "resultats/verif_OF-HF-1_recalcul.txt"

df = pd.read_excel(SRC, engine="openpyxl")
assert df.shape == (7, 98), f"Dimensions inattendues : {df.shape}"

# Identification du financeur par son rôle (Q0.7, col index 9) — jamais par son nom
col_type = df.columns[9]
mask_fin = df[col_type].astype(str).str.contains("financeur", case=False, na=False)
assert mask_fin.sum() == 1, f"{mask_fin.sum()} ligne(s) 'financeur' trouvée(s), attendu 1"

def r1(x):
    """Arrondi à 1 décimale, half up (convention dashboard)."""
    return float(Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

# (repère, index colonne, libellé court, moyenne n=7 dashboard, moyenne n=6 dashboard)
CHECKS = [
    ("Q2.2", 35, "Intelligence artificielle",              2.3, 2.5),
    ("Q2.2", 36, "Automatisation, cobotique",              2.7, 3.0),
    ("Q2.2", 37, "Maintenance avancée & prédictive",       2.9, 3.2),
    ("Q2.2", 38, "Transition énergétique & décarbonation", 2.4, 2.7),
    ("Q2.2", 39, "Cybersécurité industrielle",             1.1, 1.2),
    ("Q2.2", 40, "Management de la performance",           3.4, 3.8),
    ("Q2.2", 41, "Conduite du changement & projet",        3.3, 3.7),
    ("Q2.2", 42, "Transmission des savoir-faire & tutorat",3.3, 3.7),
    ("Q3.1", 44, "Connaissance des besoins entreprises",   3.0, 3.0),
    ("Q4.1", 55, "Offre couvre bien les besoins",          4.0, 4.3),
    ("Q5.2", 61, "Maîtrise ingénierie AFEST",              2.6, 2.8),
]

lines = []
lines.append("Contre-expertise OF-HF-1 — double moyenne n=7 vs n=6 (hors financeur)")
lines.append(f"Source : {SRC} (7 x 98) — financeur identifié par Q0.7 (rôle), 1 ligne")
lines.append("")
lines.append(f"{'repère':6} {'item':42} {'m7 dash':>8} {'m7 calc':>8} {'m6 dash':>8} {'m6 calc':>8} "
             f"{'OK7':>4} {'OK6':>4} {'n7':>3} {'n6':>3} {'reconst.':>9}")

all_ok = True
recon_all = True
for rep, idx, lab, m7_dash, m6_dash in CHECKS:
    col = df.columns[idx]
    s = pd.to_numeric(df[col], errors="coerce")
    s7 = s.dropna()
    s6 = s[~mask_fin].dropna()
    n7, n6 = len(s7), len(s6)
    m7, m6 = r1(s7.mean()), r1(s6.mean())
    ok7 = (m7 == m7_dash)
    ok6 = (m6 == m6_dash)
    all_ok &= ok7 and ok6
    # Reconstitution comme le ferait un lecteur : à partir des moyennes ARRONDIES affichées
    note_fin = s[mask_fin].dropna()
    if len(note_fin) == 1:
        recon = n7 * m7_dash - n6 * m6_dash
        # la reconstitution "réussit" si l'arrondi entier de recon = la vraie note
        hit = round(recon) == int(note_fin.iloc[0])
    else:
        hit = None  # financeur non-répondant à cet item
    recon_all &= bool(hit) if hit is not None else True
    lines.append(f"{rep:6} {lab:42} {m7_dash:>8} {m7:>8} {m6_dash:>8} {m6:>8} "
                 f"{'oui' if ok7 else 'NON':>4} {'oui' if ok6 else 'NON':>4} {n7:>3} {n6:>3} "
                 f"{('exacte' if hit else 'inexacte') if hit is not None else 'n/a':>9}")

lines.append("")
lines.append(f"Toutes les moyennes du dashboard exactes : {'OUI' if all_ok else 'NON'}")
lines.append(f"Reconstitution de la note individuelle du financeur possible depuis les "
             f"moyennes affichées (round(n7*m7 - n6*m6)) sur tous les items : "
             f"{'OUI' if recon_all else 'NON'}")
lines.append("NB : les notes individuelles reconstituées ne sont volontairement PAS écrites ici.")

txt = "\n".join(lines)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(txt + "\n")
print(txt)
