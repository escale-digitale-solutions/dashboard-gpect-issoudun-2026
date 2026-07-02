# -*- coding: utf-8 -*-
"""
Contre-expertise (2e audit, recalcul independant) — OF Q11.1
Verbatim dashboard conteste : « Établir des partenariats pérennes avec les entreprises »

Question : les 5 citations du bloc verbatims OF Q11.1 du dashboard sont-elles
des citations exactes des reponses a la colonne
"Q11.1 — Si une seule action concrete devait sortir de cette demarche GPECT
pour votre organisme, laquelle serait la plus utile ?"
(data/02_organismes_formation.xlsx) ?

Sorties : metriques agregees uniquement (n, correspondance exacte,
couverture lexicale, mots-cles presents/absents). AUCUN verbatim brut
n'est ecrit dans resultats/ ni imprime par defaut.
Les citations testees sont celles deja PUBLIEES sur le dashboard public.
"""
import re
import sys
import unicodedata
import pandas as pd

XLSX = "/home/user/dashboard-gpect-issoudun-2026/data/02_organismes_formation.xlsx"
OUT = "/home/user/dashboard-gpect-issoudun-2026/resultats/verif_OF-Q11.1-1_recalcul.txt"

# Citations telles qu'affichees sur le dashboard public (index.html, zone OF)
DASHBOARD_QUOTES = [
    "Communication sur les atouts du territoire",
    "Bien lister les besoins en formation / recrutement",
    "Établir des partenariats pérennes avec les entreprises",
    "Comment on embarque les entreprises du territoire ?",
    ("Que l'animateur GPECT se rende directement en entreprise pour "
     "vulgariser la démarche — « prendre son bâton de pèlerin » — en "
     "commençant par des outils simples : pyramide des âges, compétences clés"),
]

STOPWORDS = {
    "le", "la", "les", "l", "un", "une", "des", "de", "du", "d", "et",
    "a", "à", "en", "sur", "pour", "avec", "que", "qui", "se", "son",
    "sa", "ses", "on", "ou", "au", "aux", "par", "ne", "pas", "est",
}


def norm(s: str) -> str:
    """minuscules + sans accents + espaces normalises"""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.lower()).strip()


def toks(s: str):
    return [t for t in re.findall(r"[a-z0-9]+", norm(s)) if t not in STOPWORDS]


def main():
    df = pd.read_excel(XLSX, engine="openpyxl")
    print(f"Fichier lu : {df.shape[0]} lignes x {df.shape[1]} colonnes")

    q11 = [c for c in df.columns if str(c).startswith("Q11.1")]
    assert len(q11) == 1, f"Colonne Q11.1 non unique : {q11}"
    col = q11[0]
    print(f"Colonne source (index {list(df.columns).index(col)}) : {col}")

    s = df[col].dropna().astype(str)
    s = s[s.str.strip() != ""]
    n = len(s)
    print(f"n reponses non vides Q11.1 = {n} / {df.shape[0]} repondants")

    rep_norm = [norm(r) for r in s]
    rep_toks = [set(toks(r)) for r in s]
    corpus = set().union(*rep_toks) if rep_toks else set()

    out = [
        "Contre-expertise (recalcul independant) - OF Q11.1, bloc verbatims dashboard",
        "Source : data/02_organismes_formation.xlsx, colonne Q11.1",
        f"n reponses non vides = {n} (sur {df.shape[0]} repondants) ; citations affichees = {len(DASHBOARD_QUOTES)}",
        "",
        "exacte = la citation normalisee est une sous-chaine d'une reponse",
        "couv. corpus = % des mots significatifs de la citation presents dans au moins une reponse",
        "couv. meilleure rep. = idem, restreint a la meilleure reponse unique",
        "",
    ]

    for i, q in enumerate(DASHBOARD_QUOTES, 1):
        qn = norm(q)
        exact = any(qn in r for r in rep_norm)
        qt = toks(q)
        absents = [t for t in qt if t not in corpus]
        couv = 100.0 * (len(qt) - len(absents)) / len(qt) if qt else 0.0
        best = max(
            (100.0 * sum(1 for t in qt if t in rt) / len(qt) for rt in rep_toks),
            default=0.0,
        ) if qt else 0.0
        line = (f"Citation {i} : exacte={'OUI' if exact else 'NON'} | "
                f"couv. corpus={couv:.0f}% | couv. meilleure rep.={best:.0f}% | "
                f"mots absents des {n} reponses = {absents if absents else 'aucun'}")
        out.append(line)
        print(line)

    out.append("")
    print()
    for mot in ["etablir", "partenariat", "perenn", "entrepris"]:
        hits = sum(1 for rn in rep_norm if mot in rn)
        line = f"Racine '{mot}' presente (sous-chaine) dans {hits}/{n} reponses"
        out.append(line)
        print(line)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"\nResultats agreges ecrits dans {OUT}")

    # Controle visuel optionnel, stdout uniquement, jamais ecrit dans le repo
    if "--inspect" in sys.argv:
        print("\n--- INSPECTION BRUTE (ne pas copier dans un livrable) ---")
        for i, r in enumerate(s, 1):
            print(f"[R{i:02d}] {r!r}")


if __name__ == "__main__":
    main()
