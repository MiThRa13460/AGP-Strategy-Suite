# AGP Strategy Suite - Guide Utilisateur

## Introduction

AGP Strategy Suite est une application professionnelle de sim racing pour rFactor 2, combinant:
- Telemetrie temps reel (60Hz)
- Analyse de setup avec recommandations
- Strategie endurance pour courses 24h
- Live timing multi-sources
- Overlays transparents in-game
- Integration SimHub native

## Installation

### Installation Standard

1. Telecharger `AGPStrategySuite-x.x.x-Setup.exe`
2. Executer l'installeur
3. Choisir les composants:
   - **AGP Strategy Suite** (requis)
   - **Plugin SimHub** (optionnel)
   - Raccourcis Bureau/Menu Demarrer

### Installation Manuelle

```
AGP-Strategy-Suite/
├── AGPStrategySuite.exe    → Application principale
├── backend/                 → Backend Python (lance automatiquement)
└── resources/              → Ressources
```

## Demarrage Rapide

### 1. Lancer l'application

Double-cliquer sur **AGP Strategy Suite**. Le backend Python demarre automatiquement.

### 2. Connecter rFactor 2

1. Lancer rFactor 2
2. L'application detecte automatiquement le jeu
3. Le status passe a "Connected" (vert)

### 3. Dashboard Telemetrie

L'onglet **Dashboard** affiche en temps reel:
- Vitesse, RPM, rapport de boite
- Temperatures pneus (code couleur)
- Pressions pneus
- Usure et grip
- Temperatures freins
- Forces G laterales/longitudinales

## Modules

### Dashboard

Vue d'ensemble de la telemetrie en temps reel.

**Indicateurs:**
- **Vert**: Valeur optimale
- **Jaune**: Attention requise
- **Rouge**: Probleme critique

### Setup Analysis

Analyse de vos fichiers setup (.svm) avec recommandations.

**Fonctionnalites:**
- Import de fichiers .svm
- Diagnostic automatique
- Comparaison de setups
- Recommandations data-driven

### CSV Analysis

Analyse approfondie des fichiers telemetrie.

**Formats supportes:**
- MoTeC (.csv)
- rFactor 2 export
- ACC export
- Format generique

**Analyse:**
- Detection automatique des virages
- Sous-virage/survirage par virage
- Correlation setup/performance
- Recommandations basees sur les donnees

### Strategy

Module strategie pour courses d'endurance.

**Calculs:**
- Tours restants (carburant)
- Fenetre pit optimale
- Prediction degradation pneus
- Gestion rotation pilotes

### Live Timing

Classements en temps reel multi-sources.

**Sources:**
- rF2 Shared Memory
- SimHub SMS Protocol
- rF2 HTTP API

**Indicateurs:**
- Position et ecarts
- Niveau de menace adversaires
- Analyse du rythme

### Overlays

Fenetres transparentes par-dessus rFactor 2.

**Presets:**
- **Course**: Timing + Strategy compact
- **Qualifications**: Telemetrie + Ecarts secteur
- **Minimal**: Position + Carburant uniquement

**Configuration:**
- Position par drag & drop
- Taille ajustable
- Opacite configurable
- Click-through (ne bloque pas les clics)

## Raccourcis Clavier

| Touche | Action |
|--------|--------|
| `F1` | Toggle overlay telemetrie |
| `F2` | Toggle overlay strategy |
| `F3` | Toggle overlay standings |
| `F4` | Toggle tous les overlays |
| `Ctrl+R` | Reconnecter au backend |

## Configuration

### Parametres Backend

```
Host: localhost (par defaut)
Port: 8765 (par defaut)
```

### Parametres Overlay

- **Position**: Cliquer-glisser pour deplacer
- **Taille**: Molette souris sur les bords
- **Opacite**: Slider dans les options

## Depannage

### L'application ne se connecte pas a rF2

1. Verifier que rF2 est en cours d'execution
2. Verifier que le plugin Shared Memory est actif dans rF2
3. Redemarrer l'application

### Les overlays ne s'affichent pas

1. Verifier que rF2 est en mode fenetre ou borderless
2. Desactiver l'antivirus temporairement
3. Executer en tant qu'administrateur

### Donnees incorrectes

1. Verifier la version de rF2
2. Mettre a jour AGP Strategy Suite
3. Reinitialiser les parametres

## Support

- GitHub Issues: [Signaler un bug](https://github.com/agp/agp-strategy-suite/issues)
- Documentation: Ce guide
