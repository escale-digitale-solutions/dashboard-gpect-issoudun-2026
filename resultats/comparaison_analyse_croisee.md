# Comparaison : analyse croisée du dashboard vs analyse indépendante

*Confrontation de la page « Analyse croisée » du dashboard (v12) avec
l'analyse reconstruite depuis les seules données
(`resultats/analyse_croisee_independante.md`). Chaque point est sourcé par
les contrôles de `resultats/audit_*.json` (810 chiffres recalculés, doubles
contre-expertises sur chaque écart).*

## 1. Erreurs à corriger (contredites par les données)

1. **Écart 3 — mobilité, barre « Syndicats 4,3/5 » : FAUX → 3,3/5.**
   Le 4,3 est une conversion inventée du « 86 % » (choix multiple Q17) en
   note /5. Or l'échelle 1-5 existe réellement dans le questionnaire
   syndicats (« la mobilité vous semble-t-elle un frein majeur ? ») :
   moyenne **3,3/5** (n=7 ; distribution 2·3·3·3·3·4·5). Conséquences :
   les syndicats passent SOUS les acteurs de l'emploi (3,7), et l'écart
   avec les entreprises (2,5) est de 0,8 point, pas de 1,8. Le message
   qualitatif (« verrou pour les uns, secondaire pour les autres ») reste
   vrai mais doit être calibré. La note sous le graphique (« équivalent
   ≈4,3/5 ») disparaît ; on peut garder le 86 % en complément à côté du 3,3.
2. **Écart 4 & Risque 1 — « départs concentrés à 60 % sur la production » :
   formulation fausse.** 60 % = part des **entreprises répondantes** qui
   citent la production (12/20, Q4.4), pas la part des 136 départs.
   Reformuler : « la production est citée par 60 % des entreprises comme
   premier service touché ».
3. **Signal faible « Restauration collective » — « grands employeurs
   (2 000+ salariés) » : impossible.** Aucun répondant ne dépasse 1 550
   salariés (max Q1.4). Écrire « les plus grands employeurs du bassin »
   sans seuil chiffré.
4. **Matrice, ligne Transmission (si reprise ailleurs) — rappel des erreurs
   corrigées côté pages collèges** : SYN Q08 foncier 43 % → **57 %** ;
   SYN Q09 désertification médicale 29 % → **14 %** ; ENT Q3.3 image
   3,1 → **3,2** ; ENT Q4.4 conduite 20 % → **25 %** ; ENT Q3.1 bureau
   d'études 29 % → **33 %** ; ACT Q1.2 seniors public et Q6.1 offre publique
   2,2 → **2,3** (arrondi half-up).

## 2. Points exacts mais à clarifier (bases et libellés)

1. **Convergence 3 — « disposition des acteurs à 4,7/5 »** : c'est la note
   du seul item « campagne de communication commune » (Q8.3), pas une
   disposition générale. Préciser l'item.
2. **Convergence 4 — « besoins partiellement formalisés pour 71 % des
   syndicats »** : agrégation de « partiellement identifiés » (57 %) +
   « peu formalisés » (14 %) sous un libellé unique. Soit détailler, soit
   écrire « partiellement ou peu formalisés ».
3. **Risque 2 — « 71 % investissent mais 56 % jugent leurs compétences
   suffisantes »** : bases différentes non dites (71 % sur n=21 ; 56 % sur
   n=16 investisseurs). Ajouter les n=.
4. **Écart 4 — « priorité GPECT la plus basse (2,5/5) »** : ex æquo en bas
   de classement non signalé (« développement de l'offre de formation
   locale » est à 2,6, quasi identique). Écrire « parmi les plus basses ».
5. **« 47 % de seniors »** : repose sur la base nettoyée (3 031 têtes, lignes
   incohérentes exclues) ; la base brute donne 46 %. Garder 47 % mais
   documenter le nettoyage dans la note méthodologique (l'écart avec/sans
   plus gros employeur est déjà bien traité).
6. **Convergence 4 — « attractivité 1er thème ouvert des syndicats »** :
   non reproductible tel quel dans Q26-Q29 ; s'appuyer plutôt sur les
   chiffres vérifiés (orientation/image 29 % Q09, thèmes Q23).
7. **Écart 1 — « les OF ne connaissent leurs clients qu'à 3,0/5 »** : exact,
   mais préciser n=7 comme partout.

## 3. Manques — ce que l'analyse indépendante ajoute et qui intéresse les financeurs

1. **Le chiffrage « avec/sans plus gros employeur » des 136 départs** :
   75 des 136 départs (55 %) viennent d'un seul établissement. Pour un
   financeur, le risque « diffus » (61 départs répartis dans le tissu PME)
   et le risque « concentré » ne s'adressent pas avec les mêmes dispositifs.
2. **L'asymétrie dispositifs** (§8 de l'analyse indépendante) : AFEST 1,0/5
   et France Travail 2,1/5 côté entreprises vs formation qualifiante 4,3/5,
   PMSMP 3,6 côté prescripteurs. Le dashboard en montre les morceaux mais
   ne nomme pas le levier « appropriation de l'existant, coût quasi nul » —
   argument très favorable en comité de financement.
3. **La nuance sur la mobilité syndicale** (médiane 3, un seul 5/7) : évite
   au financeur de surdimensionner un dispositif mobilité sur la foi du 86 %.
4. **L'intérim comme canal de diffusion** : 71 % de recours régulier + 5,0/5
   unanime des agences sur la relation entreprises — canal opérationnel
   concret pour toucher les entreprises, absent de la page croisée.
5. **Le foncier à 57 % comme atout n°1 des syndicats** (après correction) :
   argument positif prêt à l'emploi pour la communication territoriale.
6. **La lecture critique de l'auto-sélection** : les répondants sont
   plausiblement les plus sensibilisés → l'angle mort transmission est
   probablement pire dans le tissu réel. Une ligne dans « Limites & biais »
   renforcerait la crédibilité méthodologique du diagnostic.

## 4. Verdict d'ensemble

La page « Analyse croisée » du dashboard est **structurellement juste** :
les 4 convergences et les écarts 1, 2, 4, 5 sont confirmés par le recalcul
indépendant, et la lecture « écarts de perception = cœur de la GPECT » est
exactement celle qui ressort des données. Les corrections nécessaires sont
ciblées : **une erreur matérielle (mobilité syndicats 4,3 → 3,3)**, une
formulation fausse (60 % des départs), un signal faible à réécrire (2 000+
salariés), et une série de précisions de bases (n=, libellés regroupés).
Les enrichissements proposés (§3) sont optionnels mais à fort rendement
pour un public financeur.
