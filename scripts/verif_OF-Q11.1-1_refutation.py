# -*- coding: utf-8 -*-
"""
Contre-expertise OF Q11.1 — verbatim dashboard
"Établir des partenariats pérennes avec les entreprises"
Objectif : vérifier si ce texte est une citation exacte (ou fidèle)
d'une réponse de la colonne Q11.1 du fichier OF, ou une paraphrase.

Seules des métriques agrégées (booléens de présence lexicale, taux de
couverture) sont écrites en sortie — JAMAIS le contenu brut des réponses.
Les 5 citations testées sont celles DÉJÀ PUBLIÉES dans le dashboard
public (index.html / bloc verbatims Q11.1 OF) : pas de donnée brute ici.
"""
import re
import unicodedata
import pandas as pd

XLSX = "/home/user/dashboard-gpect-issoudun-2026/data/02_organismes_formation.xlsx"
OUT = "/home/user/dashboard-gpect-issoudun-2026/resultats/verif_OF-Q11.1-1_refutation.txt"

# Citations publiées dans le dashboard (bloc verbatims Q11.1, collège OF)
QUOTES = [
    "Communication sur les atouts du territoire",
    "Bien lister les besoins en formation / recrutement",
    "Établir des partenariats pérennes avec les entreprises",
    "Comment on embarque les entreprises du territoire ?",
    ("Que l'animateur GPECT se rende directement en entreprise pour "
     "vulgariser la démarche — « prendre son bâton de pèlerin » — en "
     "commençant par des outils simples : pyramide des âges, compétences clés"),
]

STOP = {"de", "des", "du", "la", "le", "les", "l", "d", "un", "une", "en",
        "et", "a", "au", "aux", "sur", "avec", "pour", "que", "qu", "on",
        "se", "sa", "son", "ses", "ce", "cette", "par", "dans", "ou"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.lower()


def tokens(s):
    return [t for t in re.findall(r"[a-z0-9]+", norm(s)) if t not in STOP]


df = pd.read_excel(XLSX, engine="openpyxl")
lines = []
lines.append(f"Fichier lu : {XLSX}")
lines.append(f"Dimensions : {df.shape[0]} lignes x {df.shape[1]} colonnes")

# Localiser la colonne Q11.1
col_q111 = [c for c in df.columns if "seule action concr" in norm(c)]
assert len(col_q111) == 1, f"colonnes candidates Q11.1 : {len(col_q111)}"
col_q111 = col_q111[0]
idx = list(df.columns).index(col_q111)
lines.append(f"Colonne Q11.1 trouvee a l'index {idx} (attendu : 94)")

serie = df[col_q111].dropna().astype(str).str.strip()
serie = serie[serie != ""]
lines.append(f"Q11.1 : n={len(serie)} reponses non vides (college n={df.shape[0]})")
lines.append("")

# Colonnes de texte libre alternatives (au cas où la citation viendrait
# d'une autre colonne : Q11.2, Q11.4, ou tout champ libre)
free_cols = [c for c in df.columns if df[c].dropna().astype(str).map(
    lambda v: len(v) > 25).any()]

lines.append("=== Test 1 : chaque citation dashboard vs reponses Q11.1 ===")
lines.append("(couverture = % des mots significatifs de la citation presents")
lines.append(" dans la meilleure reponse ; sous-chaine exacte testee aussi)")
lines.append("")
for i, q in enumerate(QUOTES, 1):
    qt = tokens(q)
    best_cov, best_row, exact = 0.0, None, False
    for ridx, resp in serie.items():
        rt = set(tokens(resp))
        cov = sum(1 for t in qt if t in rt) / len(qt) if qt else 0
        if cov > best_cov:
            best_cov, best_row = cov, ridx
        if norm(q) in norm(resp) or norm(resp) in norm(q):
            exact = True
    missing = []
    if best_row is not None:
        rt_best = set(tokens(serie.loc[best_row]))
        missing = [t for t in qt if t not in rt_best]
    lines.append(f"Citation {i} ({len(qt)} mots significatifs) :")
    lines.append(f"  sous-chaine exacte trouvee : {exact}")
    lines.append(f"  meilleure couverture lexicale : {best_cov:.0%} "
                 f"(repondant OF{(list(serie.index).index(best_row)+1) if best_row is not None else '?'} anonymise)")
    if missing:
        lines.append(f"  mots de la citation ABSENTS de la meilleure reponse : {missing}")
    lines.append("")

lines.append("=== Test 2 : le mot 'perenne(s)' existe-t-il quelque part ? ===")
pat = re.compile(r"perenn|perein|perren")  # variantes/fautes possibles
hits_q111 = int(serie.map(lambda v: bool(pat.search(norm(v)))).sum())
lines.append(f"Occurrences de 'perenn*' dans Q11.1 : {hits_q111} / {len(serie)}")
hits_file = 0
cols_hit = []
for c in df.columns:
    n_hit = int(df[c].dropna().astype(str).map(
        lambda v: bool(pat.search(norm(v)))).sum())
    if n_hit:
        hits_file += n_hit
        cols_hit.append((list(df.columns).index(c), n_hit))
lines.append(f"Occurrences de 'perenn*' dans TOUT le fichier OF : {hits_file} "
             f"(colonnes touchees, par index : {cols_hit})")
lines.append("")

lines.append("=== Test 3 : mots-cles 'partenariat' et 'etablir' dans Q11.1 ===")
for kw in ["partenariat", "etablir", "entreprise"]:
    n_kw = int(serie.map(lambda v: kw in norm(v)).sum())
    lines.append(f"  '{kw}' present dans {n_kw} / {len(serie)} reponses Q11.1")
lines.append("")

lines.append("=== Test 4 : citation 3 vs TOUTES les colonnes texte libre ===")
q3t = tokens(QUOTES[2])
best_any = 0.0
best_col = None
for c in free_cols:
    for v in df[c].dropna().astype(str):
        rt = set(tokens(v))
        cov = sum(1 for t in q3t if t in rt) / len(q3t)
        if cov > best_any:
            best_any, best_col = cov, list(df.columns).index(c)
lines.append(f"Meilleure couverture de la citation 3 sur l'ensemble des "
             f"colonnes texte libre : {best_any:.0%} (colonne index {best_col})")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
