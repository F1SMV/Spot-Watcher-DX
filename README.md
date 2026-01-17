DX Cluster Dashboard – v5.2

Neural Analysis Edition

Dashboard web temps réel pour radioamateurs, orienté décision, veille DX et analyse d’activité observée, connecté à un DX Cluster via Telnet.

📡 Radio Spot Watcher DX

DX Cluster Dashboard & Meta Analysis Engine

Application locale de surveillance DX et d’analyse différée destinée aux radioamateurs exigeants.
Pensée pour la lecture stratégique, la fiabilité et le recul analytique, pas pour l’effet vitrine.

🧭 Présentation générale

Radio Spot Watcher DX est une application web locale qui :

se connecte à des DX Clusters (Telnet)

affiche les spots en temps réel (HF / VHF / UHF)

intègre les indices solaires (SFI, A, Kp…)

conserve un historique exploitable

propose une META ANALYSE différée du log

L’objectif n’est pas de “voir beaucoup”, mais de voir juste.

🖥️ Capture d’écran

📷 Interface principale & page Analyse

📸 Aperçu

![Apercu du Dashboard](apercu.png)

🧱 Architecture fonctionnelle
1. Temps réel — page principale

Connexion DX Cluster (ex: dxfun.com)

Réception et parsing des spots

Calcul du SPD (distance, rareté, bande…)

Mise à jour continue de l’interface

Visualisation instantanée de l’activité radio

👉 Objectif : observer ce qui se passe maintenant.

2. Analyse différée — page Analyse

C’est ici qu’intervient le pavé META ANALYSE.

🧠 META ANALYSE — Page Analyse
Rôle

La META ANALYSE est un outil de lecture macro, basé sur l’analyse du log applicatif
radio_spot_watcher.log.

Elle répond à une question simple :

Qu’est-ce qui s’est réellement passé sur la durée, au-delà du flux temps réel ?

Ce que fait la META ANALYSE

Un script dédié (log_meta_analyzer.py) :

parcourt le log applicatif

extrait uniquement les spots valides

nettoie les doublons et artefacts

agrège les données sur une période donnée

génère des fichiers structurés (data/meta/*.json)

Ces fichiers sont ensuite consommés par l’interface.

Informations affichées

Le pavé META ANALYSE affiche :

nombre total de spots analysés

plage temporelle couverte

date de génération

Top DX (SPD) sur la période

compteur “Relance possible”

Fonctionnement volontairement manuel

La META ANALYSE fonctionne en mode manuel journalier :

❌ pas de cron automatique

❌ pas de recalcul permanent

✅ une analyse déclenchée à la demande

✅ maximum 1 fois toutes les 24 heures

Le bouton ↻ RUN :

relance l’analyse

régénère les statistiques

réinitialise le compteur journalier

👉 Ce choix est délibéré : on évite le bruit et l’analyse à chaud.

Ce que la META ANALYSE ne fait pas

❌ pas de prédiction de propagation

❌ pas de recommandation automatique

❌ pas d’aide à la décision temps réel

Elle documente le passé récent, rien de plus.

🧩 Pourquoi la META ANALYSE est dans la page Analyse

Elle n’apparaît pas sur la page principale car :

elle n’est pas temps réel

elle nécessite du recul

elle complète l’observation instantanée

👉 C’est un outil d’aide à la décision différée, pas un widget live.

⚙️ Composants techniques

Backend : Python / Flask

Frontend : HTML / CSS / JavaScript (local)

Cluster : Telnet DX Cluster

Logs : fichier applicatif unique

Analyse : script Python indépendant

Stockage : JSON / CSV locaux

Aucune dépendance cloud.
Conçu pour Raspberry Pi ou machine locale.

🎨 Organisation du CSS (important)

Le projet distingue volontairement :

base.css → thèmes, couleurs, variables globales

CSS inline par page → layout spécifique et prioritaire

⚠️ Les styles inline écrasent base.css sur certaines pages
(c’est un choix assumé pour garantir la lisibilité critique).

🔐 Sécurité & philosophie

application locale / LAN

aucune exposition publique par défaut

déclenchements volontaires

données maîtrisées par l’opérateur

Pas de télémétrie. Pas de cloud. Pas de dépendance externe critique.

🔄 Schéma de flux logique
DX Cluster (Telnet)
        ↓
 TelnetWorker
        ↓
 radio_spot_watcher.log
        ↓
 log_meta_analyzer.py
        ↓
 data/meta/*.json
        ↓
 Page Analyse (META ANALYSE)

🧑‍✈️ Guide opérateur (lecture recommandée)

La page principale sert à observer

La page Analyse sert à comprendre

La META ANALYSE sert à confirmer ou infirmer un ressenti

Le SPD n’est pas un score absolu, mais un indicateur comparatif

🧪 Guide développeur (repères clés)

ne pas automatiser la META ANALYSE sans réflexion

ne pas mélanger temps réel et analyse différée

conserver le log comme source de vérité

toute décision doit pouvoir être expliquée par les données

🗂️ Historique des versions
v4.x

interface très lisible

séparation visuelle forte des pavés

base fonctionnelle stable

v5.0

refonte structurelle du frontend

introduction des workers (Solar, Telnet, History…)

v5.1

stabilisation des flux

amélioration du SPD

nettoyage des routes Flask

v5.2 (actuelle)

introduction de la META ANALYSE

analyse différée du log

bouton manuel journalier

séparation claire temps réel / analyse

page Analyse dédiée

📌 Positionnement du projet

Radio Spot Watcher DX n’est pas :

un simple viewer de cluster

un gadget graphique

un outil prédictif

C’est un outil d’observation radio raisonné,
conçu pour ceux qui veulent comprendre ce qu’ils voient.


👤 Auteur

Développé par F1SMV Eric
avec l’assistance de ChatGPT (v5.2) et #gimini3 #vibecoding pour la structuration et l’analyse,
au service de la communauté radioamateur.

vous pouvez me contacter via mon fil X
