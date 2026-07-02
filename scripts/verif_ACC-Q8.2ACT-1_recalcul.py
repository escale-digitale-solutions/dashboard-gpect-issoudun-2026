# Contre-expertise ACCUEIL — message clé 5 : "acteurs de l'emploi disposés à 4,7/5"
# Recalcul de ACT Q8.2 (disposition à participer aux actions collectives), colonnes 76-82.
# Aucune donnée en dur ; sortie = agrégats anonymisés uniquement.
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

PATH = "/home/user/dashboard-gpect-issoudun-2026/data/03_acteurs_emploi.xlsx"
df = pd.read_excel(PATH, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

cols = list(df.columns[76:83])  # Q8.2, 7 sous-items
print("\nSous-items Q8.2 :")
for i, c in enumerate(cols, start=76):
    print(f"  [{i}] {c[:120]}")

def r1(x):
    return Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

print("\nMoyennes par item (1->5) :")
means = {}
for i, c in enumerate(cols, start=76):
    s = pd.to_numeric(df[c], errors="coerce").dropna()
    means[c] = s.mean()
    # label court = texte entre crochets
    lab = c.split("[")[-1].rstrip("]")
    print(f"  [{i}] {lab} : moyenne={r1(s.mean())} (brut {s.mean():.4f}), n={len(s)}")
    print(f"        valeurs uniques (comptage) : {dict(s.value_counts().sort_index())}")

# Moyenne des 6 actions collectives (hors item negatif "Aucune participation")
action_cols = [c for c in cols if "Aucune participation" not in c]
sub = df[action_cols].apply(pd.to_numeric, errors="coerce")
all_vals = sub.stack().dropna()
mean_of_item_means = sum(means[c] for c in action_cols) / len(action_cols)
print(f"\nNb d'actions collectives (hors 'Aucune participation') : {len(action_cols)}")
print(f"Moyenne des moyennes d'items (6 actions) : {r1(mean_of_item_means)} (brut {mean_of_item_means:.4f})")
print(f"Moyenne globale toutes cellules (6 actions) : {r1(all_vals.mean())} (brut {all_vals.mean():.4f}), N cellules={len(all_vals)}")

# Verification aussi avec les 7 items (au cas ou)
sub7 = df[cols].apply(pd.to_numeric, errors="coerce")
v7 = sub7.stack().dropna()
print(f"Moyenne globale 7 items (avec 'Aucune') : {r1(v7.mean())} (brut {v7.mean():.4f})")
