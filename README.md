# AGP Strategy Suite

Application professionnelle de sim racing pour rFactor 2 combinant telemetrie temps reel, analyse de setup, strategie endurance et live timing.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

## Fonctionnalites

### Telemetrie Temps Reel
- Donnees live a 60Hz via shared memory rF2
- Temperatures et pressions pneus avec code couleur
- Usure et grip en temps reel
- Temperatures freins
- Forces G laterales/longitudinales

### Analyse de Setup
- Import fichiers .svm rFactor 2
- Diagnostics automatiques (suspension, aero, pneus)
- Recommandations intelligentes
- Comparaison de setups

### Analyse CSV Avancee
- Support multi-format (MoTeC, rF2, ACC)
- Detection automatique des virages
- Analyse sous-virage/survirage par virage
- Correlation setup/performance
- Recommandations data-driven avec scores de confiance

### Strategie Endurance
- Calcul tours restants (carburant/pneus)
- Fenetre pit optimale
- Prediction degradation
- Gestion rotation pilotes
- Timeline strategique interactive

### Live Timing
- Classements multi-sources
- Analyse des ecarts
- Niveau de menace adversaires
- Profils concurrents

### Overlays
- Fenetres transparentes click-through
- Presets configurables (Course, Qualifications, Minimal)
- Position/taille personnalisables

### Plugin SimHub
- 50+ proprietes exposees
- Integration native dashboards SimHub
- Formules NCalc compatibles

## Installation

### Via Installeur (Recommande)

Telecharger `AGPStrategySuite-1.0.0-Setup.exe` depuis [Releases](https://github.com/agp/agp-strategy-suite/releases).

### Build Manuel

```bash
# Cloner le repo
git clone https://github.com/agp/agp-strategy-suite.git
cd agp-strategy-suite

# Builder tout
cd installer
.\build.ps1 -Release
```

## Structure du Projet

```
AGP-Strategy-Suite/
├── apps/
│   ├── desktop/              # Application Tauri + React
│   │   ├── src/              # Composants React
│   │   └── src-tauri/        # Backend Rust
│   └── simhub-plugin/        # Plugin SimHub C#
├── packages/
│   └── core/                 # Backend Python
│       └── agp_core/
│           ├── telemetry/    # Lecteur shared memory
│           ├── analysis/     # Strategie & fuel
│           ├── setup/        # Parser SVM & CSV analysis
│           ├── live_timing/  # Connecteurs multi-sources
│           └── server/       # WebSocket server
├── installer/                # Scripts NSIS & build
└── docs/                     # Documentation
```

## Developpement

### Prerequis

- Python 3.11+
- Node.js 20+ & pnpm
- Rust & Cargo
- .NET SDK 4.8 (pour SimHub plugin)
- rFactor 2

### Backend Python

```bash
cd packages/core
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Frontend Tauri

```bash
cd apps/desktop
pnpm install
pnpm tauri:dev
```

### Plugin SimHub

```bash
cd apps/simhub-plugin
$env:SIMHUB_PATH = "C:\Program Files (x86)\SimHub"
dotnet build AGPStrategy/AGPStrategy.csproj -c Release
```

## Documentation

- [Guide Utilisateur](docs/user-guide.md)
- [Integration SimHub](docs/simhub-integration.md)

## Proprietes SimHub

Le plugin expose les proprietes suivantes (prefixe `AGP.`):

| Categorie | Proprietes |
|-----------|------------|
| Pneus | `TireTemp_FL/FR/RL/RR`, `TirePressure_*`, `TireWear_*`, `TireGrip_*` |
| Freins | `BrakeTemp_FL/FR/RL/RR` |
| Analyse | `Understeer_Pct`, `Oversteer_Pct`, `BalanceScore`, `CornerPhase` |
| Strategie | `FuelLapsRemaining`, `OptimalPitLap`, `InPitWindow`, `IsCritical` |
| Timing | `Position`, `GapAhead`, `ThreatLevel`, `NearestThreatName` |
| Calcules | `BalanceIndicator`, `TireCondition`, `FuelUrgency` |

## Performance

| Composant | CPU | RAM |
|-----------|-----|-----|
| Backend Python | <5% | <100MB |
| App Tauri | <3% | <150MB |
| Overlays | <2% | <50MB |
| Plugin SimHub | <1% | <30MB |
| **Total** | **<11%** | **<330MB** |

## License

MIT License - voir [LICENSE](LICENSE)

## Auteur

AGP - Sim Racing Tools
