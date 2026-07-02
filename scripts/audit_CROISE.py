# -*- coding: utf-8 -*-
"""
Audit de la page « Analyse croisée » du dashboard GPECT Issoudun 2026.
Recalcule chaque chiffre affiché (convergences, 5 écarts de perception,
matrice inter-collèges, risques, signaux faibles) depuis les 4 exports
xlsx du 30/06/2026. Aucune donnée brute ni verbatim n'est écrit :
uniquement des agrégats anonymes (n, %, moyennes, comptages de mots-clés).

Sortie : resultats/audit_CROISE.json  ({q, label, dashboard, calcule, verdict})
Conventions dashboard : % arrondis à l'entier (half-up), moyennes à 1 décimale,
n = réponses non vides à la question.
"""
import json
import re
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

BASE = "/home/user/dashboard-gpect-issoudun-2026"

ENT = pd.read_excel(f"{BASE}/data/01_entreprises.xlsx", engine="openpyxl")
OF = pd.read_excel(f"{BASE}/data/02_organismes_formation.xlsx", engine="openpyxl")
ACT = pd.read_excel(f"{BASE}/data/03_acteurs_emploi.xlsx", engine="openpyxl")
SYN = pd.read_excel(f"{BASE}/data/04_syndicats.xlsx", engine="openpyxl")


def rnd(x, nd):
    """Arrondi half-up (convention dashboard)."""
    q = Decimal("1") if nd == 0 else Decimal("0.1")
    return float(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP))


def mean1(df, idx):
    """Moyenne à 1 décimale d'une colonne échelle 1-5 (par position)."""
    s = pd.to_numeric(df.iloc[:, idx], errors="coerce").dropna()
    return rnd(s.mean(), 1), int(len(s))


def series_txt(df, idx):
    s = df.iloc[:, idx].dropna().astype(str).str.strip()
    return s[s != ""]


def pct_contains(df, idx, needle, base_n=None):
    """% de répondants (base = non vides sauf base_n) dont la cellule contient needle (littéral)."""
    s = series_txt(df, idx)
    n = base_n if base_n is not None else len(s)
    c = int(s.str.contains(needle, case=False, regex=False).sum())
    return int(rnd(100.0 * c / n, 0)), c, n


def pct_regex(df, idx, pattern, base_n=None):
    """% de répondants dont la cellule (texte libre) matche le motif regex."""
    s = series_txt(df, idx)
    n = base_n if base_n is not None else len(s)
    c = int(s.str.contains(pattern, case=False, regex=True).sum())
    return int(rnd(100.0 * c / n, 0)), c, n


controls = []


def add(q, label, dash, calc, ok=None):
    if ok is None:
        ok = str(dash) == str(calc)
    if isinstance(ok, (bool,)) or hasattr(ok, "item"):  # bool ou numpy.bool_
        ok = "OK" if bool(ok) else "ECART"
    controls.append({"q": q, "label": label, "dashboard": str(dash),
                     "calcule": str(calc), "verdict": str(ok)})


# ---------------------------------------------------------------- header
add("HEAD", "42 répondants (21+7+7+7)", "42",
    ENT.shape[0] + OF.shape[0] + ACT.shape[0] + SYN.shape[0])

# ============================================================ SECTION 1 — CONVERGENCES
# CV1 — tension métiers techniques
s = series_txt(ENT, 25)  # Q3.2
n = len(s)
c = int(s.str.startswith("Oui").sum())
add("CV1/ENT-Q3.2", "Entreprises : 95% en tension (Oui maj.+ponct.)", 95,
    f"{int(rnd(100 * c / n, 0))} ({c}/{n})", int(rnd(100 * c / n, 0)) == 95)

m, n = mean1(ACT, 25)  # Q3.1 maintenance
add("CV1/ACT-Q3.1", "Acteurs : difficulté maintenance /5", "4,9", f"{m} (n={n})", m == 4.9)
m, n = mean1(ACT, 26)  # Q3.1 CNC/robots
add("CV1/ACT-Q3.1", "Acteurs : difficulté programmation CNC/robots /5", "4,9", f"{m} (n={n})", m == 4.9)

p, c, n = pct_regex(SYN, 10, r"usinage|fraiseur|tourneur|ajusteur")
add("CV1/SYN-C10", "Syndicats : usinage cité (métiers en tension, texte libre)", 43,
    f"{p} ({c}/{n})", p == 43)
