interface FuelGaugeProps {
  currentFuel: number
  tankCapacity: number
  consumptionPerLap: number
  lapsRemaining: number
  pitWindowStart: number
  pitWindowEnd: number
  currentLap: number
  isCritical: boolean
}

export function FuelGauge({
  currentFuel,
  tankCapacity,
  consumptionPerLap,
  lapsRemaining,
  pitWindowStart,
  pitWindowEnd,
  currentLap,
  isCritical,
}: FuelGaugeProps) {
  const fuelPercentage = (currentFuel / tankCapacity) * 100
  const inPitWindow = currentLap >= pitWindowStart && currentLap <= pitWindowEnd

  return (
    <div className="bg-agp-card border border-agp-border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm text-gray-400">Carburant</h3>
        {isCritical && (
          <span className="text-xs px-2 py-1 rounded bg-agp-danger/20 text-agp-danger animate-pulse">
            CRITIQUE
          </span>
        )}
      </div>

      {/* Main gauge */}
      <div className="relative mb-6">
        {/* Tank visualization */}
        <div className="h-32 w-full rounded-lg bg-black/30 border border-agp-border overflow-hidden relative">
          {/* Fuel level */}
          <div
            className="absolute bottom-0 left-0 right-0 transition-all duration-500"
            style={{
              height: `${fuelPercentage}%`,
              background: getFuelGradient(fuelPercentage, isCritical),
            }}
          />

          {/* Level markers */}
          {[25, 50, 75].map(level => (
            <div
              key={level}
              className="absolute left-0 right-0 border-t border-dashed border-gray-700"
              style={{ bottom: `${level}%` }}
            >
              <span className="absolute right-2 -top-3 text-[10px] text-gray-600">
                {level}%
              </span>
            </div>
          ))}

          {/* Current value overlay */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-4xl font-bold text-white tabular-nums">
                {currentFuel.toFixed(1)}
              </div>
              <div className="text-sm text-gray-400">litres</div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <StatBox
          label="Tours restants"
          value={lapsRemaining.toFixed(1)}
          highlight={lapsRemaining < 3}
          icon="🔄"
        />
        <StatBox
          label="Conso/tour"
          value={`${consumptionPerLap.toFixed(2)}L`}
          icon="⛽"
        />
      </div>

      {/* Pit window indicator */}
      <div className="p-3 rounded-lg bg-black/20 border border-agp-border">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-500">Fenetre de pit</span>
          {inPitWindow && (
            <span className="text-xs text-agp-accent">MAINTENANT</span>
          )}
        </div>

        {/* Window visualization */}
        <div className="relative h-6 bg-black/30 rounded-full overflow-hidden">
          {/* Window range */}
          <div
            className="absolute h-full bg-agp-accent/30"
            style={{
              left: `${(pitWindowStart / (pitWindowEnd + 10)) * 100}%`,
              width: `${((pitWindowEnd - pitWindowStart) / (pitWindowEnd + 10)) * 100}%`,
            }}
          />

          {/* Current position */}
          <div
            className="absolute h-full w-1 bg-white"
            style={{
              left: `${(currentLap / (pitWindowEnd + 10)) * 100}%`,
            }}
          />

          {/* Labels */}
          <div className="absolute inset-0 flex items-center justify-between px-2">
            <span className="text-[10px] text-gray-500">T{pitWindowStart}</span>
            <span className="text-[10px] text-gray-500">T{pitWindowEnd}</span>
          </div>
        </div>

        <div className="mt-2 text-center text-xs text-gray-400">
          {inPitWindow
            ? `${pitWindowEnd - currentLap} tours avant fin de fenetre`
            : currentLap < pitWindowStart
              ? `Fenetre dans ${pitWindowStart - currentLap} tours`
              : 'Fenetre depassee'}
        </div>
      </div>
    </div>
  )
}

interface StatBoxProps {
  label: string
  value: string
  highlight?: boolean
  icon?: string
}

function StatBox({ label, value, highlight, icon }: StatBoxProps) {
  return (
    <div className={`p-3 rounded-lg ${highlight ? 'bg-agp-danger/10 border border-agp-danger/30' : 'bg-black/20'}`}>
      <div className="flex items-center gap-2 mb-1">
        {icon && <span className="text-sm">{icon}</span>}
        <span className="text-xs text-gray-500">{label}</span>
      </div>
      <div className={`text-xl font-bold tabular-nums ${highlight ? 'text-agp-danger' : 'text-white'}`}>
        {value}
      </div>
    </div>
  )
}

function getFuelGradient(percentage: number, isCritical: boolean): string {
  if (isCritical || percentage < 15) {
    return 'linear-gradient(to top, #ff3366, #ff6644)'
  }
  if (percentage < 30) {
    return 'linear-gradient(to top, #ffaa00, #ffcc00)'
  }
  return 'linear-gradient(to top, #00aa55, #00ff88)'
}

export default FuelGauge
