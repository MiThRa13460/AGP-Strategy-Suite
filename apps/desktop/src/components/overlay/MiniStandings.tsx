import { useTelemetryStore } from '../../stores/telemetryStore'

interface Standing {
  position: number
  driverName: string
  gap: string
  interval: string
  isPlayer: boolean
  className: string
  classColor: string
  threat: 'none' | 'low' | 'medium' | 'high'
}

// Mock standings data - would come from WebSocket in production
function useStandingsData(): Standing[] {
  const { telemetry } = useTelemetryStore()
  const playerPosition = telemetry?.position || 3

  // Generate mock standings around player position
  const standings: Standing[] = []

  for (let i = 1; i <= 10; i++) {
    const isPlayer = i === playerPosition
    standings.push({
      position: i,
      driverName: isPlayer ? 'MOI' : `Driver ${i}`,
      gap: i === 1 ? 'Leader' : `+${((i - 1) * 2.5 + Math.random() * 3).toFixed(1)}s`,
      interval: i === 1 ? '-' : `+${(Math.random() * 3 + 0.5).toFixed(1)}s`,
      isPlayer,
      className: i <= 3 ? 'Pro' : i <= 6 ? 'Am' : 'GT4',
      classColor: i <= 3 ? '#00ff88' : i <= 6 ? '#ffaa00' : '#00aaff',
      threat: !isPlayer && Math.abs(i - playerPosition) <= 1
        ? (i < playerPosition ? 'high' : 'medium')
        : 'none',
    })
  }

  return standings
}

export function MiniStandings() {
  const standings = useStandingsData()

  // Show only relevant positions (around player)
  const playerIndex = standings.findIndex(s => s.isPlayer)
  const startIndex = Math.max(0, playerIndex - 3)
  const visibleStandings = standings.slice(startIndex, startIndex + 8)

  return (
    <div className="w-full h-full bg-black/85 backdrop-blur-sm rounded-lg p-2 text-white select-none overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-2 px-1">
        <span className="text-xs text-gray-500 uppercase tracking-wide">Classement</span>
        <span className="text-[10px] text-gray-600">
          {standings.length} voitures
        </span>
      </div>

      {/* Standings list */}
      <div className="space-y-0.5">
        {visibleStandings.map((standing) => (
          <StandingRow key={standing.position} standing={standing} />
        ))}
      </div>

      {/* Show more indicator if needed */}
      {startIndex + 8 < standings.length && (
        <div className="text-center text-[10px] text-gray-600 mt-1">
          +{standings.length - (startIndex + 8)} autres
        </div>
      )}
    </div>
  )
}

interface StandingRowProps {
  standing: Standing
}

function StandingRow({ standing }: StandingRowProps) {
  const threatColors = {
    none: '',
    low: 'border-l-2 border-yellow-500/50',
    medium: 'border-l-2 border-orange-500',
    high: 'border-l-2 border-agp-danger',
  }

  return (
    <div
      className={`flex items-center gap-1 px-1.5 py-1 rounded ${
        standing.isPlayer
          ? 'bg-agp-accent/20 border border-agp-accent/50'
          : 'bg-black/40 hover:bg-black/60'
      } ${threatColors[standing.threat]}`}
    >
      {/* Position */}
      <div className={`w-5 text-center text-xs font-bold ${
        standing.position <= 3 ? 'text-agp-accent' : 'text-gray-400'
      }`}>
        {standing.position}
      </div>

      {/* Class badge */}
      <div
        className="w-1 h-4 rounded-sm"
        style={{ backgroundColor: standing.classColor }}
        title={standing.className}
      />

      {/* Driver name */}
      <div className={`flex-1 text-xs truncate ${
        standing.isPlayer ? 'text-white font-bold' : 'text-gray-300'
      }`}>
        {standing.driverName}
      </div>

      {/* Gap/Interval */}
      <div className="text-right">
        <div className={`text-[10px] tabular-nums ${
          standing.position === 1 ? 'text-agp-accent' : 'text-gray-400'
        }`}>
          {standing.gap}
        </div>
        {standing.position > 1 && (
          <div className="text-[8px] text-gray-600 tabular-nums">
            {standing.interval}
          </div>
        )}
      </div>

      {/* Threat indicator */}
      {standing.threat !== 'none' && !standing.isPlayer && (
        <div className={`w-1.5 h-1.5 rounded-full ${
          standing.threat === 'high' ? 'bg-agp-danger animate-pulse' :
          standing.threat === 'medium' ? 'bg-orange-500' : 'bg-yellow-500'
        }`} />
      )}
    </div>
  )
}

export default MiniStandings
