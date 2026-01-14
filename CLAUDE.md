# AGP Strategy Suite - Instructions Claude Code

## Vue d'ensemble

Application sim racing professionnelle pour rFactor 2 combinant:
- Telemetrie temps reel (shared memory 60Hz)
- Analyse de setup avec recommandations
- Strategie endurance 24h
- Live timing multi-sources
- Plugin SimHub natif

## Architecture

```
Python Backend (packages/core) <--WebSocket--> Tauri Frontend (apps/desktop)
                                                      |
                                                SimHub Plugin (apps/simhub-plugin)
```

## Structure

- `packages/core/agp_core/telemetry/` - Lecteur shared memory rF2
- `packages/core/agp_core/analysis/` - Analyseur de setup
- `packages/core/agp_core/server/` - Serveur WebSocket
- `apps/desktop/src/` - React frontend
- `apps/desktop/src-tauri/` - Rust backend Tauri

## Commandes

```bash
# Backend Python
cd packages/core
python main.py

# Frontend Tauri
cd apps/desktop
npm run tauri:dev

# Build
npm run tauri:build
```

## Standards

- Python: Ruff, Python 3.11+
- TypeScript: Strict mode
- React: Functional components, Zustand
- Styling: TailwindCSS

## Regles

1. TOUJOURS terminer la tache en cours
2. JAMAIS refactorer sans demande
3. Tester avec rF2 avant de valider
4. Repondre en francais
