#!/usr/bin/env python3
"""
Contre-expertise OF-HF-1 : double affichage "ensemble (n=7) vs hors financeur (n=6)"
sur Q2.2, Q3.1, Q4.1, Q5.2 du collège Organismes de formation.

Vérifie :
 1. que les moyennes affichées par le dashboard (n=7 et n=6) sont exactes ;
 2. que chaque question a bien 7 réponses non vides (sinon l'arithmétique
    de reconstitution ne tient pas) ;
 3. si la note individuelle du répondant "financeur" se reconstitue à partir
    des DEUX moyennes ARRONDIES affichées : note ∈ [7*m7 - 6*m6 ± incertitude
    d'arrondi], et si cet intervalle ne contient qu'un seul entier 1..5.

Aucune donnée nominative n'est imprimée. Le répondant "financeur" est
identifié uniquement par son type d'organisme (Q0.7), rôle déjà publié
dans le texte du dashboard.
"""
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

F = "/home/user/dashboard-gpect-issoudun-2026/data/02_organismes_formation.xlsx"
df = pd.read_excel(F, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

cols = list(df.columns)

def r1(x):
    return float(Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

# --- repérage du répondant "financeur" via Q0.7 (type d'organisme) ---
q07 = cols[9]
vals = df[q07].astype(str).str.lower()
mask_fin = vals.str.contains("financ") | vals.str.contains("région") | vals.str.contains("region") | vals.str.contains("conseil")
# aussi la colonne "autre type, précisez"
q07b = cols[10]
vals_b = df[q07b].astype(str).str.lower()
mask_fin_b = vals_b.str.contains("financ") | vals_b.str.contains("région") | vals_b.str.contains("region") | vals_b.str.contains("conseil")
mask = mask_fin | mask_fin_b
n_fin = int(mask.sum())
print(f"\nNb de répondants dont le type d'organisme (Q0.7/Q0.7bis) évoque financeur/région/conseil : {n_fin}")
if n_fin != 1:
    print("Types d'organisme distincts (Q0.7) et effectifs (agrégat non nominatif) :")
    print(df[q07].value_counts(dropna=False).to_string())
idx_fin = df.index[mask].tolist()
print(f"Le répondant 'financeur' est UNIQUE dans le panel : {n_fin == 1}")

# --- questions ciblées ---
# Q2.2 : colonnes 35..42 (8 items), Q3.1 : col 44, Q4.1 : col 55, Q5.2 : col 61
Q22 = {
    "Intelligence artificielle": 35,
    "Automatisation, cobotique": 36,
    "Maintenance avancée & prédictive": 37,
    "Transition énergétique & décarbonation": 38,
    "Cybersécurité industrielle": 39,
    "Management de la performance": 40,
    "Conduite du changement & projet": 41,
    "Transmission des savoir-faire & tutorat": 42,
}
SINGLES = {"Q3.1": 44, "Q4.1": 55, "Q5.2": 61}

# valeurs affichées par le dashboard (v = ensemble n=7 ; v2 = hors financeur n=6)
DASH = {
    "Q2.2 [Management de la performance]": (3.4, 3.8),
    "Q2.2 [Conduite du changement & projet]": (3.3, 3.7),
    "Q2.2 [Transmission des savoir-faire & tutorat]": (3.3, 3.7),
    "Q2.2 [Maintenance avancée & prédictive]": (2.9, 3.2),
    "Q2.2 [Automatisation, cobotique]": (2.7, 3.0),
    "Q2.2 [Transition énergétique & décarbonation]": (2.4, 2.7),
    "Q2.2 [Intelligence artificielle]": (2.3, 2.5),
    "Q2.2 [Cybersécurité industrielle]": (1.1, 1.2),
    "Q3.1": (3.0, 3.0),   # "identique hors financeur"
    "Q4.1": (4.0, 4.3),
    "Q5.2": (2.6, 2.8),
}

def check(label, colidx):
    s = pd.to_numeric(df[cols[colidx]], errors="coerce")
    n_all = int(s.notna().sum())
    m7 = r1(s.mean())
    s6 = s[~mask]
    n6 = int(s6.notna().sum())
    m6 = r1(s6.mean())
    d7, d6 = DASH[label]
    ok7 = (m7 == d7)
    ok6 = (m6 == d6)
    # reconstitution à partir des moyennes ARRONDIES affichées
    est = n_all * d7 - n6 * d6
    # incertitude : chaque moyenne arrondie à ±0,05 près
    lo = n_all * (d7 - 0.05) - n6 * (d6 + 0.05)
    hi = n_all * (d7 + 0.05) - n6 * (d6 - 0.05)
    candidats = [k for k in range(1, 6) if lo <= k <= hi]
    vraie = s[mask].dropna()
    vraie_note = float(vraie.iloc[0]) if len(vraie) == 1 else None
    recon = (len(candidats) == 1 and vraie_note is not None
             and candidats[0] == vraie_note)
    print(f"\n{label}")
    print(f"  n réponses = {n_all} (ensemble) / {n6} (hors financeur)")
    print(f"  moyenne ensemble : calculée {m7} vs dashboard {d7} -> {'OK' if ok7 else 'ECART'}")
    print(f"  moyenne hors financeur : calculée {m6} vs dashboard {d6} -> {'OK' if ok6 else 'ECART'}")
    print(f"  reconstitution : 7*m7 - 6*m6 = {est:.1f}, intervalle [{lo:.2f} ; {hi:.2f}], "
          f"entiers candidats {candidats}")
    print(f"  la note individuelle du financeur est-elle retrouvée exactement ? "
          f"{'OUI' if recon else 'NON (intervalle ambigu ou note non entiere)'}")
    return ok7, ok6, recon

res = []
for lab, (dashlab, ci) in zip(
    ["Management de la performance", "Conduite du changement & projet",
     "Transmission des savoir-faire & tutorat", "Maintenance avancée & prédictive",
     "Automatisation, cobotique", "Transition énergétique & décarbonation",
     "Intelligence artificielle", "Cybersécurité industrielle"],
    [(f"Q2.2 [{k}]", Q22[k]) for k in
     ["Management de la performance", "Conduite du changement & projet",
      "Transmission des savoir-faire & tutorat", "Maintenance avancée & prédictive",
      "Automatisation, cobotique", "Transition énergétique & décarbonation",
      "Intelligence artificielle", "Cybersécurité industrielle"]]):
    res.append(check(dashlab, ci))

for q, ci in SINGLES.items():
    res.append(check(q, ci))

nb_ok7 = sum(1 for a, _, _ in res if a)
nb_ok6 = sum(1 for _, b, _ in res if b)
nb_rec = sum(1 for _, _, c in res if c)
print(f"\n=== BILAN ===")
print(f"Moyennes 'ensemble (n=7)' conformes au dashboard : {nb_ok7}/{len(res)}")
print(f"Moyennes 'hors financeur (n=6)' conformes au dashboard : {nb_ok6}/{len(res)}")
print(f"Questions où la note individuelle du financeur se reconstitue "
      f"sans ambiguïté depuis les valeurs affichées : {nb_rec}/{len(res)}")