p, c, n = pct_regex(SYN, 10, r"qualit|méthode|contrôle|controle")
add("CV1/SYN-C10", "Syndicats : qualité/méthodes cité (texte libre)", 43,
    f"{p} ({c}/{n})", p == 43)

# CV2 — offre de formation locale
m, n = mean1(ACT, 53)  # Q6.1
add("CV2/ACT-Q6.1", "Acteurs : offre formation locale /5", "2,3", f"{m} (n={n})", m == 2.3)
m, n = mean1(ENT, 94)  # Q7.6
add("CV2/ENT-Q7.6", "Entreprises : offre formation adaptée /5", "3,1", f"{m} (n={n})", m == 3.1)
s = series_txt(SYN, 14)
n = len(s)
c = int(s.str.contains("Peu adaptée|Partiellement adaptée", case=False, regex=True).sum())
add("CV2/SYN-C14", "Syndicats : 71% « peu/partiellement adaptée »", 71,
    f"{int(rnd(100 * c / n, 0))} ({c}/{n})", int(rnd(100 * c / n, 0)) == 71)

# CV3 — attractivité / image
s = series_txt(ENT, 110)  # Q8.1 choix multiple
n = len(s)
c = int(s.str.contains("Image globale du territoire", case=False, regex=False).sum())
p = int(rnd(100 * c / n, 0))
add("CV3/ENT-Q8.1", "Entreprises : image citée comme frein territorial", 95, f"{p} ({c}/{n})", p == 95)
# rang n°1 parmi les options fixes de Q8.1
opts_q81 = {
    "Image globale du territoire": c,
    "Offre de soins": int(s.str.contains("Offre de soins", case=False, regex=False).sum()),
    "transports en commun": int(s.str.contains("transports en commun", case=False, regex=False).sum()),
    "logement": int(s.str.contains("logement", case=False, regex=False).sum()),
    "services à la personne": int(s.str.contains("services à la personne", case=False, regex=False).sum()),
    "emploi pour le conjoint": int(s.str.contains("conjoint", case=False, regex=False).sum()),
    "animation culturelle": int(s.str.contains("animation culturelle", case=False, regex=False).sum()),
}
rang1 = max(opts_q81, key=opts_q81.get)
add("CV3/ENT-Q8.1", "Image = frein n°1 des entreprises", "frein n°1",
    f"n°1 = {rang1}", rang1 == "Image globale du territoire")

m, n = mean1(ENT, 111)  # Q8.2
add("CV3/ENT-Q8.2", "Entreprises : image auprès des candidats /5", "2,3", f"{m} (n={n})", m == 2.3)
m, n = mean1(ACT, 79)  # Q8.2 campagne commune
add("CV3/ACT-Q8.2", "Acteurs : disposition campagne commune /5", "4,7", f"{m} (n={n})", m == 4.7)

# « attractivité » 1er thème ouvert des syndicats — source : col 23 (thèmes sur lesquels
# les entreprises seraient prêtes à s'engager, texte libre). Sur col 26 (action prioritaire
# unique) « attractivité » n'apparaît que 1/7.
s23 = series_txt(SYN, 23)
themes_c23 = {
    "attractivité": int(s23.str.contains(r"attractiv", case=False, regex=True).sum()),
    "formation": int(s23.str.contains(r"formation", case=False, regex=True).sum()),
    "transmission": int(s23.str.contains(r"transmission", case=False, regex=True).sum()),
    "mobilité/transport": int(s23.str.contains(r"mobilit|transport", case=False, regex=True).sum()),
    "recrutement": int(s23.str.contains(r"recrut", case=False, regex=True).sum()),
}
c_att = themes_c23["attractivité"]
p_att = int(rnd(100 * c_att / len(s23), 0))
add("CV3/SYN-C23", "Syndicats : « attractivité » 1er thème ouvert (thèmes d'engagement, texte libre)",
    "43% · 1er thème", f"{p_att}% ({c_att}/{len(s23)}) · comptages thèmes = {themes_c23}",
    p_att == 43 and c_att == max(themes_c23.values()))

# CV4 — connaissance du marché du travail
m, n = mean1(OF, 81)  # Q9.1 connaissance marché
add("CV4/OF-Q9.1", "OF : priorité connaissance du marché /5", "4,0", f"{m} (n={n})", m == 4.0)
means_of_q91 = {i: mean1(OF, i)[0] for i in range(81, 89)}
add("CV4/OF-Q9.1", "Connaissance du marché = priorité n°1 des OF", "n°1",
    f"max des 8 thématiques = {max(means_of_q91.values())} (col 81 = {means_of_q91[81]})",
    means_of_q91[81] == max(means_of_q91.values()))
