interface BrakeData {
  FL: number
  FR: number
  RL: number
  RR: number
}

interface BrakeDisplayProps {
  temps: BrakeData
  brakePct: number
}

export function BrakeDisplay({ temps, brakePct }: BrakeDisplayProps) {
  const avgFront = (temps.FL + temps.FR) / 2
  const avgRear = (temps.RL + temps.RR) / 2
  const maxTemp = Math.max(temps.FL, temps.FR, temps.RL, temps.RR)

  return (
    <div className="bg-agp-card border border-agp-border rounded-lg p-6">
      <h3 className="text-sm text-gray-400 mb-4">Freins</h3>

      {/* Brake pedal indicator */}
      <div className="flex items-center gap-4 mb-4">
        <div className="flex-1">
          <div className="text-xs text-gray-500 mb-1">Pedale</div>
          <div className="h-3 bg-agp-border rounded-full overflow-hidden">
            <div
              className="h-full bg-agp-danger rounded-full transition-all duration-75"
              style={{ width: `${brakePct}%` }}
            />
          </div>
        </div>
        <div className="text-xl font-bold text-agp-danger">
          {Math.round(brakePct)}%
        </div>
      </div>

      {/* Temperature grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Front */}
        <div className="space-y-2">
          <div className="text-xs text-gray-500 text-center">Avant</div>
          <div className="flex justify-center gap-4">
            <BrakeDisc temp={temps.FL} label="G" />
            <BrakeDisc temp={temps.FR} label="D" />
          </div>
          <div className="text-center">
            <span className={`text-sm font-medium ${getTempTextColor(avgFront)}`}>
              Moy: {Math.round(avgFront)}°C
            </span>
          </div>
        </div>

        {/* Rear */}
        <div className="space-y-2">
          <div className="text-xs text-gray-500 text-center">Arriere</div>
          <div className="flex justify-center gap-4">
            <BrakeDisc temp={temps.RL} label="G" />
            <BrakeDisc temp={temps.RR} label="D" />
          </div>
          <div className="text-center">
            <span className={`text-sm font-medium ${getTempTextColor(avgRear)}`}>
              Moy: {Math.round(avgRear)}°C
            </span>
          </div>
        </div>
      </div>

      {/* Max temperature warning */}
      {maxTemp > 650 && (
        <div className={`mt-4 p-2 rounded text-center text-sm ${
          maxTemp > 750 ? 'bg-agp-danger/20 text-agp-danger' : 'bg-agp-warning/20 text-agp-warning'
        }`}>
          {maxTemp > 750 ? '⚠️ SURCHAUFFE FREINS' : '⚡ Freins chauds'}
        </div>
      )}

      {/* Temperature scale */}
      <div className="mt-4 flex items-center justify-between text-[10px] text-gray-500">
        <span>200°C</span>
        <div className="flex-1 mx-2 h-1.5 rounded-full bg-gradient-to-r from-blue-500 via-green-500 via-yellow-500 to-red-500" />
        <span>800°C</span>
      </div>
    </div>
  )
}

interface BrakeDiscProps {
  temp: number
  label: string
}

function BrakeDisc({ temp, label }: BrakeDiscProps) {
  const color = getTempColor(temp)
  const glowIntensity = Math.min((temp - 300) / 500, 1) * 0.5

  return (
    <div className="flex flex-col items-center">
      <div className="text-[10px] text-gray-600 mb-1">{label}</div>
      <div
        className="w-10 h-10 rounded-full border-4 flex items-center justify-center transition-all"
        style={{
          borderColor: color,
          boxShadow: temp > 400 ? `0 0 ${10 + glowIntensity * 20}px ${color}` : 'none',
          background: `radial-gradient(circle, ${color}33, transparent)`
        }}
      >
        <span className="text-xs font-bold" style={{ color }}>
          {Math.round(temp)}
        </span>
      </div>
    </div>
  )
}

function getTempColor(temp: number): string {
  if (temp < 300) return '#4488ff'   // Blue - cold
  if (temp < 400) return '#00ff88'   // Green - warming
  if (temp < 550) return '#88ff88'   // Light green - optimal
  if (temp < 650) return '#ffff00'   // Yellow - hot
  if (temp < 750) return '#ffaa00'   // Orange - very hot
  return '#ff3366'                    // Red - overheating
}

function getTempTextColor(temp: number): string {
  if (temp < 300) return 'text-blue-400'
  if (temp < 550) return 'text-agp-accent'
  if (temp < 700) return 'text-agp-warning'
  return 'text-agp-danger'
}

export default BrakeDisplay
