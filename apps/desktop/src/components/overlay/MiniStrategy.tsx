import { useTelemetryStore } from '../../stores/telemetryStore'

interface StrategyData {
  currentLap: number
  totalLaps: number
  fuelLapsRemaining: number
  tireLapsRemaining: number
  nextPitLap: number | null
  inPitWindow: boolean
  pitWindowStart: number
  pitWindowEnd: number
  recommendation: string
  isCritical: boolean
}

// Mock strategy data - would come from WebSocket in production
function useStrategyData(): StrategyData {
  const { telemetry } = useTelemetryStore()

  const fuelLapsRemaining = (telemetry?.fuel_per_lap ?? 0) > 0
    ? (telemetry?.fuel ?? 0) / (telemetry?.fuel_per_lap ?? 1)
    : 30

  // These would come from strategy engine via WebSocket
  return {
    currentLap: telemetry?.lap_number || 0,
    totalLaps: 100,
    fuelLapsRemaining,
    tireLapsRemaining: 22,
    nextPitLap: 52,
    inPitWindow: fuelLapsRemaining < 20 && fuelLapsRemaining > 5,
    pitWindowStart: 45,
    pitWindowEnd: 55,
    recommendation: 'Continuer',
    isCritical: fuelLapsRemaining < 5,
  }
}

export function MiniStrategy() {
  const strategy = useStrategyData()

  return (
    <div className="w-full h-full bg-black/85 backdrop-blur-sm rounded-lg p-3 text-white select-none">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-500 uppercase tracking-wide">Strategie</span>
        {strategy.isCritical && (
          <span className="text-[10px] px-1.5 py-0.5 bg-agp-danger/30 text-agp-danger rounded animate-pulse">
            CRITIQUE
          </span>
        )}
      </div>

      {/* Progress bar */}
      <div className="relative mb-3">
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          {/* Progress */}
          <div
            className="absolute h-full bg-agp-accent/40 rounded-full"
            style={{ width: `${(strategy.currentLap / strategy.totalLaps) * 100}%` }}
          />
          {/* Pit window */}
          <div
            className="absolute h-full bg-agp-warning/30"
            style={{
              left: `${(strategy.pitWindowStart / strategy.totalLaps) * 100}%`,
              width: `${((strategy.pitWindowEnd - strategy.pitWindowStart) / strategy.totalLaps) * 100}%`,
            }}
          />
          {/* Next pit marker */}
          {strategy.nextPitLap && (
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-white"
              style={{ left: `${(strategy.nextPitLap / strategy.totalLaps) * 100}%` }}
            />
          )}
        </div>
        <div className="flex justify-between text-[8px] text-gray-600 mt-0.5">
          <span>0</span>
          <span>{strategy.totalLaps}</span>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-2 mb-2">
        {/* Fuel */}
        <div className="bg-black/50 rounded p-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-gray-500">Carburant</span>
            <span className={`text-xs font-bold tabular-nums ${
              strategy.fuelLapsRemaining < 5 ? 'text-agp-danger' :
              strategy.fuelLapsRemaining < 10 ? 'text-agp-warning' : 'text-white'
            }`}>
              {strategy.fuelLapsRemaining.toFixed(1)}
            </span>
          </div>
          <div className="h-1 bg-gray-800 rounded-full mt-1 overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{
                width: `${Math.min((strategy.fuelLapsRemaining / 30) * 100, 100)}%`,
                backgroundColor: strategy.fuelLapsRemaining < 5 ? '#ff3366' :
                  strategy.fuelLapsRemaining < 10 ? '#ffaa00' : '#00ff88'
              }}
            />
          </div>
        </div>

        {/* Tires */}
        <div className="bg-black/50 rounded p-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-gray-500">Pneus</span>
            <span className={`text-xs font-bold tabular-nums ${
              strategy.tireLapsRemaining < 5 ? 'text-agp-danger' :
              strategy.tireLapsRemaining < 10 ? 'text-agp-warning' : 'text-white'
            }`}>
              {strategy.tireLapsRemaining}
            </span>
          </div>
          <div className="h-1 bg-gray-800 rounded-full mt-1 overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{
                width: `${Math.min((strategy.tireLapsRemaining / 30) * 100, 100)}%`,
                backgroundColor: strategy.tireLapsRemaining < 5 ? '#ff3366' :
                  strategy.tireLapsRemaining < 10 ? '#ffaa00' : '#00ff88'
              }}
            />
          </div>
        </div>
      </div>

      {/* Next pit info */}
      {strategy.nextPitLap && (
        <div className={`p-2 rounded text-center ${
          strategy.inPitWindow ? 'bg-agp-accent/20 border border-agp-accent/50' : 'bg-black/50'
        }`}>
          <div className="text-[10px] text-gray-500">
            {strategy.inPitWindow ? 'FENETRE OUVERTE' : 'Prochain pit'}
          </div>
          <div className="flex items-center justify-center gap-2">
            <span className={`text-lg font-bold ${strategy.inPitWindow ? 'text-agp-accent' : 'text-white'}`}>
              T{strategy.nextPitLap}
            </span>
            <span className="text-xs text-gray-500">
              ({strategy.nextPitLap - strategy.currentLap} tours)
            </span>
          </div>
        </div>
      )}

      {/* Recommendation */}
      <div className="mt-2 text-center">
        <span className={`text-xs font-medium ${
          strategy.isCritical ? 'text-agp-danger' : 'text-gray-400'
        }`}>
          {strategy.isCritical ? 'PIT IMMEDIAT' : strategy.recommendation}
        </span>
      </div>
    </div>
  )
}

export default MiniStrategy