s = series_txt(OF, 75)  # Q7.2 leviers
n = len(s)
c = int(s.str.contains("Observatoire local", case=False, regex=False).sum())
p = int(rnd(100 * c / n, 0))
add("CV4/OF-Q7.2", "OF : levier observatoire local", "71% · levier n°1", f"{p}% ({c}/{n})", p == 71)
m, n = mean1(ENT, 113)  # Q9.1 connaissance marché
add("CV4/ENT-Q9.1", "Entreprises : priorité connaissance du marché /5", "3,3", f"{m} (n={n})", m == 3.3)
means_ent_q91 = {i: mean1(ENT, i)[0] for i in range(113, 121)}
rang = sorted(means_ent_q91.values(), reverse=True).index(means_ent_q91[113]) + 1
add("CV4/ENT-Q9.1", "Connaissance du marché = 2e priorité des entreprises", "2e",
    f"rang {rang} sur 8", rang == 2)
s = series_txt(SYN, 11)
n = len(s)
c = int(s.str.contains("Partiellement identifiés|Peu formalisés", case=False, regex=True).sum())
p = int(rnd(100 * c / n, 0))
add("CV4/SYN-C11", "Syndicats : besoins « partiellement formalisés » 71% "
    "(= agrégat Partiellement identifiés 57% + Peu formalisés 14%)", 71, f"{p} ({c}/{n})", p == 71)

# ============================================================ ÉCART 1 — adéquation formation
m_of, n = mean1(OF, 55)   # Q4.1 auto-éval couverture
add("E1/OF-Q4.1", "gapBars OF auto-évaluation /5", "4,0", f"{m_of} (n={n})", m_of == 4.0)
m_ent, n = mean1(ENT, 94)
add("E1/ENT-Q7.6", "gapBars Entreprises /5", "3,1", f"{m_ent} (n={n})", m_ent == 3.1)
m_act, n = mean1(ACT, 53)
add("E1/ACT-Q6.1", "gapBars Acteurs de l'emploi /5", "2,3", f"{m_act} (n={n})", m_act == 2.3)
add("E1", "Écart affiché 1,7 pt entre OF et acteurs", "1,7", rnd(m_of - m_act, 1),
    rnd(m_of - m_act, 1) == 1.7)
m, n = mean1(OF, 44)  # Q3.1 connaissance clients
add("E1/OF-Q3.1", "OF : connaissance des besoins des entreprises /5", "3,0", f"{m} (n={n})", m == 3.0)

# ============================================================ ÉCART 2 — nature du déficit
m, n = mean1(ENT, 26)  # Q3.3 pénurie
add("E2/ENT-Q3.3", "Entreprises : pénurie de candidats /5", "4,5", f"{m} (n={n})", m == 4.5)
means_ent_q33 = {i: mean1(ENT, i)[0] for i in range(26, 36)}
add("E2/ENT-Q3.3", "Pénurie = cause n°1 des tensions", "cause n°1",
    f"max des 10 causes = {max(means_ent_q33.values())} (col 26 = {means_ent_q33[26]})",
    means_ent_q33[26] == max(means_ent_q33.values()))
m, n = mean1(ENT, 73)  # Q5.3 manque de candidats
add("E2/ENT-Q5.3", "Entreprises : manque de candidats au recrutement /5", "4,3", f"{m} (n={n})", m == 4.3)
m1, _ = mean1(ENT, 74)  # Q5.3 inadéquation
m2, _ = mean1(ENT, 27)  # Q3.3 inadéquation
add("E2/ENT", "Inadéquation des compétences « reléguée à 2,8-3,1 »", "2,8-3,1",
    f"Q5.3={m1} · Q3.3={m2}", m1 == 2.8 and m2 == 3.1)
m, n = mean1(ACT, 17)  # Q2.2 manque compétences techniques
add("E2/ACT-Q2.2", "Acteurs : manque de compétences techniques /5", "4,3", f"{m} (n={n})", m == 4.3)
means_act_q22 = {i: mean1(ACT, i)[0] for i in range(17, 24)}
add("E2/ACT-Q2.2", "Compétences techniques = facteur n°1 d'inadéquation (cohérence narrative)",
    "implicite n°1", f"max des 7 facteurs = {max(means_act_q22.values())} (col 17 = {means_act_q22[17]})",
    means_act_q22[17] == max(means_act_q22.values()))
