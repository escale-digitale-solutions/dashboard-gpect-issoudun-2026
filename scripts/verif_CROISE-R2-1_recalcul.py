#!/usr/bin/env python3
"""Contre-expertise CROISE Risque 2 :
"71% des entreprises investissent (robots, ERP), mais 56% jugent leurs
compétences suffisantes".
Recalcul indépendant de Q2.4 (investissements à 3 ans) et Q2.5
(nouvelles compétences nécessaires) sur data/01_entreprises.xlsx.
Aucune donnée en dur ; sortie agrégée anonymisée uniquement.
"""
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

PATH = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"


def pct(k, n):
    """Pourcentage arrondi à l'entier, round half up (convention dashboard)."""
    return int((Decimal(k) * 100 / Decimal(n))
               .quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def main():
    df = pd.read_excel(PATH, engine="openpyxl")
    print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

    col_q24 = df.columns[22]
    col_q25 = df.columns[23]
    print(f"\nColonne [22] : {col_q24}")
    print(f"Colonne [23] : {col_q25}")

    # --- Q2.4 ---
    s24 = df[col_q24].dropna().astype(str).str.strip()
    s24 = s24[s24 != ""]
    n24 = len(s24)
    print(f"\nQ2.4 — n (réponses non vides) = {n24}")
    vc24 = s24.value_counts()
    for val, k in vc24.items():
        print(f"  {k}/{n24} = {pct(k, n24)}% : {val!r}")
    inv_mask = s24.str.lower().str.startswith("oui")
    k_inv = int(inv_mask.sum())
    print(f"Q2.4 'Oui' (toutes modalités confondues) : "
          f"{k_inv}/{n24} = {pct(k_inv, n24)}%")

    # --- Q2.5 ---
    s25 = df[col_q25].dropna().astype(str).str.strip()
    s25 = s25[s25 != ""]
    n25 = len(s25)
    print(f"\nQ2.5 — n (réponses non vides) = {n25}")
    vc25 = s25.value_counts()
    for val, k in vc25.items():
        print(f"  {k}/{n25} = {pct(k, n25)}% : {val!r}")
    suff_mask = s25.str.lower().str.startswith("non")
    k_suff = int(suff_mask.sum())
    print(f"Q2.5 'Non / compétences suffisantes' : "
          f"{k_suff}/{n25} = {pct(k_suff, n25)}%")

    # Croisement de contrôle : les répondants Q2.5 sont-ils bien
    # les 'Oui' de Q2.4 ?
    both = df[[col_q24, col_q25]].copy()
    both.columns = ["q24", "q25"]
    both["rep25"] = both["q25"].notna() & (
        both["q25"].astype(str).str.strip() != "")
    n_rep25_parmi_oui = int(
        (both["rep25"] & both["q24"].astype(str).str.strip()
         .str.lower().str.startswith("oui")).sum())
    print(f"\nContrôle : répondants Q2.5 qui ont dit 'Oui' à Q2.4 : "
          f"{n_rep25_parmi_oui}/{n25}")

    # % 'compétences suffisantes' rapporté aux 21 entreprises (base totale)
    print(f"\nLecture alternative : 'compétences suffisantes' sur base 21 : "
          f"{k_suff}/21 = {pct(k_suff, 21)}%")


if __name__ == "__main__":
    main()
