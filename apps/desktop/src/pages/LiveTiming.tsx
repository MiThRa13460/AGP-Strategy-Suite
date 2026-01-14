import { useState, useEffect } from 'react'
import { StandingsTable } from '../components/StandingsTable'
import { OpponentCard } from '../components/OpponentCard'

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

interface SessionInfo {
  session_type: string
  session_name: string
  track_name: string
  elapsed_time: number
  remaining_time: number
  air_temp: number
  track_temp: number
  flag: string
}

interface LiveTimingData {
  session: SessionInfo | null
  standings: Standing[]
  player_id: string | null
  classes: string[]
}

export function LiveTimingPage() {
  const [data, setData] = useState<LiveTimingData>({
    session: null,
    standings: [],
    player_id: null,
    classes: [],
  })
  const [selectedClass, setSelectedClass] = useState<string | null>(null)
  const [selectedDriver, setSelectedDriver] = useState<Driver | null>(null)
  const [viewMode, setViewMode] = useState<'table' | 'threats'>('table')

  // In production, this would connect to the WebSocket server
  useEffect(() => {
    // Generate mock data for demonstration
    const mockStandings = generateMockStandings()
    setData({
      session: {
        session_type: 'race',
        session_name: 'Course 1',
        track_name: 'Spa-Francorchamps',
        elapsed_time: 3600,
        remaining_time: 1800,
        air_temp: 22,
        track_temp: 28,
        flag: 'green',
      },
      standings: mockStandings,
      player_id: 'player1',
      classes: ['GT3', 'GT4'],
    })

    // Simulate live updates
    const interval = setInterval(() => {
      setData(prev => ({
        ...prev,
        standings: updateMockStandings(prev.standings),
      }))
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  const playerPosition = data.standings.find(s => s.driver.id === data.player_id)?.position || 0
  const threats = data.standings.filter(s =>
    !s.driver.is_player &&
    s.driver.threat_level !== 'none' &&
    s.driver.position > playerPosition
  ).sort((a, b) => {
    const order = { critical: 0, high: 1, medium: 2, low: 3 }
    return (order[a.driver.threat_level as keyof typeof order] || 4) -
           (order[b.driver.threat_level as keyof typeof order] || 4)
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Live Timing</h2>
          <p className="text-sm text-gray-500">
            {data.session?.track_name || 'En attente de session'}
          </p>
        </div>

        <div className="flex items-center gap-4">
          {/* Session info */}
          {data.session && (
            <div className="flex items-center gap-4 text-sm">
              <FlagIndicator flag={data.session.flag} />
              <div className="text-gray-400">
                <span className="text-white">{formatTime(data.session.remaining_time)}</span> restant
              </div>
              <div className="flex items-center gap-2 text-gray-500">
                <span>Air: {data.session.air_temp}C</span>
                <span>Piste: {data.session.track_temp}C</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* View mode */}
          <button
            onClick={() => setViewMode('table')}
            className={`px-4 py-2 text-sm rounded-lg transition-all ${
              viewMode === 'table'
                ? 'bg-agp-accent/20 text-agp-accent'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            Classement
          </button>
          <button
            onClick={() => setViewMode('threats')}
            className={`px-4 py-2 text-sm rounded-lg transition-all ${
              viewMode === 'threats'
                ? 'bg-agp-accent/20 text-agp-accent'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            Menaces ({threats.length})
          </button>
        </div>

        {/* Class filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Classe:</span>
          <button
            onClick={() => setSelectedClass(null)}
            className={`px-3 py-1.5 text-xs rounded transition-all ${
              selectedClass === null
                ? 'bg-agp-accent text-black'
                : 'bg-agp-border text-gray-400 hover:text-white'
            }`}
          >
            Toutes
          </button>
          {data.classes.map(cls => (
            <button
              key={cls}
              onClick={() => setSelectedClass(cls)}
              className={`px-3 py-1.5 text-xs rounded transition-all ${
                selectedClass === cls
                  ? 'bg-agp-accent text-black'
                  : 'bg-agp-border text-gray-400 hover:text-white'
              }`}
            >
              {cls}
            </button>
          ))}
        </div>
      </div>

      {/* Main content */}
      <div className="grid grid-cols-12 gap-6">
        {/* Standings or Threats view */}
        <div className={selectedDriver ? 'col-span-8' : 'col-span-12'}>
          {viewMode === 'table' ? (
            <StandingsTable
              standings={data.standings}
              playerId={data.player_id}
              selectedClass={selectedClass}
              onSelectDriver={(driver) => setSelectedDriver(driver)}
            />
          ) : (
            <ThreatsView
              threats={threats}
              onSelectDriver={(driver) => setSelectedDriver(driver)}
            />
          )}
        </div>

        {/* Selected driver detail */}
        {selectedDriver && (
          <div className="col-span-4">
            <OpponentCard
              driver={selectedDriver}
              playerPosition={playerPosition}
              onClose={() => setSelectedDriver(null)}
            />
          </div>
        )}
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-4 gap-4">
        <QuickStat
          label="Position"
          value={`P${playerPosition}`}
          subtext={`sur ${data.standings.length}`}
        />
        <QuickStat
          label="Ecart leader"
          value={formatGapShort(data.standings.find(s => s.driver.id === data.player_id)?.gap_to_leader)}
        />
        <QuickStat
          label="Menaces proches"
          value={threats.filter(t => t.driver.threat_level === 'critical' || t.driver.threat_level === 'high').length.toString()}
          highlight={threats.some(t => t.driver.threat_level === 'critical')}
        />
        <QuickStat
          label="Pilotes en piste"
          value={data.standings.filter(s => !s.driver.in_pit).length.toString()}
          subtext={`${data.standings.filter(s => s.driver.in_pit).length} aux stands`}
        />
      </div>
    </div>
  )
}

// Threats view component
interface ThreatsViewProps {
  threats: Standing[]
  onSelectDriver: (driver: Driver) => void
}

function ThreatsView({ threats, onSelectDriver }: ThreatsViewProps) {
  if (threats.length === 0) {
    return (
      <div className="bg-agp-card border border-agp-border rounded-lg p-8 text-center">
        <div className="text-4xl mb-3">🛡️</div>
        <p className="text-gray-500">Aucune menace detectee</p>
        <p className="text-xs text-gray-600 mt-1">Les pilotes derriere vous sont plus lents ou trop loin</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {threats.map(standing => (
        <ThreatRow
          key={standing.driver.id}
          standing={standing}
          onClick={() => onSelectDriver(standing.driver)}
        />
      ))}
    </div>
  )
}

function ThreatRow({ standing, onClick }: { standing: Standing; onClick: () => void }) {
  const { driver } = standing
  const threatConfig = getThreatConfig(driver.threat_level)

  return (
    <div
      className="bg-agp-card border border-agp-border rounded-lg p-4 cursor-pointer hover:border-agp-accent/50 transition-all"
      style={{ borderLeftColor: threatConfig.color, borderLeftWidth: '3px' }}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="text-2xl font-bold text-white">P{driver.position}</div>
          <div>
            <div className="font-medium text-white">{driver.name}</div>
            <div className="text-xs text-gray-500">{driver.car_name}</div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-xs text-gray-500">Ecart</div>
            <div className="text-lg font-bold text-white tabular-nums">
              +{Math.abs(driver.gap_to_player).toFixed(2)}s
            </div>
          </div>

          <div className="text-right">
            <div className="text-xs text-gray-500">Rythme</div>
            <div className={`text-lg font-bold tabular-nums ${
              driver.pace_delta < 0 ? 'text-agp-danger' : 'text-gray-400'
            }`}>
              {driver.pace_delta > 0 ? '+' : ''}{driver.pace_delta.toFixed(2)}s
            </div>
          </div>

          <div
            className="px-3 py-1 rounded text-xs font-medium"
            style={{ backgroundColor: `${threatConfig.color}22`, color: threatConfig.color }}
          >
            {threatConfig.label}
          </div>
        </div>
      </div>
    </div>
  )
}

function FlagIndicator({ flag }: { flag: string }) {
  const config: Record<string, { color: string; label: string }> = {
    green: { color: '#00ff88', label: 'Vert' },
    yellow: { color: '#ffaa00', label: 'Jaune' },
    red: { color: '#ff3366', label: 'Rouge' },
    white: { color: '#ffffff', label: 'Blanc' },
    checkered: { color: '#888888', label: 'Damier' },
  }

  const flagConfig = config[flag] || config.green

  return (
    <div className="flex items-center gap-2">
      <div
        className="w-4 h-3 rounded-sm"
        style={{ backgroundColor: flagConfig.color }}
      />
      <span className="text-xs" style={{ color: flagConfig.color }}>
        {flagConfig.label}
      </span>
    </div>
  )
}

function QuickStat({ label, value, subtext, highlight }: {
  label: string
  value: string
  subtext?: string
  highlight?: boolean
}) {
  return (
    <div className="bg-agp-card border border-agp-border rounded-lg p-4">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${highlight ? 'text-agp-danger' : 'text-white'}`}>
        {value}
      </div>
      {subtext && <div className="text-xs text-gray-600">{subtext}</div>}
    </div>
  )
}

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)

  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatGapShort(gap: number | string | undefined): string {
  if (gap === undefined) return '-'
  if (typeof gap === 'string') return gap
  if (gap <= 0) return 'Leader'
  return `+${gap.toFixed(1)}s`
}

function getThreatConfig(threat: string): { color: string; label: string } {
  switch (threat) {
    case 'critical': return { color: '#ff3366', label: 'Critique' }
    case 'high': return { color: '#ff8844', label: 'Elevee' }
    case 'medium': return { color: '#ffaa00', label: 'Moderee' }
    case 'low': return { color: '#88ff88', label: 'Faible' }
    default: return { color: '#666666', label: 'Aucune' }
  }
}

// Mock data generators
function generateMockStandings(): Standing[] {
  const names = [
    'Max Verstappen', 'Lewis Hamilton', 'Charles Leclerc', 'Carlos Sainz',
    'Lando Norris', 'Oscar Piastri', 'George Russell', 'Fernando Alonso',
    'Pierre Gasly', 'Esteban Ocon', 'Lance Stroll', 'Yuki Tsunoda',
  ]

  const classes = ['GT3', 'GT3', 'GT3', 'GT3', 'GT4', 'GT4', 'GT3', 'GT3', 'GT4', 'GT4', 'GT3', 'GT4']

  return names.map((name, idx) => {
    const isPlayer = idx === 4 // Player is P5
    const position = idx + 1
    const baseTime = 120 + Math.random() * 5
    const lastLapTime = baseTime + (Math.random() - 0.5) * 3

    const driver: Driver = {
      id: isPlayer ? 'player1' : `driver${idx}`,
      name,
      car_number: String(idx + 1),
      car_class: classes[idx],
      car_name: classes[idx] === 'GT3' ? 'Porsche 911 GT3 R' : 'BMW M4 GT4',
      team: `Team ${idx + 1}`,
      is_player: isPlayer,
      position,
      class_position: position,
      laps_completed: 15 + Math.floor(Math.random() * 3),
      pit_status: 'on_track',
      pit_stops: Math.floor(Math.random() * 2),
      in_pit: Math.random() < 0.1,
      gap_to_leader: idx === 0 ? 0 : idx * 2 + Math.random() * 3,
      gap_to_ahead: idx === 0 ? 0 : 1.5 + Math.random() * 2,
      gap_to_player: isPlayer ? 0 : (idx - 4) * 2,
      threat_level: position > 5 ? ['none', 'low', 'medium', 'high', 'critical'][Math.floor(Math.random() * 5)] : 'none',
      pace_delta: isPlayer ? 0 : (Math.random() - 0.5) * 1.5,
      best_lap: {
        total: baseTime,
        formatted: formatLapTime(baseTime),
        is_personal_best: true,
        is_session_best: idx === 0,
      },
      last_lap: {
        total: lastLapTime,
        formatted: formatLapTime(lastLapTime),
        is_personal_best: lastLapTime < baseTime,
        is_session_best: false,
      },
    }

    return {
      position,
      driver,
      gap_to_leader: driver.gap_to_leader,
      gap_to_ahead: driver.gap_to_ahead,
      interval: driver.gap_to_ahead,
      last_lap: driver.last_lap,
      best_lap: driver.best_lap,
      laps: driver.laps_completed,
      pit_stops: driver.pit_stops,
      status: driver.in_pit ? 'pit' : 'running',
    }
  })
}

function updateMockStandings(standings: Standing[]): Standing[] {
  return standings.map(s => ({
    ...s,
    driver: {
      ...s.driver,
      gap_to_player: s.driver.gap_to_player + (Math.random() - 0.5) * 0.5,
      pace_delta: s.driver.pace_delta + (Math.random() - 0.5) * 0.1,
    },
  }))
}

function formatLapTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toFixed(3).padStart(6, '0')}`
}

export default LiveTimingPage