m, n = mean1(ACT, 40)  # Q4.1 qualification insuffisante
add("E2/ACT-Q4.1", "Acteurs : niveau de qualification insuffisant /5", "4,3", f"{m} (n={n})", m == 4.3)
p, c, n = pct_regex(SYN, 13, r"lire|écrire|ecrire|compter|calcul|lecture|écriture|"
                              r"\bbase|socle|fondament|français|francais|illettr")
add("E2/SYN-C13", "Syndicats : savoirs de base (lire/écrire/compter) cités — thème publié page Syndicats",
    57, f"{p} ({c}/{n})", p == 57)

# ============================================================ ÉCART 3 — mobilité
p, c, n = pct_contains(SYN, 17, "Mobilité rurale")
add("E3/SYN-C17", "Syndicats : mobilité rurale frein structurant", 86, f"{p} ({c}/{n})", p == 86)
# la conversion « 86% ≈ 4,3/5 » vs la vraie échelle 1-5 posée aux syndicats (col 18)
m_syn18, n = mean1(SYN, 18)
add("E3/SYN-C18", "gapBars Syndicats 4,3/5 (« équivalent » du 86%) vs échelle 1-5 réellement posée "
    "(question mobilité, affichée 3,3/5 sur la page Syndicats)", "4,3",
    f"{m_syn18} (n={n}) sur l'échelle réelle", m_syn18 == 4.3)
m_act36, n = mean1(ACT, 36)  # Q4.1 mobilité
add("E3/ACT-Q4.1", "gapBars Acteurs /5", "3,7", f"{m_act36} (n={n})", m_act36 == 3.7)
m_ent31, n = mean1(ENT, 31)  # Q3.3 transport
add("E3/ENT-Q3.3", "gapBars Entreprises (contrainte transport) /5", "2,5", f"{m_ent31} (n={n})", m_ent31 == 2.5)
add("E3", "Cohérence narrative « verrou n°1 pour les syndicats, au-dessus des acteurs » : "
    "sur les échelles 1-5 réelles, syndicats vs acteurs", "SYN 4,3 > ACT 3,7",
    f"SYN {m_syn18} < ACT {m_act36} (l'ordre s'inverse avec l'échelle réelle)",
    m_syn18 > m_act36)

# ============================================================ ÉCART 4 — transmission / seniors
s = series_txt(SYN, 24)
n = len(s)
c = int((s == "Prioritaire").sum() + (s == "Très prioritaire").sum())
p = int(rnd(100 * c / n, 0))
add("E4/SYN-C24", "Syndicats : transmission-reprise (très) prioritaire", 71, f"{p} ({c}/{n})", p == 71)

# Pyramide : le dashboard (page Entreprises) travaille sur une base « nettoyée »
# excluant les lignes incohérentes (valeurs fractionnaires ou somme pyramide très
# éloignée de l'effectif Q1.4) → 3 031 têtes. On calcule les deux bases.
pyr = ENT.iloc[:, 42:50].apply(pd.to_numeric, errors="coerce")
q14 = pd.to_numeric(ENT.iloc[:, 14], errors="coerce")
aberr = [ix for ix in pyr.index
         if pd.notna(q14.loc[ix]) and q14.loc[ix] > 0
         and (((pyr.loc[ix] % 1) != 0).any()
              or pyr.loc[ix].sum() > 3 * q14.loc[ix]
              or pyr.loc[ix].sum() < q14.loc[ix] / 3)]
def sen_pct(p):
    tot = p.sum().sum()
    sen = p.iloc[:, 4:].sum().sum()
    return rnd(100 * sen / tot, 0), tot
p_clean, tot_clean = sen_pct(pyr[~pyr.index.isin(aberr)])
p_raw, tot_raw = sen_pct(pyr)
add("E4/ENT-Q4.1", "47% de seniors (45 ans et +) — cohérent avec la pyramide de la page "
    "Entreprises (base nettoyée, lignes incohérentes exclues) ; 46% sur base brute", 47,
    f"base nettoyée : {int(p_clean)}% ({tot_clean:.0f} têtes, {len(aberr)} ligne(s) exclue(s)) · "
    f"base brute : {int(p_raw)}% ({tot_raw:.0f} têtes)",
    "OK" if p_clean == 47 else "ECART")

