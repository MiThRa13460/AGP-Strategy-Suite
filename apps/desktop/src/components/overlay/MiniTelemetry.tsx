import { useTelemetryStore } from '../../stores/telemetryStore'

export function MiniTelemetry() {
  const { telemetry, analysis } = useTelemetryStore()

  if (!telemetry) {
    return (
      <div className="w-full h-full bg-black/80 backdrop-blur-sm rounded-lg p-3 flex items-center justify-center">
        <span className="text-gray-500 text-sm">En attente...</span>
      </div>
    )
  }

  const fuelLapsRemaining = telemetry.fuel_per_lap > 0
    ? Math.floor(telemetry.fuel / telemetry.fuel_per_lap)
    : 0

  return (
    <div className="w-full h-full bg-black/85 backdrop-blur-sm rounded-lg p-3 text-white select-none">
      {/* Speed & Gear */}
      <div className="flex items-end justify-between mb-2">
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-agp-accent tabular-nums">
            {telemetry.speed}
          </span>
          <span className="text-xs text-gray-500">km/h</span>
        </div>
        <div className="text-2xl font-bold tabular-nums">
          {telemetry.gear === 0 ? 'N' : telemetry.gear === -1 ? 'R' : telemetry.gear}
        </div>
      </div>

      {/* RPM Bar */}
      <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden mb-3">
        <div
          className="h-full rounded-full transition-all duration-75"
          style={{
            width: `${(telemetry.rpm / (telemetry.max_rpm || 8000)) * 100}%`,
            background: telemetry.rpm > (telemetry.max_rpm || 8000) * 0.9
              ? '#ff3366'
              : '#00ff88'
          }}
        />
      </div>

      {/* Compact stats */}
      <div className="grid grid-cols-3 gap-2 text-center">
        {/* Fuel */}
        <div className="bg-black/50 rounded p-1.5">
          <div className="text-[10px] text-gray-500">Fuel</div>
          <div className={`text-sm font-bold tabular-nums ${
            fuelLapsRemaining < 5 ? 'text-agp-danger' :
            fuelLapsRemaining < 10 ? 'text-agp-warning' : 'text-white'
          }`}>
            {fuelLapsRemaining}
          </div>
          <div className="text-[8px] text-gray-600">tours</div>
        </div>

        {/* Lap */}
        <div className="bg-black/50 rounded p-1.5">
          <div className="text-[10px] text-gray-500">Tour</div>
          <div className="text-sm font-bold text-white tabular-nums">
            {telemetry.lap_number}
          </div>
        </div>

        {/* Position */}
        <div className="bg-black/50 rounded p-1.5">
          <div className="text-[10px] text-gray-500">Pos</div>
          <div className="text-sm font-bold text-agp-accent tabular-nums">
            P{telemetry.position || '-'}
          </div>
        </div>
      </div>

      {/* Behavior indicators */}
      {analysis && (
        <div className="flex gap-1 mt-2">
          {analysis.understeer_pct > 20 && (
            <div className="flex-1 h-1 bg-agp-danger/60 rounded-full" title="Sous-virage" />
          )}
          {analysis.oversteer_pct > 20 && (
            <div className="flex-1 h-1 bg-agp-warning/60 rounded-full" title="Survirage" />
          )}
          {analysis.traction_loss_pct > 15 && (
            <div className="flex-1 h-1 bg-orange-500/60 rounded-full" title="Patinage" />
          )}
          {analysis.understeer_pct <= 20 && analysis.oversteer_pct <= 20 && analysis.traction_loss_pct <= 15 && (
            <div className="flex-1 h-1 bg-agp-success/60 rounded-full" title="OK" />
          )}
        </div>
      )}

      {/* Last lap time */}
      {telemetry.last_lap_time > 0 && (
        <div className="mt-2 text-center">
          <span className="text-xs text-gray-500">Dernier: </span>
          <span className="text-sm font-mono text-agp-accent">
            {formatLapTime(telemetry.last_lap_time)}
          </span>
        </div>
      )}
    </div>
  )
}

function formatLapTime(seconds: number): string {
  if (!seconds || seconds <= 0) return '--:--.---'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toFixed(3).padStart(6, '0')}`
}

export default MiniTelemetry
