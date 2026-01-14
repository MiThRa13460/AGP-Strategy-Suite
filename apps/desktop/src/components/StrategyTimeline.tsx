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

interface StrategyTimelineProps {
  totalLaps: number
  currentLap: number
  pitStops: PitStop[]
  stints: Stint[]
  currentStint: number
}

export function StrategyTimeline({
  totalLaps,
  currentLap,
  pitStops,
  stints,
  currentStint,
}: StrategyTimelineProps) {
  const progress = (currentLap / totalLaps) * 100

  return (
    <div className="bg-agp-card border border-agp-border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm text-gray-400">Timeline Strategie</h3>
        <div className="text-sm">
          <span className="text-white font-bold">Tour {currentLap}</span>
          <span className="text-gray-500"> / {totalLaps}</span>
        </div>
      </div>

      {/* Main timeline */}
      <div className="relative mb-6">
        {/* Background track */}
        <div className="h-12 bg-black/30 rounded-lg border border-agp-border relative overflow-hidden">
          {/* Progress */}
          <div
            className="absolute top-0 bottom-0 left-0 bg-agp-accent/20"
            style={{ width: `${progress}%` }}
          />

          {/* Stints */}
          {stints.map((stint, idx) => {
            const startPct = (stint.start_lap / totalLaps) * 100
            const endPct = ((stint.end_lap || totalLaps) / totalLaps) * 100
            const width = endPct - startPct
            const color = getCompoundColor(stint.tire_compound)
            const isCurrent = stint.stint_number === currentStint

            return (
              <div
                key={idx}
                className={`absolute top-1 bottom-1 rounded transition-all ${isCurrent ? 'ring-2 ring-white' : ''}`}
                style={{
                  left: `${startPct}%`,
                  width: `${width}%`,
                  backgroundColor: `${color}44`,
                  borderLeft: `3px solid ${color}`,
                }}
                title={`Stint ${stint.stint_number}: ${stint.driver}`}
              >
                <div className="px-2 py-1 text-[10px] text-white truncate">
                  {stint.driver}
                </div>
              </div>
            )
          })}

          {/* Pit stops markers */}
          {pitStops.map((stop, idx) => {
            const position = (stop.lap / totalLaps) * 100
            return (
              <div
                key={idx}
                className={`absolute top-0 bottom-0 w-0.5 ${stop.completed ? 'bg-gray-500' : 'bg-agp-warning'}`}
                style={{ left: `${position}%` }}
              >
                <div
                  className={`absolute -top-1 -left-2 w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${
                    stop.completed ? 'bg-gray-600' : 'bg-agp-warning'
                  }`}
                >
                  P
                </div>
              </div>
            )
          })}

          {/* Current position marker */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-white z-10"
            style={{ left: `${progress}%` }}
          >
            <div className="absolute -top-3 -left-3 w-6 h-6 rounded-full bg-white flex items-center justify-center">
              <span className="text-black text-[10px] font-bold">▼</span>
            </div>
          </div>
        </div>

        {/* Lap markers */}
        <div className="flex justify-between mt-2 text-[10px] text-gray-600">
          <span>0</span>
          <span>{Math.round(totalLaps * 0.25)}</span>
          <span>{Math.round(totalLaps * 0.5)}</span>
          <span>{Math.round(totalLaps * 0.75)}</span>
          <span>{totalLaps}</span>
        </div>
      </div>

      {/* Pit stops list */}
      <div className="space-y-2">
        <h4 className="text-xs text-gray-500 uppercase tracking-wide">Arrets planifies</h4>
        {pitStops.length === 0 ? (
          <p className="text-sm text-gray-600">Aucun arret planifie</p>
        ) : (
          pitStops.map((stop, idx) => (
            <PitStopItem
              key={idx}
              stop={stop}
              index={idx + 1}
              isNext={!stop.completed && pitStops.filter(s => !s.completed).indexOf(stop) === 0}
              currentLap={currentLap}
            />
          ))
        )}
      </div>

      {/* Compound legend */}
      <div className="mt-4 pt-4 border-t border-agp-border">
        <div className="flex flex-wrap gap-3 text-xs">
          {['soft', 'medium', 'hard', 'wet', 'intermediate'].map(compound => (
            <div key={compound} className="flex items-center gap-1">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: getCompoundColor(compound) }}
              />
              <span className="text-gray-500 capitalize">{compound}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

interface PitStopItemProps {
  stop: PitStop
  index: number
  isNext: boolean
  currentLap: number
}

function PitStopItem({ stop, index, isNext, currentLap }: PitStopItemProps) {
  const lapsUntil = stop.lap - currentLap

  return (
    <div
      className={`p-3 rounded-lg border transition-all ${
        stop.completed
          ? 'bg-black/20 border-gray-700 opacity-60'
          : isNext
            ? 'bg-agp-accent/10 border-agp-accent'
            : 'bg-black/20 border-agp-border'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            stop.completed ? 'bg-gray-700' : isNext ? 'bg-agp-accent' : 'bg-agp-border'
          }`}>
            <span className={`text-sm font-bold ${stop.completed || isNext ? 'text-black' : 'text-white'}`}>
              {index}
            </span>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-white font-medium">Tour {stop.lap}</span>
              {stop.tire_compound && (
                <span
                  className="text-[10px] px-1.5 py-0.5 rounded capitalize"
                  style={{
                    backgroundColor: `${getCompoundColor(stop.tire_compound)}33`,
                    color: getCompoundColor(stop.tire_compound),
                  }}
                >
                  {stop.tire_compound}
                </span>
              )}
            </div>
            <div className="text-xs text-gray-500">
              {stop.fuel_to_add > 0 && `+${stop.fuel_to_add.toFixed(1)}L`}
              {stop.fuel_to_add > 0 && stop.tire_compound && ' + '}
              {stop.tire_compound && 'Pneus'}
              {' • '}{stop.estimated_duration.toFixed(0)}s
            </div>
          </div>
        </div>

        <div className="text-right">
          {stop.completed ? (
            <span className="text-xs text-gray-500">Complete</span>
          ) : (
            <div>
              <div className={`text-lg font-bold ${isNext ? 'text-agp-accent' : 'text-white'}`}>
                {lapsUntil > 0 ? `${lapsUntil}` : 'NOW'}
              </div>
              <div className="text-[10px] text-gray-500">
                {lapsUntil > 0 ? 'tours' : ''}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function getCompoundColor(compound: string): string {
  switch (compound?.toLowerCase()) {
    case 'soft': return '#ff3366'
    case 'medium': return '#ffaa00'
    case 'hard': return '#ffffff'
    case 'wet': return '#00aaff'
    case 'intermediate': return '#00ff88'
    default: return '#888888'
  }
}

export default StrategyTimeline