dep5 = pd.to_numeric(ENT.iloc[:, 51], errors="coerce").dropna()
add("E4/ENT-Q4.3", "136 départs retraite à 5 ans (cumul)", 136, f"{dep5.sum():.0f} (n={len(dep5)})",
    dep5.sum() == 136)
p, c, n = pct_regex(ENT, 52, r"production|fabrication")
add("E4/ENT-Q4.4", "Départs « concentrés à 60% sur la production » (base = entreprises répondantes "
    "citant la production, pas % des départs)", 60, f"{p} ({c}/{n})", p == 60)
p, c, n = pct_regex(ENT, 19, r"transmission|cession", base_n=len(series_txt(ENT, 19)))
add("E4/ENT-Q2.1", "Transmission = préoccupation pour 5% seulement", 5, f"{p} ({c}/{n})", p == 5)
m, n = mean1(ENT, 118)  # Q9.1 seniors/transmission
add("E4/ENT-Q9.1", "Priorité GPECT transmission/seniors /5", "2,5", f"{m} (n={n})", m == 2.5)
mins = min(means_ent_q91.values())
exaequo = [i for i, v in means_ent_q91.items() if v == mins]
add("E4/ENT-Q9.1", "« priorité GPECT la plus basse » (2,5)", "la plus basse",
    f"minimum = {mins}, atteint par {len(exaequo)} thématique(s) (cols {exaequo})",
    exaequo == [118])
m, n = mean1(ENT, 66)  # Q4.8 AFEST
add("E4/ENT-Q4.8", "AFEST /5", "1,0", f"{m} (n={n})", m == 1.0)
s = series_txt(ENT, 70)
n = len(s)
c = int(s.str.contains("suffisants", case=False, regex=False).sum())
p = int(rnd(100 * c / n, 0))
add("E4/ENT-Q4.8b", "67% jugent leurs dispositifs « suffisants »", 67, f"{p} ({c}/{n})", p == 67)
s = series_txt(ENT, 53)
n = len(s)
c = int(s.str.contains("Faible et maîtrisé", case=False, regex=False).sum())
p = int(rnd(100 * c / n, 0))
add("E4/ENT-Q4.5", "Turnover faible : 81%", 81, f"{p} ({c}/{n})", p == 81)

# ============================================================ ÉCART 5 — mobilisation collective
s = series_txt(ENT, 112)  # Q8.3
n = len(s)
for lab, needle, exp in [
    ("Campagne commune : 76%", "Campagne de communication commune", 76),
    ("Ateliers RH inter-entreprises : 62%", "Ateliers inter-entreprises sur les bonnes pratiques RH", 62),
    ("Visites coordonnées : 57%", "Visites d'entreprises et journées portes ouvertes", 57),
]:
    c = int(s.str.contains(needle, case=False, regex=False).sum())
    p = int(rnd(100 * c / n, 0))
    add("E5/ENT-Q8.3", lab, exp, f"{p} ({c}/{n})", p == exp)
s = series_txt(ENT, 121)  # Q9.2
n = len(s)
c = int(s.str.contains("ne souhaite pas participer", case=False, regex=False).sum())
p = int(rnd(100 * c / n, 0))
add("E5/ENT-Q9.2", "33% ne souhaitent pas participer aux ateliers", 33, f"{p} ({c}/{n})", p == 33)
s = series_txt(SYN, 20)
n = len(s)
c = int((s == "Faible").sum())
p = int(rnd(100 * c / n, 0))
add("E5/SYN-C20", "Syndicats : engagement des entreprises « faible » 57%", 57, f"{p} ({c}/{n})", p == 57)
s = series_txt(OF, 73)  # Q7.1
n = len(s)
c = int(s.str.contains("Difficulté à mobiliser les entreprises", case=False, regex=False).sum())
p = int(rnd(100 * c / n, 0))
add("E5/OF-Q7.1", "OF : difficulté à mobiliser les entreprises 71%", 71, f"{p} ({c}/{n})", p == 71)
freins_of = {
    "mobiliser entreprises": c,
    "financements": int(s.str.contains("financements", case=False, regex=False).sum()),
    "attractivité métiers": int(s.str.contains("attractivité de certains métiers", case=False, regex=False).sum()),
    "plateaux techniques": int(s.str.contains("plateaux techniques", case=False, regex=False).sum()),
}
add("E5/OF-Q7.1", "Difficulté à mobiliser = frein n°1 des OF", "frein n°1",
    f"comptages = {freins_of}", freins_of["mobiliser entreprises"] == max(freins_of.values()))
