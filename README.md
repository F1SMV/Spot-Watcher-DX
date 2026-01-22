📡 Radio Spot Watcher DX — v5.6

DX Cluster Dashboard & Advanced Radio Analysis Engine

Application web locale de surveillance DX et d’analyse radio destinée aux radioamateurs exigeants.
Conçue pour observer, comprendre et prendre du recul, pas pour faire du bruit visuel.

🧭 Présentation générale

Radio Spot Watcher DX est une application web locale qui :

se connecte à un ou plusieurs DX Clusters (Telnet)

affiche les spots en temps réel (HF / VHF / UHF)

intègre les indices solaires (SFI, A, Kp…)

conserve une mémoire exploitable de l’activité

propose plusieurs niveaux d’analyse, du live à la lecture stratégique

L’objectif n’est pas de voir beaucoup, mais de voir juste.

🖥️ Pages principales
1️⃣ Page Index — Temps réel & suivi opérateur

C’est la page d’observation immédiate.

Elle affiche :

le flux de spots en direct

les bandes actives

les DX recherchés / wanted

les indices solaires

les signaux de “surge” d’activité

👉 Objectif : savoir ce qui se passe maintenant.

📸 Aperçu

![Apercu du Dashboard](apercu.png)

📡 Pavé Tracking Watchlist (nouveauté v5.6)

Le pavé WATCHLIST · TRACKING répond à un besoin concret :

“Je n’étais pas devant l’écran : qu’est-ce que j’ai raté sur mes indicatifs surveillés ?”

Fonctionnement

basé sur la watchlist

exploite un historique en mémoire des spots reçus

affiche les 5 ou 10 derniers spots par indicatif

Caractéristiques

filtre dynamique par call (ex: 9, VK, /P)

mise à jour automatique

affichage clair :

heure UTC

bande

mode

fréquence

Philosophie

❌ pas un log brut

❌ pas un dump massif

✅ un outil de rattrapage d’activité

✅ pensé pour l’opérateur humain

Quand le filtre est vide, le pavé reste volontairement neutre.

2️⃣ Page Map — Carte d’observation

Carte classique des spots en cours :

visualisation géographique

représentation immédiate de l’activité

complément naturel de la liste temps réel

👉 Objectif : voir où ça se passe.

3️⃣ Page Analyse — META ANALYSE différée

La META ANALYSE est un outil volontairement non temps réel.

Elle s’appuie sur l’analyse du fichier applicatif :

radio_spot_watcher.log

Principe

Un script dédié :

parcourt le log

nettoie doublons et artefacts

agrège les données sur une période

génère des fichiers structurés (data/meta/*.json)

Ces données sont ensuite affichées dans la page Analyse.

Ce que fait la META ANALYSE

lecture macro de l’activité

top DX sur la période

validation ou infirmation d’un ressenti opérateur

Ce qu’elle ne fait pas

❌ pas de prédiction

❌ pas d’alerte live

❌ pas d’automatisme aveugle

👉 C’est un outil de recul, pas un gadget.

4️⃣ Page World — Forecast & Anomalies (nouveauté majeure)

La World Forecast Map est un outil d’analyse avancée, distinct de la carte classique.

Principe fondamental

Comparer :

ce qui est attendu (modèle de propagation)

ce qui est observé (spots réels)

👉 pour ne montrer que ce qui sort du modèle.

Ce que montre la page World

🌍 une carte mondiale

🔥 des zones rouges (heatmap) représentant des clusters anormaux

📍 des calls affichés directement sur la carte

🧠 une lecture immédiate de phénomènes inhabituels

Aucun spot isolé n’est affiché.

Définition d’une anomalie

Un cluster est considéré comme anormal selon :

la bande

l’heure UTC

la distance

le mode (FT8 pondéré différemment)

la cohérence temporelle

les indices solaires

Un Surprise Score est calculé.
Seuls les clusters dépassant un seuil sont affichés.

Philosophie de la page World

❌ pas de magie

❌ pas de prédiction automatique

❌ pas de bruit visuel

✅ ce qui s’affiche mérite ton attention

La page World est un outil de lecture stratégique, pas un écran de monitoring.

⚙️ Architecture technique

Backend : Python / Flask

Frontend : HTML / CSS / JavaScript (local)

Cluster : Telnet DX Cluster

Logs : fichier applicatif unique

Analyse : scripts Python dédiés

Stockage : mémoire + JSON locaux

Aucune dépendance cloud.
Conçu pour Raspberry Pi ou machine locale.

🎨 Organisation du CSS

Le projet distingue volontairement :

base.css → thèmes, couleurs, variables globales

CSS inline par page → layout critique et lisibilité

⚠️ Certains styles inline écrasent le thème :
c’est un choix assumé pour la lisibilité opérationnelle.

🔐 Sécurité & philosophie

application locale / LAN

aucune exposition publique par défaut

aucune télémétrie

aucune dépendance externe critique

L’opérateur reste maître de ses données.

🗂️ Historique des versions (extrait)
v5.6 (actuelle)

Page World : Forecast & Anomalies

Détection de clusters anormaux

Heatmap analytique

Affichage des calls sur la carte

Pavé Tracking Watchlist

Stabilisation générale frontend/backend

entre la 5.2 et la 5.6 plusieurs versions de travail non publiées

v5.2

Introduction de la META ANALYSE

Analyse différée du log

Séparation claire temps réel / analyse

📌 Positionnement du projet

Radio Spot Watcher DX n’est pas :

un simple viewer DX

un gadget graphique

un outil prédictif automatique

C’est un outil d’observation radio raisonné,
conçu pour ceux qui veulent comprendre ce qu’ils voient.

👤 Auteur

Développé par F1SMV – Eric
avec l’assistance de ChatGPT5.2 et Gimini
au service de la communauté radioamateur.

vous pouvez me contacter via mon fil X


