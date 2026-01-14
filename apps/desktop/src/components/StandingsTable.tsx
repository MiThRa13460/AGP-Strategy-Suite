interface LapTime {
  total: number
  formatted: string
  is_personal_best: boolean
  is_session_best: boolean
}

interface Driver {
  id: string
  name: string
  car_number: string
  car_class: string
  car_name: string
  team: string
  is_player: boolean
  position: number
  class_position: number
  laps_completed: number
  pit_status: string
  pit_stops: number
  in_pit: boolean
  gap_to_leader: number
  gap_to_ahead: number
  gap_to_player: number
  threat_level: string
  pace_delta: number
  best_lap: LapTime | null
  last_lap: LapTime | null
}

interface Standing {
  position: number
  driver: Driver
  gap_to_leader: number | string
  gap_to_ahead: number | string
  interval: number
  last_lap: LapTime | null
  best_lap: LapTime | null
  laps: number
  pit_stops: number
  status: string
}

interface StandingsTableProps {
  standings: Standing[]
  playerId: string | null
  selectedClass: string | null
  onSelectDriver?: (driver: Driver) => void
}

export function StandingsTable({ standings, playerId, selectedClass, onSelectDriver }: StandingsTableProps) {
  // Filter by class if selected
  const filteredStandings = selectedClass
    ? standings.filter(s => s.driver.car_class === selectedClass)
    : standings

  if (filteredStandings.length === 0) {
    return (
      <div className="bg-agp-card border border-agp-border rounded-lg p-8 text-center">
        <div className="text-3xl mb-2">🏁</div>
        <p className="text-gray-500">Aucune donnee de classement disponible</p>
      </div>
    )
  }

  return (
    <div className="bg-agp-card border border-agp-border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="grid grid-cols-12 gap-2 px-4 py-2 bg-black/30 text-xs text-gray-500 uppercase tracking-wide">
        <div className="col-span-1 text-center">Pos</div>
        <div className="col-span-3">Pilote</div>
        <div className="col-span-2 text-center">Ecart</div>
        <div className="col-span-2 text-center">Intervalle</div>
        <div className="col-span-2 text-center">Dernier</div>
        <div className="col-span-1 text-center">Tours</div>
        <div className="col-span-1 text-center">Pits</div>
      </div>

      {/* Rows */}
      <div className="divide-y divide-agp-border/50">
        {filteredStandings.map((standing) => (
          <StandingRow
            key={standing.driver.id}
            standing={standing}
            isPlayer={standing.driver.id === playerId}
            onClick={() => onSelectDriver?.(standing.driver)}
          />
        ))}
      </div>
    </div>
  )
}

interface StandingRowProps {
  standing: Standing
  isPlayer: boolean
  onClick?: () => void
}

