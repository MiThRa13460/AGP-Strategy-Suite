# Changelog

Toutes les modifications notables de ce projet sont documentees dans ce fichier.

Le format est base sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [Unreleased]

### En cours
- Ameliorations performances backend Python
- Support iRacing (experimental)

---

## [1.0.0] - 2024-01-15

### Premiere version stable

La version 1.0.0 marque la premiere release stable de AGP Strategy Suite!

### Nouveautes

#### Telemetrie Temps Reel
- Lecture shared memory rFactor 2 a 60Hz
- Affichage temperatures pneus avec code couleur intelligent
- Pressions pneus en temps reel
- Usure et grip des pneumatiques
- Temperatures freins avec alertes
- Traces G-Force laterales et longitudinales

#### Analyse de Setup
- Parser de fichiers .svm rFactor 2
- Diagnostics automatiques (suspension, aerodynamique, pneus)
- Moteur de recommandations intelligentes
- Comparaison de setups cote a cote

#### Analyse CSV Avancee
- Support multi-format: MoTeC, rF2, ACC, generique
- Detection automatique des virages via steering et G lateral
- Analyse sous-virage/survirage par virage
- Correlation setup/performance multi-sessions
- Recommandations data-driven avec scores de confiance

#### Module Strategie Endurance
- Calcul tours restants (carburant et pneus)
- Fenetre pit optimale automatique
- Prediction degradation pneumatiques
- Gestion rotation pilotes pour 24h
- Timeline strategique interactive

#### Live Timing
- Support multi-sources (Shared Memory, SMS, HTTP API)
- Classements temps reel avec filtrage par classe
- Analyse des ecarts
- Detection niveau de menace adversaires
- Profils concurrents

#### Systeme Overlay
- Fenetres transparentes click-through
- 3 presets: Course, Qualifications, Minimal
- Position et taille personnalisables
- Hotkeys configurables (F1-F4)

#### Plugin SimHub
- Plus de 50 proprietes exposees
- Integration native dashboards SimHub
- Compatible formules NCalc
- Auto-reconnexion WebSocket

### Technique
- Backend Python optimise (<5% CPU)
- Frontend Tauri leger (~150MB RAM)
- WebSocket temps reel
- Auto-updater integre

---

## [0.9.0] - 2024-01-01

### Beta Release

Version beta pour tests internes.

### Ajoute
- Structure de base du projet
- Backend Python avec serveur WebSocket
- Frontend Tauri + React
- Dashboard telemetrie basique
- Premiere version du parser SVM

### Connu
- Performance a optimiser sur longues sessions
- Quelques fuites memoire dans l'analyseur CSV

---

## [0.1.0] - 2023-12-15

### Alpha Release

Premiere version alpha pour validation du concept.

### Ajoute
- Proof of concept lecteur shared memory
- Interface React basique
- Communication WebSocket fonctionnelle

---

## Types de changements

- **Ajoute** pour les nouvelles fonctionnalites
- **Modifie** pour les changements aux fonctionnalites existantes
- **Deprecie** pour les fonctionnalites qui seront supprimees prochainement
- **Supprime** pour les fonctionnalites supprimees
- **Corrige** pour les corrections de bugs
- **Securite** pour les vulnerabilites corrigees
