"""Protocole §4 — Annonce des dimensions des 4 exports xlsx (30/06/2026).

Lecture seule. Aucun calcul statistique : uniquement lignes (répondants)
x colonnes par fichier, noms de feuilles, et contrôle de cohérence avec
la base validée (21 / 7 / 7 / 7 = 42 répondants).
"""
import pandas as pd
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

FICHIERS = {
    "01_entreprises.xlsx": ("Entreprises", 21),
    "02_organismes_formation.xlsx": ("Organismes de formation", 7),
    "03_acteurs_emploi.xlsx": ("Acteurs de l'emploi", 7),
    "04_syndicats.xlsx": ("Syndicats & org. professionnelles", 7),
}

total = 0
for nom, (college, attendu) in FICHIERS.items():
    chemin = DATA / nom
    xls = pd.ExcelFile(chemin, engine="openpyxl")
    print(f"\n=== {nom} — collège {college} ===")
    print(f"Feuilles : {xls.sheet_names}")
    for feuille in xls.sheet_names:
        df = pd.read_excel(chemin, sheet_name=feuille, engine="openpyxl")
        lignes, colonnes = df.shape
        print(f"  Feuille « {feuille} » : {lignes} lignes (répondants) x {colonnes} colonnes")
        if feuille == xls.sheet_names[0]:
            total += lignes
            statut = "OK" if lignes == attendu else f"ECART (attendu n={attendu})"
            print(f"  Contrôle base validée : {statut}")

print(f"\nTOTAL répondants (1re feuille de chaque fichier) : {total} (base validée : 42)")
