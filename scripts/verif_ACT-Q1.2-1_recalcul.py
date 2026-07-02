# -*- coding: utf-8 -*-
"""
Contre-expertise ACT Q1.2 — Importance des publics : Réfugiés / primo-arrivants
Sous-groupe "Opérateurs publics" (dashboard : leg2 'Public (n=4)', valeur affichée 2,2).
Recalcul indépendant depuis data/03_acteurs_emploi.xlsx.
Aucune donnée en dur ; sortie agrégée anonymisée uniquement.
"""
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

XLSX = "/home/user/dashboard-gpect-issoudun-2026/data/03_acteurs_emploi.xlsx"

df = pd.read_excel(XLSX, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

# Identification des colonnes par leur intitulé (pas par index en dur)
col_type = [c for c in df.columns if c.startswith("Q0.1")]
col_refu = [c for c in df.columns if c.startswith("Q1.2") and "Réfugiés" in c]
assert len(col_type) == 1, col_type
assert len(col_refu) == 1, col_refu
col_type, col_refu = col_type[0], col_refu[0]
print(f"Colonne type de structure : {col_type!r}")
print(f"Colonne cible : {col_refu!r}")

# Valeurs distinctes du type de structure (catégories fermées, non nominatives)
print("\nRépartition Q0.1 (type de structure) :")
print(df[col_type].value_counts(dropna=False).to_string())

# Définition des sous-groupes conformes au dashboard :
# Intérim = agences d'intérim ; Public = tout le reste (FT, ML, Cap Emploi, APEC)
mask_interim = df[col_type].astype(str).str.contains("intérim", case=False, na=False) | \
               df[col_type].astype(str).str.contains("interim", case=False, na=False)
mask_public = ~mask_interim
print(f"\nEffectifs sous-groupes : Intérim n={mask_interim.sum()} · Public n={mask_public.sum()}")

vals_all = pd.to_numeric(df[col_refu], errors="coerce")
print(f"\nValeurs brutes (échelle 1-5), distribution globale :")
print(vals_all.value_counts(dropna=False).sort_index().to_string())

def stats(mask, label):
    v = vals_all[mask].dropna()
    n = len(v)
    if n == 0:
        print(f"{label}: aucune réponse")
        return
    mean_exact = v.sum() / n
    mean_round = Decimal(str(mean_exact)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    print(f"{label}: n={n} · somme={v.sum():.0f} · moyenne exacte={mean_exact} "
          f"· arrondi half-up 1 déc.={mean_round}")
    print(f"  distribution: {v.value_counts().sort_index().to_dict()}")

print("\n--- Réfugiés / primo-arrivants ---")
stats(mask_interim, "Intérim")
stats(mask_public,  "Public ")
stats(vals_all.notna(), "Ensemble")
