import { useState } from 'react'
import { FuelGauge } from '../components/FuelGauge'
import { StrategyTimeline } from '../components/StrategyTimeline'

// Types
interface PitStop {
  lap: number
  stop_type: string
  fuel_to_add: number
  tire_compound: string | null
  estimated_duration: number
  completed: boolean
}

interface Stint {
  stint_number: number
  driver: string
  start_lap: number
  end_lap: number | null
  tire_compound: string
  laps_completed: number
}

interface Recommendation {
  action: string
  priority: number
  reason: string
  details: Record<string, unknown>
}

interface DriverInfo {
  name: string
  color: string
  totalLaps: number
  totalTime: string
}

// Mock data for development
const mockPitStops: PitStop[] = [
  { lap: 25, stop_type: 'fuel_and_tires', fuel_to_add: 85.0, tire_compound: 'medium', estimated_duration: 25, completed: true },
  { lap: 52, stop_type: 'fuel_and_tires', fuel_to_add: 90.0, tire_compound: 'hard', estimated_duration: 25, completed: false },
  { lap: 78, stop_type: 'fuel_only', fuel_to_add: 45.0, tire_compound: null, estimated_duration: 15, completed: false },
]

const mockStints: Stint[] = [
  { stint_number: 1, driver: 'Pierre', start_lap: 0, end_lap: 25, tire_compound: 'soft', laps_completed: 25 },
  { stint_number: 2, driver: 'Marc', start_lap: 25, end_lap: 52, tire_compound: 'medium', laps_completed: 27 },
  { stint_number: 3, driver: 'Pierre', start_lap: 52, end_lap: 78, tire_compound: 'hard', laps_completed: 0 },
  { stint_number: 4, driver: 'Marc', start_lap: 78, end_lap: 100, tire_compound: 'medium', laps_completed: 0 },
]

const mockRecommendations: Recommendation[] = [
  { action: 'stay_out', priority: 10, reason: 'Continuer le stint actuel', details: { fuel_laps: 18.5, tire_laps: 22 } },
]

const mockDrivers: DriverInfo[] = [
  { name: 'Pierre', color: '#00ff88', totalLaps: 45, totalTime: '1:32:15' },
  { name: 'Marc', color: '#ffaa00', totalLaps: 42, totalTime: '1:28:44' },
]

