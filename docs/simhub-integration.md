# AGP Strategy Suite - Integration SimHub

## Vue d'ensemble

Le plugin SimHub expose toutes les donnees AGP Strategy Suite sous forme de proprietes SimHub standard. Vous pouvez les utiliser dans vos dashboards, overlays et scripts NCalc.

## Installation

### Via l'installeur

Cocher **"SimHub Plugin"** lors de l'installation.

### Manuelle

1. Copier `AGPStrategyPlugin.dll` dans `SimHub/Plugins/`
2. Copier les dependances:
   - `Newtonsoft.Json.dll`
   - `websocket-sharp.dll`
3. Redemarrer SimHub

## Configuration

1. Ouvrir SimHub
2. Aller dans **Additional Plugins** → **AGP Strategy Suite**
3. Configurer:
   - **Host**: `localhost` (ou IP du PC avec AGP)
   - **Port**: `8765`
   - **Auto-connect**: Active par defaut

## Proprietes Disponibles

Toutes les proprietes sont prefixees par `AGP.`

### Connection

| Propriete | Type | Description |
|-----------|------|-------------|
| `AGP.Connected` | bool | Connecte au backend AGP |
| `AGP.Rf2Connected` | bool | rF2 detecte et actif |

### Temperatures Pneus

| Propriete | Type | Unite | Description |
|-----------|------|-------|-------------|
| `AGP.TireTemp_FL` | double | °C | Temperature pneu avant-gauche |
| `AGP.TireTemp_FR` | double | °C | Temperature pneu avant-droit |
| `AGP.TireTemp_RL` | double | °C | Temperature pneu arriere-gauche |
| `AGP.TireTemp_RR` | double | °C | Temperature pneu arriere-droit |
| `AGP.TireTemp_FrontAvg` | double | °C | Moyenne avant |
| `AGP.TireTemp_RearAvg` | double | °C | Moyenne arriere |

### Pressions Pneus

| Propriete | Type | Unite | Description |
|-----------|------|-------|-------------|
| `AGP.TirePressure_FL` | double | kPa | Pression pneu avant-gauche |
| `AGP.TirePressure_FR` | double | kPa | Pression pneu avant-droit |
| `AGP.TirePressure_RL` | double | kPa | Pression pneu arriere-gauche |
| `AGP.TirePressure_RR` | double | kPa | Pression pneu arriere-droit |

### Usure Pneus

| Propriete | Type | Unite | Description |
|-----------|------|-------|-------------|
| `AGP.TireWear_FL` | double | % | Usure pneu avant-gauche (100=neuf) |
| `AGP.TireWear_FR` | double | % | Usure pneu avant-droit |
| `AGP.TireWear_RL` | double | % | Usure pneu arriere-gauche |
| `AGP.TireWear_RR` | double | % | Usure pneu arriere-droit |
| `AGP.TireWear_FrontAvg` | double | % | Moyenne usure avant |
| `AGP.TireWear_RearAvg` | double | % | Moyenne usure arriere |

### Grip Pneus

| Propriete | Type | Unite | Description |
|-----------|------|-------|-------------|
| `AGP.TireGrip_FL` | double | % | Niveau grip avant-gauche |
| `AGP.TireGrip_FR` | double | % | Niveau grip avant-droit |
| `AGP.TireGrip_RL` | double | % | Niveau grip arriere-gauche |
| `AGP.TireGrip_RR` | double | % | Niveau grip arriere-droit |

### Temperatures Freins

| Propriete | Type | Unite | Description |
|-----------|------|-------|-------------|
| `AGP.BrakeTemp_FL` | double | °C | Temperature frein avant-gauche |
| `AGP.BrakeTemp_FR` | double | °C | Temperature frein avant-droit |
| `AGP.BrakeTemp_RL` | double | °C | Temperature frein arriere-gauche |
| `AGP.BrakeTemp_RR` | double | °C | Temperature frein arriere-droit |

### Analyse Comportement

| Propriete | Type | Unite | Description |
|-----------|------|-------|-------------|
| `AGP.Understeer_Pct` | double | % | Pourcentage sous-virage detecte |
| `AGP.Oversteer_Pct` | double | % | Pourcentage survirage detecte |
| `AGP.TractionLoss_Pct` | double | % | Perte de traction |
| `AGP.BrakeLock_Pct` | double | % | Blocage de roues au freinage |
| `AGP.CornerPhase` | string | - | Phase virage (entry/apex/exit) |
| `AGP.BalanceScore` | double | - | Score equilibrage global |
| `AGP.EntryBalance` | double | - | Equilibre en entree de virage |
| `AGP.MidCornerBalance` | double | - | Equilibre au point de corde |
| `AGP.ExitBalance` | double | - | Equilibre en sortie |

