# -*- coding: utf-8 -*-
"""
Contre-expertise OF-INS-1 — insight section 3-4 du collège OF :
« Écart de 1 à 1,7 point » entre auto-évaluation OF (Q4.1) et notes
des utilisateurs (ENT Q7.6, ACT Q6.1).

Vérifie :
  1. les 3 moyennes sous-jacentes (brutes + arrondies à 1 décimale, half-up)
  2. l'écart calculé sur les moyennes AFFICHÉES (arrondies)
  3. l'écart calculé sur les moyennes BRUTES (hypothèse d'arrondi en aval)
  4. la sensibilité au n (valeurs manquantes, valeurs hors échelle 1-5)
Aucune donnée individuelle n'est affichée.
"""
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

DATA = "/home/user/dashboard-gpect-issoudun-2026/data"

def r1(x):  # arrondi 1 décimale, half-up (convention dashboard)
    return float(Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

def analyse(path, col_idx, label):
    df = pd.read_excel(path, engine="openpyxl")
    print(f"{label}: fichier lu {df.shape[0]} lignes x {df.shape[1]} colonnes")
    col = df.columns[col_idx]
    print(f"  colonne [{col_idx}] = {col[:90]}")
    s = pd.to_numeric(df[col], errors="coerce")
    n_nonvide = df[col].notna().sum()
    n_num = s.notna().sum()
    hors_echelle = int(((s < 1) | (s > 5)).sum())
    m = s.mean()
    print(f"  n non-vide = {n_nonvide} | n numérique = {n_num} | hors échelle 1-5 = {hors_echelle}")
    print(f"  distribution (valeur: effectif) = "
          f"{dict(sorted(s.value_counts().items()))}")
    print(f"  moyenne brute = {m:.6f} -> arrondie 1 déc. (half-up) = {r1(m)}")
    return m

print("=" * 70)
m_of  = analyse(f"{DATA}/02_organismes_formation.xlsx", 55, "OF  Q4.1 (auto-éval couverture besoins)")
print("-" * 70)
m_ent = analyse(f"{DATA}/01_entreprises.xlsx", 94, "ENT Q7.6 (offre formation adaptée)")
print("-" * 70)
m_act = analyse(f"{DATA}/03_acteurs_emploi.xlsx", 53, "ACT Q6.1 (offre formation répond aux besoins)")
print("=" * 70)

of_a, ent_a, act_a = r1(m_of), r1(m_ent), r1(m_act)
print(f"\nMoyennes affichées dashboard : OF 4,0 | ENT 3,1 | ACT 2,3")
print(f"Moyennes recalculées (arrondies) : OF {of_a} | ENT {ent_a} | ACT {act_a}")

print("\n--- Écarts sur moyennes AFFICHÉES (arrondies 1 déc.) ---")
print(f"OF - ENT = {of_a} - {ent_a} = {r1(of_a - ent_a)}")
print(f"OF - ACT = {of_a} - {act_a} = {r1(of_a - act_a)}")

print("\n--- Écarts sur moyennes BRUTES (puis arrondi 1 déc. half-up) ---")
print(f"OF - ENT brut = {m_of - m_ent:.6f} -> {r1(m_of - m_ent)}")
print(f"OF - ACT brut = {m_of - m_act:.6f} -> {r1(m_of - m_act)}")

print("\n--- Écarts bruts arrondis à l'ENTIER (half-up) ---")
def r0(x): return int(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
print(f"OF - ENT -> {r0(m_of - m_ent)} | OF - ACT -> {r0(m_of - m_act)}")

print("\nConclusion attendue : le dashboard affiche « 1 à 1,7 » ; "
      "la borne basse exacte est OF−ENT.")