export function Strategy() {
  const [activeTab, setActiveTab] = useState<'overview' | 'planning' | 'drivers'>('overview')

  // Mock state - would come from WebSocket in production
  const currentLap = 38
  const totalLaps = 100
  const currentFuel = 52.3
  const tankCapacity = 110
  const consumptionPerLap = 2.85
  const lapsRemaining = currentFuel / consumptionPerLap
  const pitWindowStart = 45
  const pitWindowEnd = 55
  const isCritical = lapsRemaining < 5
  const currentStint = 2

  const recommendations = mockRecommendations
  const pitStops = mockPitStops
  const stints = mockStints
  const drivers = mockDrivers

  return (
    <div className="min-h-screen bg-agp-bg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Strategie Course</h1>
          <p className="text-sm text-gray-500">24 Heures du Mans - GT3 Pro</p>
        </div>

        {/* Status badges */}
        <div className="flex items-center gap-3">
          <StatusBadge
            label="Carburant"
            value={`${lapsRemaining.toFixed(1)} tours`}
            status={isCritical ? 'danger' : lapsRemaining < 10 ? 'warning' : 'ok'}
          />
          <StatusBadge
            label="Pneus"
            value="22 tours restants"
            status="ok"
          />
          <StatusBadge
            label="Position"
            value="P3 / 45"
            status="ok"
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {(['overview', 'planning', 'drivers'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'bg-agp-accent text-black'
                : 'bg-agp-card text-gray-400 hover:bg-agp-border'
            }`}
          >
            {tab === 'overview' ? 'Vue Generale' : tab === 'planning' ? 'Planification' : 'Pilotes'}
          </button>
        ))}
      </div>

      {/* Content based on active tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Timeline */}
          <StrategyTimeline
            totalLaps={totalLaps}
            currentLap={currentLap}
            pitStops={pitStops}
            stints={stints}
            currentStint={currentStint}
          />

          {/* Main grid */}
          <div className="grid grid-cols-12 gap-6">
            {/* Left: Fuel Gauge */}
            <div className="col-span-4">
              <FuelGauge
                currentFuel={currentFuel}
                tankCapacity={tankCapacity}
                consumptionPerLap={consumptionPerLap}
                lapsRemaining={lapsRemaining}
                pitWindowStart={pitWindowStart}
                pitWindowEnd={pitWindowEnd}
                currentLap={currentLap}
                isCritical={isCritical}
              />
            </div>

            {/* Middle: Recommendations */}
            <div className="col-span-4">
              <RecommendationsPanel recommendations={recommendations} />
            </div>

            {/* Right: Quick Stats */}
            <div className="col-span-4">
              <QuickStatsPanel
                currentLap={currentLap}
                totalLaps={totalLaps}
                stopsCompleted={pitStops.filter(s => s.completed).length}
                stopsRemaining={pitStops.filter(s => !s.completed).length}
                currentDriver={stints.find(s => s.stint_number === currentStint)?.driver || 'N/A'}
                nextPitLap={pitStops.find(s => !s.completed)?.lap || null}
              />
            </div>
          </div>
        </div>
      )}

      {activeTab === 'planning' && (
        <PlanningView
          pitStops={pitStops}
          stints={stints}
          totalLaps={totalLaps}
          tankCapacity={tankCapacity}
          consumptionPerLap={consumptionPerLap}
        />
      )}

      {activeTab === 'drivers' && (
        <DriversView drivers={drivers} stints={stints} currentStint={currentStint} />
      )}
    </div>
  )
}

// Sub-components

interface StatusBadgeProps {
  label: string
  value: string
  status: 'ok' | 'warning' | 'danger'
}

function StatusBadge({ label, value, status }: StatusBadgeProps) {
  const colors = {
    ok: 'bg-agp-success/10 border-agp-success/30 text-agp-success',
    warning: 'bg-agp-warning/10 border-agp-warning/30 text-agp-warning',
    danger: 'bg-agp-danger/10 border-agp-danger/30 text-agp-danger',
  }

  return (
    <div className={`px-3 py-2 rounded-lg border ${colors[status]}`}>
      <div className="text-[10px] uppercase tracking-wide opacity-70">{label}</div>
      <div className="text-sm font-bold">{value}</div>
    </div>
  )
}

interface RecommendationsPanelProps {
  recommendations: Recommendation[]
}

function RecommendationsPanel({ recommendations }: RecommendationsPanelProps) {
  const getActionIcon = (action: string) => {
    switch (action) {
      case 'pit_now': return '🚨'
      case 'pit_soon': return '⚠️'
      case 'prepare_wet': return '🌧️'
      case 'stay_out': return '✓'
      default: return '📊'
    }
  }

  const getActionColor = (action: string) => {
    switch (action) {
      case 'pit_now': return 'border-agp-danger bg-agp-danger/10'
      case 'pit_soon': return 'border-agp-warning bg-agp-warning/10'
      case 'prepare_wet': return 'border-blue-500 bg-blue-500/10'
      default: return 'border-agp-border bg-black/20'
    }
  }

  return (
    <div className="bg-agp-card border border-agp-border rounded-lg p-6 h-full">
      <h3 className="text-sm text-gray-400 mb-4">Recommandations</h3>

      <div className="space-y-3">
        {recommendations.map((rec, idx) => (
          <div
            key={idx}
            className={`p-4 rounded-lg border ${getActionColor(rec.action)}`}
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl">{getActionIcon(rec.action)}</span>
              <div className="flex-1">
                <div className="text-white font-medium">{rec.reason}</div>
                {rec.details && (
                  <div className="mt-2 text-xs text-gray-500">
                    {rec.details.fuel_laps && (
                      <span>Carburant: {String(rec.details.fuel_laps)} tours • </span>
                    )}
                    {rec.details.tire_laps && (
                      <span>Pneus: {String(rec.details.tire_laps)} tours</span>
                    )}
                  </div>
                )}
              </div>
              <div className="text-xs text-gray-600">P{rec.priority}</div>
            </div>
          </div>
        ))}

        {recommendations.length === 0 && (
          <div className="text-center text-gray-600 py-8">
            Aucune recommandation active
          </div>
        )}
      </div>
    </div>
  )
}

interface QuickStatsPanelProps {
  currentLap: number
  totalLaps: number
  stopsCompleted: number
  stopsRemaining: number
  currentDriver: string
  nextPitLap: number | null
}

function QuickStatsPanel({
  currentLap,
  totalLaps,
  stopsCompleted,
  stopsRemaining,
  currentDriver,
  nextPitLap,
}: QuickStatsPanelProps) {
  const progress = (currentLap / totalLaps) * 100

  return (
    <div className="bg-agp-card border border-agp-border rounded-lg p-6 h-full">
      <h3 className="text-sm text-gray-400 mb-4">Statistiques</h3>

      {/* Progress */}
      <div className="mb-6">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-500">Progression course</span>
          <span className="text-white font-bold">{progress.toFixed(1)}%</span>
        </div>
        <div className="h-2 bg-black/30 rounded-full overflow-hidden">
          <div
            className="h-full bg-agp-accent rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-4">
        <StatItem label="Pilote actuel" value={currentDriver} />
        <StatItem label="Prochain pit" value={nextPitLap ? `Tour ${nextPitLap}` : 'N/A'} />
        <StatItem label="Arrets effectues" value={String(stopsCompleted)} />
        <StatItem label="Arrets restants" value={String(stopsRemaining)} />
        <StatItem label="Tour actuel" value={`${currentLap}/${totalLaps}`} />
        <StatItem label="Tours restants" value={String(totalLaps - currentLap)} />
      </div>
    </div>
  )
}

interface StatItemProps {
  label: string
  value: string
}

function StatItem({ label, value }: StatItemProps) {
  return (
    <div className="p-3 bg-black/20 rounded-lg">
      <div className="text-[10px] text-gray-600 uppercase tracking-wide">{label}</div>
      <div className="text-white font-bold mt-1">{value}</div>
    </div>
  )
}

interface PlanningViewProps {
  pitStops: PitStop[]
  stints: Stint[]
  totalLaps: number
  tankCapacity: number
  consumptionPerLap: number
}

function PlanningView({ pitStops, stints, totalLaps, tankCapacity, consumptionPerLap }: PlanningViewProps) {
  const maxLapsPerTank = Math.floor(tankCapacity / consumptionPerLap)

  return (
    <div className="space-y-6">
      {/* Strategy calculator */}
      <div className="bg-agp-card border border-agp-border rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">Calculateur de Strategie</h3>

        <div className="grid grid-cols-4 gap-6 mb-6">
          <div className="p-4 bg-black/20 rounded-lg">
            <div className="text-xs text-gray-500 mb-1">Tours total</div>
            <div className="text-2xl font-bold text-white">{totalLaps}</div>
          </div>
          <div className="p-4 bg-black/20 rounded-lg">
            <div className="text-xs text-gray-500 mb-1">Capacite reservoir</div>
            <div className="text-2xl font-bold text-white">{tankCapacity}L</div>
          </div>
          <div className="p-4 bg-black/20 rounded-lg">
            <div className="text-xs text-gray-500 mb-1">Conso/tour</div>
            <div className="text-2xl font-bold text-white">{consumptionPerLap.toFixed(2)}L</div>
          </div>
          <div className="p-4 bg-black/20 rounded-lg">
            <div className="text-xs text-gray-500 mb-1">Tours/plein</div>
            <div className="text-2xl font-bold text-agp-accent">{maxLapsPerTank}</div>
          </div>
        </div>

        {/* Minimum stops calculation */}
        <div className="p-4 bg-agp-accent/10 border border-agp-accent/30 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-agp-accent font-medium">Arrets minimum requis</div>
              <div className="text-xs text-gray-400 mt-1">
                Base sur {totalLaps} tours et {maxLapsPerTank} tours/plein
              </div>
            </div>
            <div className="text-4xl font-bold text-agp-accent">
              {Math.ceil(totalLaps / maxLapsPerTank) - 1}
            </div>
          </div>
        </div>
      </div>

      {/* Planned pit stops table */}
      <div className="bg-agp-card border border-agp-border rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">Arrets Planifies</h3>

        <table className="w-full">
          <thead>
            <tr className="text-left text-xs text-gray-500 uppercase tracking-wide">
              <th className="pb-3">Arret</th>
              <th className="pb-3">Tour</th>
              <th className="pb-3">Type</th>
              <th className="pb-3">Carburant</th>
              <th className="pb-3">Pneus</th>
              <th className="pb-3">Duree est.</th>
              <th className="pb-3">Statut</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-agp-border">
            {pitStops.map((stop, idx) => (
              <tr key={idx} className={stop.completed ? 'opacity-50' : ''}>
                <td className="py-3">
                  <span className="w-6 h-6 inline-flex items-center justify-center bg-agp-accent/20 text-agp-accent rounded-full text-sm font-bold">
                    {idx + 1}
                  </span>
                </td>
                <td className="py-3 text-white font-medium">Tour {stop.lap}</td>
                <td className="py-3 text-gray-400 capitalize">{stop.stop_type.replace('_', ' + ')}</td>
                <td className="py-3 text-white">{stop.fuel_to_add > 0 ? `+${stop.fuel_to_add.toFixed(1)}L` : '-'}</td>
                <td className="py-3">
                  {stop.tire_compound ? (
                    <span className={`px-2 py-1 rounded text-xs capitalize ${getCompoundClass(stop.tire_compound)}`}>
                      {stop.tire_compound}
                    </span>
                  ) : '-'}
                </td>
                <td className="py-3 text-gray-400">{stop.estimated_duration}s</td>
                <td className="py-3">
                  {stop.completed ? (
                    <span className="text-xs text-gray-500">Complete</span>
                  ) : (
                    <span className="text-xs text-agp-accent">A venir</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Stints table */}
      <div className="bg-agp-card border border-agp-border rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">Stints Planifies</h3>

        <table className="w-full">
          <thead>
            <tr className="text-left text-xs text-gray-500 uppercase tracking-wide">
              <th className="pb-3">Stint</th>
              <th className="pb-3">Pilote</th>
              <th className="pb-3">Debut</th>
              <th className="pb-3">Fin</th>
              <th className="pb-3">Tours</th>
              <th className="pb-3">Pneus</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-agp-border">
            {stints.map((stint) => (
              <tr key={stint.stint_number}>
                <td className="py-3 text-white font-bold">Stint {stint.stint_number}</td>
                <td className="py-3 text-white">{stint.driver}</td>
                <td className="py-3 text-gray-400">Tour {stint.start_lap}</td>
                <td className="py-3 text-gray-400">Tour {stint.end_lap || '?'}</td>
                <td className="py-3 text-white">{(stint.end_lap || totalLaps) - stint.start_lap}</td>
                <td className="py-3">
                  <span className={`px-2 py-1 rounded text-xs capitalize ${getCompoundClass(stint.tire_compound)}`}>
                    {stint.tire_compound}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

interface DriversViewProps {
  drivers: DriverInfo[]
  stints: Stint[]
  currentStint: number
}

function DriversView({ drivers, stints, currentStint }: DriversViewProps) {
  return (
    <div className="space-y-6">
      {/* Driver cards */}
      <div className="grid grid-cols-2 gap-6">
        {drivers.map((driver) => {
          const driverStints = stints.filter(s => s.driver === driver.name)
          const isActive = stints.find(s => s.stint_number === currentStint)?.driver === driver.name

          return (
            <div
              key={driver.name}
              className={`bg-agp-card border rounded-lg p-6 ${
                isActive ? 'border-agp-accent' : 'border-agp-border'
              }`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className="w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold"
                    style={{ backgroundColor: `${driver.color}33`, color: driver.color }}
                  >
                    {driver.name[0]}
                  </div>
                  <div>
                    <div className="text-white font-bold text-lg">{driver.name}</div>
                    {isActive && (
                      <span className="text-xs text-agp-accent">EN PISTE</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="p-3 bg-black/20 rounded-lg">
                  <div className="text-[10px] text-gray-500 uppercase">Tours</div>
                  <div className="text-xl font-bold text-white">{driver.totalLaps}</div>
                </div>
                <div className="p-3 bg-black/20 rounded-lg">
                  <div className="text-[10px] text-gray-500 uppercase">Temps</div>
                  <div className="text-xl font-bold text-white">{driver.totalTime}</div>
                </div>
                <div className="p-3 bg-black/20 rounded-lg">
                  <div className="text-[10px] text-gray-500 uppercase">Stints</div>
                  <div className="text-xl font-bold text-white">{driverStints.length}</div>
                </div>
              </div>

              {/* Driver's stints */}
              <div className="space-y-2">
                <div className="text-xs text-gray-500 uppercase tracking-wide">Stints assignes</div>
                {driverStints.map((stint) => (
                  <div
                    key={stint.stint_number}
                    className={`p-2 rounded flex items-center justify-between ${
                      stint.stint_number === currentStint
                        ? 'bg-agp-accent/20 border border-agp-accent/50'
                        : 'bg-black/20'
                    }`}
                  >
                    <span className="text-sm text-white">
                      Stint {stint.stint_number}
                    </span>
                    <span className="text-xs text-gray-400">
                      Tours {stint.start_lap} - {stint.end_lap || '?'}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] capitalize ${getCompoundClass(stint.tire_compound)}`}>
                      {stint.tire_compound}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* Driver rotation schedule */}
      <div className="bg-agp-card border border-agp-border rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">Rotation des Pilotes</h3>

        <div className="flex items-center gap-2">
          {stints.map((stint, idx) => (
            <div key={stint.stint_number} className="flex items-center">
              <div
                className={`px-4 py-2 rounded-lg ${
                  stint.stint_number === currentStint
                    ? 'bg-agp-accent text-black'
                    : stint.stint_number < currentStint
                      ? 'bg-gray-700 text-gray-400'
                      : 'bg-agp-border text-white'
                }`}
              >
                <div className="text-xs opacity-70">Stint {stint.stint_number}</div>
                <div className="font-bold">{stint.driver}</div>
              </div>
              {idx < stints.length - 1 && (
                <div className="w-8 h-0.5 bg-agp-border mx-1" />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Utility functions
function getCompoundClass(compound: string): string {
  switch (compound?.toLowerCase()) {
    case 'soft': return 'bg-red-500/20 text-red-400'
    case 'medium': return 'bg-yellow-500/20 text-yellow-400'
    case 'hard': return 'bg-white/20 text-white'
    case 'wet': return 'bg-blue-500/20 text-blue-400'
    case 'intermediate': return 'bg-green-500/20 text-green-400'
    default: return 'bg-gray-500/20 text-gray-400'
  }
}

export default Strategy
