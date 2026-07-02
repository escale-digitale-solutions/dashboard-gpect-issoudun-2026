# Contre-expertise CROISE Risque 2 :
# "71% des entreprises investissent, mais 56% jugent leurs compétences suffisantes"
# Vérifie Q2.4 (col 22) et Q2.5 (col 23) du fichier entreprises.
# Aucune donnée en dur ; sortie exclusivement agrégée et anonymisée.

from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

PATH = "/home/user/dashboard-gpect-issoudun-2026/data/01_entreprises.xlsx"


def pct(k, n):
    """% arrondi à l'entier, round half up (convention dashboard)."""
    return int((Decimal(k) * 100 / Decimal(n)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def main():
    df = pd.read_excel(PATH, engine="openpyxl")
    print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

    q24 = df.iloc[:, 22]  # Q2.4 investissements prévus d'ici 3 ans
    q25 = df.iloc[:, 23]  # Q2.5 (conditionnelle) nouvelles compétences nécessaires ?

    print("\n--- Q2.4 :", df.columns[22][:80], "...")
    v24 = q24.dropna().astype(str).str.strip()
    v24 = v24[v24 != ""]
    n24 = len(v24)
    print(f"n (réponses non vides) = {n24}")
    for val, cnt in v24.value_counts().items():
        print(f"  '{val}' : {cnt}  -> {pct(cnt, n24)}% (base n={n24}) ; {pct(cnt, 21)}% (base 21)")

    print("\n--- Q2.5 :", df.columns[23][:80], "...")
    v25 = q25.dropna().astype(str).str.strip()
    v25 = v25[v25 != ""]
    n25 = len(v25)
    print(f"n (réponses non vides) = {n25}")
    for val, cnt in v25.value_counts().items():
        print(f"  '{val}' : {cnt}  -> {pct(cnt, n25)}% (base n={n25}) ; {pct(cnt, 21)}% (base 21)")

    # Croisement de contrôle : les répondants Q2.5 sont-ils bien les "Oui" de Q2.4 ?
    oui24_mask = q24.astype(str).str.strip().str.lower().str.startswith("oui")
    rep25_mask = q25.notna() & (q25.astype(str).str.strip() != "")
    print(f"\nQ2.4 'Oui' (préfixe) : {int(oui24_mask.sum())}")
    print(f"Répondants Q2.5 : {int(rep25_mask.sum())}")
    print(f"Répondants Q2.5 parmi les 'Oui' Q2.4 : {int((oui24_mask & rep25_mask).sum())}")
    print(f"Répondants Q2.5 hors 'Oui' Q2.4 : {int((~oui24_mask & rep25_mask).sum())}")


if __name__ == "__main__":
    main()
