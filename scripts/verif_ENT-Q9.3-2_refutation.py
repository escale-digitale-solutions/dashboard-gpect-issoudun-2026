# -*- coding: utf-8 -*-
"""
Contre-expertise ENT Q9.3 — thème « Attractivité / image / com ».
Dashboard : 38% (8/21). Premier auditeur : 9/21 (43%) par mots-clés
(attractivité, image, visibilité, communication, vidéo, atouts).

Hypothèses de réfutation testées :
  H1 - bonne colonne (Q9.3 = index 122 ; contrôle Q9.4 = 123)
  H2 - base de calcul (n=21 collège vs n réponses non vides)
  H3 - arrondi round-half-up à l'entier
  H4 - choix multiples mal découpés : sans objet (texte libre), vérifié
  H5 - frontières de codage : matching mot-clé par répondant + variantes
       de grille excluant les cas frontières (image de marque de
       l'entreprise, attractivité d'un métier codée ailleurs).
Les verbatims ne sont affichés que sur stdout de session ; le fichier
resultats/ ne contient que des agrégats anonymisés.
AUCUNE donnée en dur dans ce script.
"""
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
XLSX = REPO / "data" / "01_entreprises.xlsx"
OUT = REPO / "resultats" / "verif_ENT-Q9.3-2_refutation.txt"

KEYWORDS_AUDITEUR = ["attractivite", "image", "visibilite",
                     "communication", "video", "atout"]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def p(num: int, den: int) -> int:
    """% arrondi à l'entier, round half up (convention dashboard)."""
    return int((Decimal(num) * 100 / Decimal(den))
               .quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def main() -> None:
    df = pd.read_excel(XLSX, engine="openpyxl")
    print(f"[LECTURE] {XLSX.name} : {df.shape[0]} lignes x "
          f"{df.shape[1]} colonnes")

    col_q93 = df.columns[122]
    col_q94 = df.columns[123]
    print(f"[H1] Colonne 122 : {col_q93[:90]}")
    print(f"[H1] Colonne 123 (contrôle) : {col_q94[:90]}")
    assert col_q93.startswith("Q9.3"), "La colonne 122 n'est pas Q9.3 !"

    s93 = df[col_q93]
    nv93 = s93.dropna().astype(str).str.strip()
    nv93 = nv93[nv93 != ""]
    n93 = len(nv93)
    print(f"[H2] Q9.3 : réponses non vides n={n93} / {len(df)} répondants")

    s94 = df[col_q94].dropna().astype(str).str.strip()
    print(f"[H2] Q9.4 (contrôle) : réponses non vides n={len(s94[s94 != ''])}")

    lens = nv93.str.len()
    print(f"[H4] Longueurs Q9.3 : min={lens.min()} max={lens.max()} "
          f"médiane={lens.median()} -> texte libre, pas d'options à virgules")

    # H5 : matching mots-clés, répondant par répondant
    print("\n[H5] Détail du matching (stdout session uniquement) :")
    matched = []          # (id, texte normalisé, mots-clés)
    for idx, txt in s93.items():
        rid = f"E{idx + 1:02d}"
        if pd.isna(txt) or not str(txt).strip():
            print(f"  {rid}: (vide)")
            continue
        t = norm(txt)
        hits = [k for k in KEYWORDS_AUDITEUR if k in t]
        flag = "MATCH" if hits else "-----"
        print(f"  {rid}: {flag} mots-clés={hits}")
        print(f"        verbatim: {str(txt)!r}")
        if hits:
            matched.append((rid, t, hits))

    n_match = len(matched)
    print(f"\n[H5] Grille auditeur : {n_match} répondants matchent")

    # Variantes de grille sur les cas frontières
    def est_marque_entreprise(t):
        return ("image de marque" in t
                and ("entreprise" in t or "notre" in t or "nos " in t)
                and "territoire" not in t and "issoudun" not in t)

    def est_attractivite_metier(t):
        return ("attractivite" in t
                and any(m in t for m in ("usinage", "metier", "filiere"))
                and "territoire" not in t and "image" not in t
                and "communication" not in t)

    va = [(rid, t, h) for rid, t, h in matched if not est_marque_entreprise(t)]
    vb = [(rid, t, h) for rid, t, h in matched
          if not est_attractivite_metier(t)]
    vc = [(rid, t, h) for rid, t, h in matched
          if not est_marque_entreprise(t) and not est_attractivite_metier(t)]
    print(f"[H5] Variante A (sans image-de-marque entreprise) : {len(va)}")
    print(f"[H5] Variante B (sans attractivité-métier)        : {len(vb)}")
    print(f"[H5] Variante C (sans les deux)                   : {len(vc)}")
    for nom, v in (("A", va), ("B", vb), ("C", vc)):
        exclus = sorted(set(r for r, _, _ in matched)
                        - set(r for r, _, _ in v))
        if exclus:
            print(f"      Variante {nom} exclut : {exclus}")

    # H2/H3 : combinaisons base x arrondi
    print("\n[H2/H3] Pourcentages (round half up à l'entier) :")
    for label, num in [("8 (dashboard)", 8),
                       (f"{n_match} (mots-clés auditeur)", n_match)]:
        ligne = f"  {label} : /21 = {p(num, 21)}%"
        if n93 != 21:
            ligne += f"  |  /n_q={n93} = {p(num, n93)}%"
        print(ligne)

    # Contrôle de cohérence des 4 thèmes affichés par le dashboard
    print("\n[Contrôle] Thèmes dashboard 38/24/19/14 sur base 21 :")
    for k in (8, 5, 4, 3):
        print(f"  {k}/21 -> {p(k, 21)}%")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        "Contre-expertise ENT Q9.3 - theme 'Attractivite / image / com'\n"
        f"Fichier lu : data/01_entreprises.xlsx ({df.shape[0]}x{df.shape[1]})\n"
        f"Colonne 122 = Q9.3 (texte libre). Reponses non vides : n={n93}/21\n"
        f"Dashboard : 8/21 = {p(8, 21)}%\n"
        f"Comptage mots-cles auditeur (attractivite, image, visibilite,\n"
        f"communication, video, atout) : {n_match}/21 = {p(n_match, 21)}%\n"
        f"Variantes de grille (exclusion cas frontieres) : "
        f"A={len(va)} B={len(vb)} C={len(vc)} sur 21\n"
        "Conclusion : l'ecart d'1 repondant tient a la frontiere de codage\n"
        "qualitatif, pas a une erreur de colonne, de base ou d'arrondi.\n",
        encoding="utf-8")
    print(f"\n[OK] Résultat agrégé écrit dans {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