function StandingRow({ standing, isPlayer, onClick }: StandingRowProps) {
  const { driver, gap_to_leader, interval, last_lap, laps, pit_stops, status } = standing

  const threatColor = getThreatColor(driver.threat_level)
  const isInPit = status === 'pit' || driver.in_pit

  return (
    <div
      className={`grid grid-cols-12 gap-2 px-4 py-3 items-center transition-colors cursor-pointer hover:bg-white/5 ${
        isPlayer ? 'bg-agp-accent/10 border-l-2 border-agp-accent' : ''
      } ${isInPit ? 'opacity-60' : ''}`}
      onClick={onClick}
    >
      {/* Position */}
      <div className="col-span-1 text-center">
        <span className={`text-lg font-bold ${isPlayer ? 'text-agp-accent' : 'text-white'}`}>
          {driver.position}
        </span>
        {driver.class_position > 0 && driver.class_position !== driver.position && (
          <div className="text-[10px] text-gray-500">
            C{driver.class_position}
          </div>
        )}
      </div>

      {/* Driver info */}
      <div className="col-span-3">
        <div className="flex items-center gap-2">
          {/* Threat indicator */}
          {!isPlayer && driver.threat_level !== 'none' && (
            <div
              className="w-1.5 h-6 rounded-full"
              style={{ backgroundColor: threatColor }}
              title={`Menace: ${driver.threat_level}`}
            />
          )}

          <div>
            <div className="flex items-center gap-2">
              {driver.car_number && (
                <span className="text-xs px-1.5 py-0.5 rounded bg-agp-border text-gray-400">
                  #{driver.car_number}
                </span>
              )}
              <span className={`font-medium ${isPlayer ? 'text-agp-accent' : 'text-white'}`}>
                {driver.name}
              </span>
            </div>
            <div className="text-[10px] text-gray-500 flex items-center gap-2">
              {driver.car_class && (
                <ClassBadge carClass={driver.car_class} />
              )}
              <span className="truncate max-w-[120px]">{driver.car_name}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Gap to leader */}
      <div className="col-span-2 text-center">
        {standing.position === 1 ? (
          <span className="text-agp-accent font-medium">Leader</span>
        ) : (
          <span className="text-gray-400 tabular-nums">
            {formatGap(gap_to_leader)}
          </span>
        )}
      </div>

      {/* Interval */}
      <div className="col-span-2 text-center">
        {standing.position === 1 ? (
          <span className="text-gray-600">-</span>
        ) : (
          <GapDisplay gap={interval} paceCompare={driver.pace_delta} />
        )}
      </div>

      {/* Last lap */}
      <div className="col-span-2 text-center">
        {last_lap ? (
          <span className={`tabular-nums ${
            last_lap.is_session_best ? 'text-purple-400' :
            last_lap.is_personal_best ? 'text-agp-accent' :
            'text-white'
          }`}>
            {last_lap.formatted}
          </span>
        ) : (
          <span className="text-gray-600">--:--.---</span>
        )}
      </div>

      {/* Laps */}
      <div className="col-span-1 text-center">
        <span className="text-gray-400 tabular-nums">{laps}</span>
      </div>

      {/* Pit stops */}
      <div className="col-span-1 text-center">
        <span className={`tabular-nums ${isInPit ? 'text-agp-warning' : 'text-gray-400'}`}>
          {pit_stops}
          {isInPit && <span className="text-agp-warning ml-1">P</span>}
        </span>
      </div>
    </div>
  )
}

function ClassBadge({ carClass }: { carClass: string }) {
  const color = getClassColor(carClass)

  return (
    <span
      className="text-[10px] px-1 py-0.5 rounded"
      style={{ backgroundColor: `${color}22`, color }}
    >
      {carClass}
    </span>
  )
}

function GapDisplay({ gap, paceCompare }: { gap: number; paceCompare: number }) {
  // paceCompare: negative = opponent is faster
  const trendColor = paceCompare < -0.3 ? 'text-agp-danger' : paceCompare > 0.3 ? 'text-agp-accent' : 'text-gray-400'

  return (
    <div className="flex flex-col items-center">
      <span className="text-white tabular-nums">
        +{gap.toFixed(3)}
      </span>
      {Math.abs(paceCompare) > 0.1 && (
        <span className={`text-[10px] ${trendColor}`}>
          {paceCompare > 0 ? '↓' : '↑'} {Math.abs(paceCompare).toFixed(2)}s/lap
        </span>
      )}
    </div>
  )
}

function formatGap(gap: number | string): string {
  if (typeof gap === 'string') return gap
  if (gap <= 0) return 'Leader'
  if (gap >= 60) {
    const laps = Math.floor(gap / 60)
    return `+${laps} tour${laps > 1 ? 's' : ''}`
  }
  return `+${gap.toFixed(3)}`
}

function getThreatColor(threat: string): string {
  switch (threat) {
    case 'critical': return '#ff3366'
    case 'high': return '#ff8844'
    case 'medium': return '#ffaa00'
    case 'low': return '#88ff88'
    default: return 'transparent'
  }
}

function getClassColor(carClass: string): string {
  // Generate consistent color from class name
  let hash = 0
  for (let i = 0; i < carClass.length; i++) {
    hash = carClass.charCodeAt(i) + ((hash << 5) - hash)
  }

  const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#dfe6e9', '#fd79a8', '#a29bfe']
  return colors[Math.abs(hash) % colors.length]
}

export default StandingsTable
