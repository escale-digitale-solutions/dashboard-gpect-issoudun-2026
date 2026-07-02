# Contre-expertise SYN-Q26-1 : la citation dashboard
# « Refonte de l'orientation ; simplification des démarches administratives de financement »
# est-elle fidèle à la réponse source (col 26 du xlsx syndicats) ?
# Le script n'imprime que des indicateurs de présence/absence de motifs
# déjà publiés sur le dashboard (aucune donnée nominative, aucun verbatim intégral).

import pandas as pd
import re
import unicodedata

PATH = "/home/user/dashboard-gpect-issoudun-2026/data/04_syndicats.xlsx"
df = pd.read_excel(PATH, engine="openpyxl")
print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).lower().strip()

# Motifs à tester (fragments déjà publiés sur le dashboard ou allégués par l'audit)
motifs = {
    "refonte": "refonte",
    "orientation (dans la meme cellule que refonte)": None,  # traité à part
    "programmes scolaires": "programmes scolaires",
    "simplification": "simplification",
    "demarches administratives": "demarches administratives",
    "financement": "financement",
}

# Colonnes candidates : Q26 = index 26 (« une seule action prioritaire »),
# mais le bloc dashboard agrège aussi 27 (actions rapides) et 28 (résultats attendus).
for col_idx in (26, 27, 28, 29):
    col = df.columns[col_idx]
    serie = df[col].dropna().astype(str)
    print(f"\n--- Colonne [{col_idx}] (n non vides = {len(serie)}) : {col[:60]}...")
    for i, val in serie.items():
        v = norm(val)
        flags = []
        for name, pat in motifs.items():
            if pat and pat in v:
                flags.append(name)
        if "refonte" in v:
            # contexte immédiat autour de 'refonte' (max 60 caractères), pour
            # vérifier l'objet de la refonte — fragment de verbatim dont une
            # version est déjà publiée sur le dashboard
            m = re.search(r"refonte.{0,60}", v)
            flags.append(f"contexte refonte -> '{m.group(0)}'")
        if flags:
            print(f"  Repondant S{i+1:02d} : {flags}")

# Vérification exacte des deux formulations concurrentes sur la colonne 26
serie26 = df[df.columns[26]].dropna().astype(str).map(norm)
a = serie26.str.contains("refonte de l'orientation", regex=False) | serie26.str.contains("refonte de lorientation", regex=False)
b = serie26.str.contains("refonte des programmes scolaires", regex=False)
print(f"\nCol 26 - cellules contenant 'refonte de l'orientation' : {int(a.sum())}")
print(f"Col 26 - cellules contenant 'refonte des programmes scolaires' : {int(b.sum())}")
# idem colonnes 27-29 au cas où la citation viendrait d'une autre question
for ci in (27, 28, 29):
    s = df[df.columns[ci]].dropna().astype(str).map(norm)
    print(f"Col {ci} - 'refonte de l'orientation' : {int(s.str.contains('refonte de l', regex=False).sum())} ; "
          f"'refonte des programmes scolaires' : {int(s.str.contains('refonte des programmes', regex=False).sum())}")
