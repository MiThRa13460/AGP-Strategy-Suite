interface TireData {
  FL: number
  FR: number
  RL: number
  RR: number
}

interface TireDisplayProps {
  temps: TireData
  pressures: TireData
  wear: TireData
  grip: TireData
}

export function TireDisplay({ temps, pressures, wear, grip }: TireDisplayProps) {
  return (
    <div className="bg-agp-card border border-agp-border rounded-lg p-6">
      <h3 className="text-sm text-gray-400 mb-4">Pneus</h3>

      {/* Car outline with tires */}
      <div className="relative w-full max-w-xs mx-auto">
        {/* Car body silhouette */}
        <div className="absolute inset-x-8 inset-y-4 border-2 border-agp-border rounded-lg opacity-30" />

        {/* Tire grid */}
        <div className="grid grid-cols-2 gap-x-16 gap-y-8 p-4">
          {/* Front Left */}
          <TireCorner
            corner="FL"
            temp={temps.FL}
            pressure={pressures.FL}
            wearPct={wear.FL}
            gripPct={grip.FL}
          />

          {/* Front Right */}
          <TireCorner
            corner="FR"
            temp={temps.FR}
            pressure={pressures.FR}
            wearPct={wear.FR}
            gripPct={grip.FR}
          />

          {/* Rear Left */}
          <TireCorner
            corner="RL"
            temp={temps.RL}
            pressure={pressures.RL}
            wearPct={wear.RL}
            gripPct={grip.RL}
          />

          {/* Rear Right */}
          <TireCorner
            corner="RR"
            temp={temps.RR}
            pressure={pressures.RR}
            wearPct={wear.RR}
            gripPct={grip.RR}
          />
        </div>
      </div>

      {/* Legend */}
      <div className="flex justify-center gap-6 mt-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-blue-400" /> Froid
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-agp-accent" /> Optimal
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-agp-danger" /> Chaud
        </span>
      </div>
    </div>
  )
}

interface TireCornerProps {
  corner: string
  temp: number
  pressure: number
  wearPct: number
  gripPct: number
}

function TireCorner({ corner, temp, pressure, wearPct, gripPct }: TireCornerProps) {
  const tempColor = getTempColor(temp)
  const wearColor = getWearColor(wearPct)
  const gripColor = getGripColor(gripPct)

  return (
    <div className="flex flex-col items-center">
      {/* Corner label */}
      <div className="text-xs text-gray-500 mb-1">{corner}</div>

      {/* Tire visual */}
      <div
        className="w-12 h-16 rounded-md border-2 flex flex-col items-center justify-center"
        style={{
          borderColor: tempColor,
          background: `linear-gradient(to top, ${tempColor}22, transparent)`
        }}
      >
        <span className={`text-lg font-bold`} style={{ color: tempColor }}>
          {Math.round(temp)}°
        </span>
      </div>

      {/* Pressure */}
      <div className="text-xs text-gray-400 mt-1">
        {Math.round(pressure)} kPa
      </div>

      {/* Wear & Grip bars */}
      <div className="w-full mt-2 space-y-1">
        <div className="flex items-center gap-1">
          <span className="text-[10px] text-gray-500 w-6">Wear</span>
          <div className="flex-1 h-1.5 bg-agp-border rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${wearPct}%`,
                backgroundColor: wearColor
              }}
            />
          </div>
          <span className="text-[10px] w-8" style={{ color: wearColor }}>
            {Math.round(wearPct)}%
          </span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-[10px] text-gray-500 w-6">Grip</span>
          <div className="flex-1 h-1.5 bg-agp-border rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${gripPct}%`,
                backgroundColor: gripColor
              }}
            />
          </div>
          <span className="text-[10px] w-8" style={{ color: gripColor }}>
            {Math.round(gripPct)}%
          </span>
        </div>
      </div>
    </div>
  )
}

function getTempColor(temp: number): string {
  if (temp < 60) return '#4488ff'   // Blue - cold
  if (temp < 75) return '#88aaff'   // Light blue - warming
  if (temp < 85) return '#00ff88'   // Green - optimal low
  if (temp < 95) return '#00ff88'   // Green - optimal
  if (temp < 105) return '#ffaa00'  // Yellow - hot
  return '#ff3366'                   // Red - too hot
}

function getWearColor(wear: number): string {
  if (wear > 80) return '#00ff88'   // Green - good
  if (wear > 50) return '#ffaa00'   // Yellow - medium
  if (wear > 25) return '#ff8844'   // Orange - worn
  return '#ff3366'                   // Red - critical
}

function getGripColor(grip: number): string {
  if (grip > 90) return '#00ff88'   // Green - excellent
  if (grip > 70) return '#88ff88'   // Light green - good
  if (grip > 50) return '#ffaa00'   // Yellow - medium
  return '#ff3366'                   // Red - poor
}

export default TireDisplay