p2h, c2h, n2h = pct_regex(SYN, 22, r"2\s*h|deux heures")
padt, cadt, nadt = pct_regex(SYN, 22, r"atelier|court|thème|theme|thémat")
add("E5/SYN-C22", "« ateliers de 2h, thématiques, à résultat concret » (formats cités par les syndicats)",
    "présent (qualitatif)", f"mention « 2h » : {c2h}/{n2h} · ateliers courts/thématiques : {cadt}/{nadt}",
    c2h >= 1 and cadt >= 2)

# ============================================================ MATRICE (chiffres non déjà contrôlés)
p, c, n = pct_regex(OF, 92, r"transports en commun|mobilité|mobilite")
add("MAT/OF-Q10.2", "Matrice : OF mobilité 57%", 57, f"{p} ({c}/{n})", p == 57)
p, c, n = pct_regex(OF, 92, r"Image globale du territoire")
add("MAT/OF-Q10.2", "Matrice : OF image 71%", 71, f"{p} ({c}/{n})", p == 71)
m, n = mean1(OF, 42)  # Q2.2 transmission
add("MAT/OF-Q2.2", "Matrice : OF capacité transmission savoir-faire /5", "3,3", f"{m} (n={n})", m == 3.3)
m, n = mean1(ACT, 86)  # Q8.3 atelier transmission
add("MAT/ACT-Q8.3", "Matrice : acteurs intérêt atelier transmission /5", "4,0", f"{m} (n={n})", m == 4.0)
s = series_txt(ENT, 88)  # Q6.5
n = len(s)
c = int(s.str.contains("Intelligence artificielle", case=False, regex=False).sum())
p = int(rnd(100 * c / n, 0))
add("MAT/ENT-Q6.5", "Matrice : IA à développer 38% (entreprises)", 38, f"{p} ({c}/{n})", p == 38)
m, n = mean1(OF, 35)
add("MAT/OF-Q2.2", "Matrice + R3 : OF capacité IA /5", "2,3", f"{m} (n={n})", m == 2.3)
m, n = mean1(OF, 39)
add("MAT/OF-Q2.2", "Matrice + R3 : OF capacité cybersécurité /5", "1,1", f"{m} (n={n})", m == 1.1)
m, n = mean1(ACT, 58)  # Q6.2 industrie 4.0 / IA
add("MAT/ACT-Q6.2", "Matrice : acteurs manque formation Industrie 4.0/IA /5", "4,1", f"{m} (n={n})", m == 4.1)
p, c, n = pct_regex(SYN, 12, r"\bIA\b|intelligence artificielle|digital|numérique|numerique")
add("MAT/SYN-C12", "Matrice : syndicats IA/digitalisation 14% (compétences techniques, texte libre)",
    14, f"{p} ({c}/{n})", p == 14)
# 'Reconnue (offre solide)' OF ligne tension — contrôle indicatif
m_us, _ = mean1(OF, 23)
m_mn, _ = mean1(OF, 24)
add("MAT/OF-Q2.1", "Matrice : « Reconnue (offre solide) » (qualitatif) — niveaux d'offre usinage/maintenance",
    "qualitatif", f"usinage {m_us}/5 · maintenance {m_mn}/5", m_us >= 3.5 and m_mn >= 3.5)

# ============================================================ RISQUES
s = series_txt(ENT, 22)  # Q2.4
n = len(s)
c = int(s.str.startswith("Oui").sum())
p = int(rnd(100 * c / n, 0))
add("R2/ENT-Q2.4", "71% des entreprises investissent", 71, f"{p} ({c}/{n})", p == 71)
s = series_txt(ENT, 23)  # Q2.5
n = len(s)
c = int(s.str.contains("suffisantes", case=False, regex=False).sum())
p = int(rnd(100 * c / n, 0))
add("R2/ENT-Q2.5", "56% jugent leurs compétences « suffisantes » (base n=16 répondants Q2.5)",
    56, f"{p} ({c}/{n})", p == 56)
