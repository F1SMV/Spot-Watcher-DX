📡 DX Cluster Dashboard – v5.0

Neural Analysis Edition

Dashboard web temps réel pour radioamateurs, orienté décision, veille DX et analyse d’activité observée, connecté à un DX Cluster via Telnet.

Cette version 5.0 marque un changement de philosophie :
👉 on ne “regarde plus des spots”, on interprète une activité radio réelle.
🚀 Quoi de neuf dans la v5.0 ?
🗺️ Nouvelle page map.html — Lecture avancée de l’activité DX

La page Map n’est plus une simple carte de points.
Elle propose trois modes d’analyse complémentaires, activables à la demande.
🔹 Mode Points (référence)

Affichage classique des spots :

    Un point = un spot réel

    Couleur = bande

    Taille = score SPD

    Popup détaillé (indicatif, mode, distance, score)

📌 Usage : inspection précise, clic par clic.
🔥 Mode A — Heatmap par bande (activité observée)

La Heatmap représente où de l’activité radio a été observée récemment sur une bande donnée.

Principe exact :

    Chaque spot récent devient une source d’intensité

    L’intensité est proportionnelle au score SPD

    Les zones colorées indiquent une concentration d’activité réelle

⚠️ Important :

    La heatmap est volontairement limitée à une seule bande

    Elle ne représente pas la propagation ionosphérique

    Elle ne trace aucun trajet radio

    Heatmap = activité observée, pas prédiction.

📌 Usage recommandé :

    Analyser une bande précise (ex : 20m)

    Identifier rapidement où l’activité se concentre

    Fenêtre courte (5–15 min) = ouverture en cours

🟠 Mode C — Cercles d’activité (lecture faible densité)

Le mode Cercles est conçu pour les situations réalistes :

    Peu de spots

    Trafic CW / SSB

    Activité DX diffuse

Principe :

    Chaque spot dessine une zone circulaire semi-transparente

    Rayon basé sur une heuristique simple (distance / lisibilité)

    Couleur = bande

Ce mode remplit visuellement la carte sans mentir sur la densité.

📌 Usage recommandé :

    Quand la heatmap est trop pauvre

    Pour visualiser des zones probables d’activité

    Lecture “radio-terrain”, pas statistique

🧠 Lecture assistée intégrée

La colonne gauche de la page Map explique en temps réel :

    ce que montre le mode actif

    quand l’utiliser

    quand en changer

Objectif : aucune ambiguïté d’interprétation.
✍️ Spot manuel intégré (hérité du Dashboard)

La page Map intègre désormais le pavé “Spot manuel” :

    Envoi direct de commandes DX au cluster

    Pré-remplissage depuis le dernier spot cliqué sur la carte

    Retour d’état clair (OK / erreur / cluster non connecté)

👉 Continuité fonctionnelle totale avec la page principale.
🧠 Philosophie v5.0

La v5.0 ne prétend pas prédire la propagation.
Elle se concentre sur ce qui est observable, mesurable et exploitable immédiatement :

    Activité réelle

    Densité de trafic

    Zones DX actives

    Priorisation par score SPD

La carte devient un outil d’analyse, pas une illustration.
📸 Aperçu

![Apercu du Dashboard](apercu.png)


🛠️ Fonctionnalités héritées (v4.8 et antérieures)

(contenu inchangé, conservé pour l’historique)
🚀 Quoi de neuf dans la 4.8 ?

    Horodatage des spots dans la page Analyse

    Pavé “détecteur d’anomalies” avec RAZ périodique

🚀 Quoi de neuf dans la v4.7 ?

(… contenu original intégral conservé …)

    🧠 Moteur de Score SPD
    🗺️ AI Path Optimizer & Grayline
    📊 Statistiques DXCC
    🌠 Meteor Scatter
    ☀️ Données solaires NOAA
    🗣️ Synthèse vocale
    📊 Interface modulaire
    🧠 Architecture technique
    🔗 Connectivité cluster
    📡 Routes API

🧩 Évolutions envisagées (post-v5.0)

    Page /now : recommandations opérationnelles immédiates

    Détection automatique d’ouvertures (événements, pas graphiques)

    IA explicative : “Pourquoi cette bande maintenant ?”

    Corrélation activité ↔ données solaires (sans sur-interprétation)

👤 Auteur

Développé par F1SMV Eric
avec l’assistance de ChatGPT (v5.2) et #gimini3 pour la structuration et l’analyse,
au service de la communauté radioamateur.

vous pouvez me contacter via mon fil X

73’s & bon DX