### Strategie

| Propriete | Type | Unite | Description |
|-----------|------|-------|-------------|
| `AGP.FuelLapsRemaining` | double | tours | Tours restants avec carburant |
| `AGP.TireLapsRemaining` | int | tours | Tours avant changement pneus |
| `AGP.PitWindowStart` | int | tour | Debut fenetre pit optimale |
| `AGP.PitWindowEnd` | int | tour | Fin fenetre pit optimale |
| `AGP.InPitWindow` | bool | - | Dans la fenetre de pit |
| `AGP.NextPitLap` | int | tour | Prochain arret prevu |
| `AGP.OptimalPitLap` | int | tour | Tour optimal pour pit |
| `AGP.IsCritical` | bool | - | Situation critique (fuel/pneus) |
| `AGP.CurrentStint` | int | - | Numero du stint actuel |
| `AGP.CurrentDriver` | string | - | Nom du pilote actuel |

### Recommandations

| Propriete | Type | Description |
|-----------|------|-------------|
| `AGP.NextRecommendation` | string | Titre de la prochaine recommandation |
| `AGP.NextRecommendationPriority` | int | Priorite (1=critique, 5=basse) |
| `AGP.NextRecommendationAction` | string | Action recommandee |
| `AGP.RecommendationCount` | int | Nombre de recommandations actives |

### Live Timing

| Propriete | Type | Unite | Description |
|-----------|------|-------|-------------|
| `AGP.Position` | int | - | Position actuelle |
| `AGP.TotalCars` | int | - | Nombre total de voitures |
| `AGP.GapAhead` | double | sec | Ecart avec la voiture devant |
| `AGP.GapBehind` | double | sec | Ecart avec la voiture derriere |
| `AGP.ThreatLevel` | string | - | Niveau menace (none/low/medium/high) |
| `AGP.NearestThreatName` | string | - | Nom du concurrent menacant |
| `AGP.NearestThreatGap` | double | sec | Ecart avec la menace |

### Proprietes Calculees

| Propriete | Type | Plage | Description |
|-----------|------|-------|-------------|
| `AGP.BalanceIndicator` | double | -100 to +100 | -100=sous-virage, +100=survirage |
| `AGP.TireCondition` | double | 0-100 | Condition globale des pneus |
| `AGP.FuelUrgency` | double | 0-100 | Urgence ravitaillement |

## Exemples NCalc

### Indicateur couleur pneus

```ncalc
if([AGP.TireTemp_FL] < 70, '#3498db',
   if([AGP.TireTemp_FL] < 90, '#2ecc71',
      if([AGP.TireTemp_FL] < 100, '#f39c12', '#e74c3c')))
```

### Alerte carburant

```ncalc
if([AGP.FuelLapsRemaining] < 3, 'FUEL CRITICAL!',
   if([AGP.FuelLapsRemaining] < 5, 'Low Fuel', ''))
```

### Balance visuelle

```ncalc
if([AGP.BalanceIndicator] < -20, 'UNDERSTEER',
   if([AGP.BalanceIndicator] > 20, 'OVERSTEER', 'NEUTRAL'))
```

### Menace derriere

```ncalc
if([AGP.ThreatLevel] == 'high', 'DEFEND!',
   if([AGP.ThreatLevel] == 'medium', 'Pressure', ''))
```

## Exemple Dashboard

### Widget Temperature Pneus

```json
{
  "Type": "TextBlock",
  "Text": "[AGP.TireTemp_FL:0]°C",
  "Foreground": {
    "Type": "Ncalc",
    "Expression": "if([AGP.TireTemp_FL] < 80, '#3498db', if([AGP.TireTemp_FL] < 100, '#2ecc71', '#e74c3c'))"
  }
}
```

### Widget Strategie

```json
{
  "Type": "StackPanel",
  "Children": [
    {
      "Type": "TextBlock",
      "Text": "Fuel: [AGP.FuelLapsRemaining:1] laps"
    },
    {
      "Type": "TextBlock",
      "Text": "Pit Window: [AGP.PitWindowStart]-[AGP.PitWindowEnd]"
    },
    {
      "Type": "TextBlock",
      "Text": "[AGP.NextRecommendation]",
      "Visibility": "[AGP.RecommendationCount] > 0"
    }
  ]
}
```

## Depannage

### Le plugin ne se connecte pas

1. Verifier que AGP Strategy Suite est lance
2. Verifier host/port dans les parametres
3. Verifier le pare-feu Windows

### Proprietes a zero

1. Verifier la connexion a rF2
2. Verifier que la voiture est en piste
3. Redemarrer SimHub

### Valeurs incorrectes

1. Mettre a jour le plugin
2. Verifier la version de AGP Strategy Suite
3. Reinitialiser la configuration