s = series_txt(ENT, 19)  # Q2.1
n = len(s)
c = int(s.str.contains("compétitivité", case=False, regex=False).sum())
p = int(rnd(100 * c / n, 0))
add("R4/ENT-Q2.1", "Compétitivité 1ère préoccupation à 67%", 67, f"{p} ({c}/{n})", p == 67)
opts_q21 = {
    "compétitivité": c,
    "Recruter": int(s.str.contains("Recruter des collaborateurs", case=False, regex=False).sum()),
    "Fidéliser": int(s.str.contains("Fidéliser", case=False, regex=False).sum()),
}
add("R4/ENT-Q2.1", "Compétitivité = préoccupation n°1", "n°1",
    f"comptages = {opts_q21}", opts_q21["compétitivité"] == max(opts_q21.values()))
s = series_txt(ENT, 110)
n = len(s)
c = int(s.str.contains("Offre de soins", case=False, regex=False).sum())
p = int(rnd(100 * c / n, 0))
add("R4/ENT-Q8.1", "Désertification médicale 67% (offre de soins insuffisante)", 67, f"{p} ({c}/{n})", p == 67)

# ============================================================ SIGNAUX FAIBLES
std_afest = pd.to_numeric(ENT.iloc[:, 66], errors="coerce").dropna().std(ddof=0)
add("S1/ENT-Q4.8", "AFEST écart-type nul", "0", rnd(std_afest, 1), std_afest == 0)
m, n = mean1(OF, 61)  # Q5.2
add("S1/OF-Q5.2", "Maîtrise AFEST des OF /5", "2,6", f"{m} (n={n})", m == 2.6)

txt_syn_cols = [8, 9, 19, 21, 25, 26, 27, 28, 29]
def syn_mentions(pattern):
    tot = 0
    for i in txt_syn_cols:
        tot += int(series_txt(SYN, i).str.contains(pattern, case=False, regex=True).sum())
    return tot

add("S2/SYN", "Puissance électrique insuffisante / ligne HT (verbatim syndicat) — présence",
    "présent (verbatim)", f"mentions électricité/puissance/HT dans réponses ouvertes SYN : {syn_mentions(r'électri|electri|puissance|haute tension|ligne HT')}",
    syn_mentions(r"électri|electri|puissance|haute tension|ligne HT") >= 1)
add("S4/SYN", "Restauration collective absente (verbatim) — présence",
    "présent (verbatim)", f"mentions cantine/restauration dans réponses ouvertes SYN : {syn_mentions(r'cantine|restauration')}",
    syn_mentions(r"cantine|restauration") >= 1)
n2000 = syn_mentions(r"2\s?000")
top13 = series_txt(ENT, 13)
mask250 = top13.str.contains("250 salariés et plus", case=False, regex=False)
eff = pd.to_numeric(ENT.iloc[:, 14], errors="coerce")
sum_top = eff[mask250.reindex(eff.index, fill_value=False)].sum()
add("S4/SYN+ENT", "« grands employeurs (2 000+ salariés) » : aucun répondant n'atteint 2 000 "
    "(max ~1 550) ; lecture possible = cumul des grands sites",
    "2 000+", f"mention « 2 000 » dans verbatims SYN : {n2000} · cumul effectifs des entreprises "
    f"250+ répondantes ≥ 2 000 : {'oui' if sum_top >= 2000 else 'non'}", "NUANCE")

# ---------------------------------------------------------------- sortie
nb_ok = sum(1 for c in controls if c["verdict"] == "OK")
out = {
    "section": "Page analyse croisée (PAGES_EXTRA.croise)",
    "sources": ["data/01_entreprises.xlsx", "data/02_organismes_formation.xlsx",
                "data/03_acteurs_emploi.xlsx", "data/04_syndicats.xlsx"],
    "conventions": "moyennes 1 décimale half-up ; % entiers half-up ; n = réponses non vides",
    "nb_controles": len(controls),
    "nb_ok": nb_ok,
    "nb_ecarts": sum(1 for c in controls if c["verdict"] == "ECART"),
    "controles": controls,
}
with open(f"{BASE}/resultats/audit_CROISE.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print(f"Contrôles : {len(controls)} · OK : {nb_ok} · ECART : "
      f"{out['nb_ecarts']} · autres : {len(controls) - nb_ok - out['nb_ecarts']}")
for c in controls:
    if c["verdict"] != "OK":
        print(f"[{c['verdict']}] {c['q']} — {c['label']}\n    dashboard={c['dashboard']} | calcule={c['calcule']}")
