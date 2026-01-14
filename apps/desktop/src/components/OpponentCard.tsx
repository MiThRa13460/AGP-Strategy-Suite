interface LapTime {
  total: number
  formatted: string
  sector1?: number | null
  sector2?: number | null
  sector3?: number | null
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

interface OpponentCardProps {
  driver: Driver
  playerPosition: number
  onClose?: () => void
}

export function OpponentCard({ driver, playerPosition, onClose }: OpponentCardProps) {
  const isAhead = driver.position < playerPosition
  const gapToPlayer = Math.abs(driver.gap_to_player)
  const threatConfig = getThreatConfig(driver.threat_level)

  return (
    <div className="bg-agp-card border border-agp-border rounded-lg overflow-hidden">
      {/* Header */}
      <div
        className="px-4 py-3 flex items-center justify-between"
        style={{ background: `linear-gradient(135deg, ${threatConfig.color}22, transparent)` }}
      >
        <div className="flex items-center gap-3">
          {/* Position badge */}
          <div className="w-10 h-10 rounded-lg bg-black/30 flex items-center justify-center">
            <span className="text-xl font-bold text-white">P{driver.position}</span>
          </div>

          <div>
            <div className="flex items-center gap-2">
              {driver.car_number && (
                <span className="text-xs px-1.5 py-0.5 rounded bg-agp-border text-gray-400">
                  #{driver.car_number}
                </span>
              )}
              <span className="font-bold text-white">{driver.name}</span>
            </div>
            <div className="text-xs text-gray-500">{driver.car_name}</div>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-white transition-colors"
          >
            ✕
          </button>
        )}
      </div>

      {/* Threat indicator */}
      <div
        className="px-4 py-2 flex items-center justify-between"
        style={{ backgroundColor: `${threatConfig.color}11` }}
      >
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: threatConfig.color }}
          />
          <span className="text-sm" style={{ color: threatConfig.color }}>
            {threatConfig.label}
          </span>
        </div>
        <span className="text-xs text-gray-500">
          {isAhead ? 'Devant vous' : 'Derriere vous'}
        </span>
      </div>

      {/* Gap info */}
      <div className="p-4 grid grid-cols-2 gap-4">
        {/* Gap to player */}
        <div className="text-center p-3 rounded-lg bg-black/20">
          <div className="text-xs text-gray-500 mb-1">Ecart</div>
          <div className="text-2xl font-bold text-white tabular-nums">
            {isAhead ? '-' : '+'}{gapToPlayer.toFixed(3)}
          </div>
          <div className="text-xs text-gray-600">secondes</div>
        </div>

        {/* Pace delta */}
        <div className="text-center p-3 rounded-lg bg-black/20">
          <div className="text-xs text-gray-500 mb-1">Rythme</div>
          <div className={`text-2xl font-bold tabular-nums ${
            driver.pace_delta < -0.3 ? 'text-agp-danger' :
            driver.pace_delta > 0.3 ? 'text-agp-accent' :
            'text-white'
          }`}>
            {driver.pace_delta > 0 ? '+' : ''}{driver.pace_delta.toFixed(2)}
          </div>
          <div className="text-xs text-gray-600">s/tour vs vous</div>
        </div>
      </div>

      {/* Lap times */}
      <div className="px-4 pb-4">
        <div className="text-xs text-gray-500 mb-2">Temps au tour</div>
        <div className="grid grid-cols-2 gap-3">
          {/* Last lap */}
          <div className="p-2 rounded bg-black/20">
            <div className="text-[10px] text-gray-600 mb-1">Dernier tour</div>
            {driver.last_lap ? (
              <div className={`text-lg font-medium tabular-nums ${
                driver.last_lap.is_session_best ? 'text-purple-400' :
                driver.last_lap.is_personal_best ? 'text-agp-accent' :
                'text-white'
              }`}>
                {driver.last_lap.formatted}
              </div>
            ) : (
              <div className="text-lg text-gray-600">--:--.---</div>
            )}
          </div>

          {/* Best lap */}
          <div className="p-2 rounded bg-black/20">
            <div className="text-[10px] text-gray-600 mb-1">Meilleur tour</div>
            {driver.best_lap ? (
              <div className={`text-lg font-medium tabular-nums ${
                driver.best_lap.is_session_best ? 'text-purple-400' : 'text-agp-accent'
              }`}>
                {driver.best_lap.formatted}
              </div>
            ) : (
              <div className="text-lg text-gray-600">--:--.---</div>
            )}
          </div>
        </div>

        {/* Sector times if available */}
        {driver.last_lap?.sector1 && (
          <div className="mt-3 grid grid-cols-3 gap-2">
            <SectorTime label="S1" time={driver.last_lap.sector1} />
            <SectorTime label="S2" time={driver.last_lap.sector2} />
            <SectorTime label="S3" time={driver.last_lap.sector3} />
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="px-4 pb-4 grid grid-cols-3 gap-2">
        <StatBox label="Tours" value={driver.laps_completed} />
        <StatBox label="Pit stops" value={driver.pit_stops} />
        <StatBox
          label="Statut"
          value={driver.in_pit ? 'Pit' : 'Piste'}
          highlight={driver.in_pit}
        />
      </div>

      {/* Projection */}
      {!isAhead && driver.pace_delta < -0.2 && gapToPlayer > 0 && (
        <div className="px-4 pb-4">
          <div className="p-3 rounded-lg bg-agp-danger/10 border border-agp-danger/30">
            <div className="text-xs text-agp-danger mb-1">Projection</div>
            <div className="text-sm text-white">
              Rattrapage prevu dans ~{Math.ceil(gapToPlayer / Math.abs(driver.pace_delta))} tours
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function SectorTime({ label, time }: { label: string; time: number | null | undefined }) {
  if (!time) return null

  return (
    <div className="text-center p-1.5 rounded bg-black/20">
      <div className="text-[10px] text-gray-600">{label}</div>
      <div className="text-sm text-white tabular-nums">
        {time.toFixed(3)}
      </div>
    </div>
  )
}

function StatBox({ label, value, highlight }: { label: string; value: string | number; highlight?: boolean }) {
  return (
    <div className="text-center p-2 rounded bg-black/20">
      <div className="text-[10px] text-gray-600">{label}</div>
      <div className={`text-sm font-medium ${highlight ? 'text-agp-warning' : 'text-white'}`}>
        {value}
      </div>
    </div>
  )
}

function getThreatConfig(threat: string): { color: string; label: string } {
  switch (threat) {
    case 'critical':
      return { color: '#ff3366', label: 'Menace critique' }
    case 'high':
      return { color: '#ff8844', label: 'Menace elevee' }
    case 'medium':
      return { color: '#ffaa00', label: 'Menace moderee' }
    case 'low':
      return { color: '#88ff88', label: 'Menace faible' }
    default:
      return { color: '#666666', label: 'Aucune menace' }
  }
}

export default OpponentCard
