interface SetupData {
  name: string
  suspension?: {
    front_ride_height_mm: number
    rear_ride_height_mm: number
    rake_mm: number
    front_arb: number
    rear_arb: number
    front_camber_deg: number
    rear_camber_deg: number
  }
  differential?: {
    power_lock: number
    coast_lock: number
    preload: number
  }
  brakes?: {
    bias_front: number
    pressure: number
  }
  aero?: {
    front_wing: number
    rear_wing: number
  }
  tire_compound: string
  fuel_load: number
}

interface SetupComparisonProps {
  setupA: SetupData | null
  setupB: SetupData | null
}

export function SetupComparison({ setupA, setupB }: SetupComparisonProps) {
  if (!setupA && !setupB) {
    return (
      <div className="bg-agp-card border border-agp-border rounded-lg p-6 text-center">
        <div className="text-3xl mb-2">📊</div>
        <p className="text-gray-500">Charge deux setups pour les comparer</p>
      </div>
    )
  }

  return (
    <div className="bg-agp-card border border-agp-border rounded-lg p-6">
      <h3 className="text-sm text-gray-400 mb-4">Comparaison de Setups</h3>

      {/* Header with setup names */}
      <div className="grid grid-cols-3 gap-4 mb-4 pb-2 border-b border-agp-border">
        <div className="text-xs text-gray-500">Parametre</div>
        <div className="text-center">
          <span className="text-sm font-medium text-agp-accent">
            {setupA?.name || 'Setup A'}
          </span>
        </div>
        <div className="text-center">
          <span className="text-sm font-medium text-agp-accent-blue">
            {setupB?.name || 'Setup B'}
          </span>
        </div>
      </div>

      {/* Comparison rows */}
      <div className="space-y-1">
        {/* General */}
        <SectionHeader title="General" />
        <ComparisonRow
          label="Compound"
          valueA={setupA?.tire_compound}
          valueB={setupB?.tire_compound}
        />
        <ComparisonRow
          label="Carburant"
          valueA={setupA?.fuel_load}
          valueB={setupB?.fuel_load}
          unit="L"
        />

        {/* Suspension */}
        <SectionHeader title="Suspension" />
        <ComparisonRow
          label="Hauteur AV"
          valueA={setupA?.suspension?.front_ride_height_mm}
          valueB={setupB?.suspension?.front_ride_height_mm}
          unit="mm"
          precision={0}
        />
        <ComparisonRow
          label="Hauteur AR"
          valueA={setupA?.suspension?.rear_ride_height_mm}
          valueB={setupB?.suspension?.rear_ride_height_mm}
          unit="mm"
          precision={0}
        />
        <ComparisonRow
          label="Rake"
          valueA={setupA?.suspension?.rake_mm}
          valueB={setupB?.suspension?.rake_mm}
          unit="mm"
          precision={1}
        />
        <ComparisonRow
          label="ARB Avant"
          valueA={setupA?.suspension?.front_arb}
          valueB={setupB?.suspension?.front_arb}
        />
        <ComparisonRow
          label="ARB Arriere"
          valueA={setupA?.suspension?.rear_arb}
          valueB={setupB?.suspension?.rear_arb}
        />
        <ComparisonRow
          label="Carrossage AV"
          valueA={setupA?.suspension?.front_camber_deg}
          valueB={setupB?.suspension?.front_camber_deg}
          unit=""
          precision={1}
        />
        <ComparisonRow
          label="Carrossage AR"
          valueA={setupA?.suspension?.rear_camber_deg}
          valueB={setupB?.suspension?.rear_camber_deg}
          unit=""
          precision={1}
        />

        {/* Differential */}
        <SectionHeader title="Differentiel" />
        <ComparisonRow
          label="Power Lock"
          valueA={setupA?.differential?.power_lock}
          valueB={setupB?.differential?.power_lock}
          unit="%"
          precision={0}
        />
        <ComparisonRow
          label="Coast Lock"
          valueA={setupA?.differential?.coast_lock}
          valueB={setupB?.differential?.coast_lock}
          unit="%"
          precision={0}
        />
        <ComparisonRow
          label="Preload"
          valueA={setupA?.differential?.preload}
          valueB={setupB?.differential?.preload}
          unit="Nm"
          precision={0}
        />

        {/* Brakes */}
        <SectionHeader title="Freins" />
        <ComparisonRow
          label="Repartition"
          valueA={setupA?.brakes?.bias_front}
          valueB={setupB?.brakes?.bias_front}
          unit="%"
          precision={1}
        />
        <ComparisonRow
          label="Pression"
          valueA={setupA?.brakes?.pressure}
          valueB={setupB?.brakes?.pressure}
          unit="%"
          precision={0}
        />

        {/* Aero */}
        <SectionHeader title="Aero" />
        <ComparisonRow
          label="Aileron AV"
          valueA={setupA?.aero?.front_wing}
          valueB={setupB?.aero?.front_wing}
        />
        <ComparisonRow
          label="Aileron AR"
          valueA={setupA?.aero?.rear_wing}
          valueB={setupB?.aero?.rear_wing}
        />
      </div>
    </div>
  )
}

function SectionHeader({ title }: { title: string }) {
  return (
    <div className="pt-3 pb-1">
      <span className="text-xs text-gray-600 uppercase tracking-wide">{title}</span>
    </div>
  )
}

interface ComparisonRowProps {
  label: string
  valueA: number | string | undefined
  valueB: number | string | undefined
  unit?: string
  precision?: number
}

function ComparisonRow({ label, valueA, valueB, unit = '', precision = 0 }: ComparisonRowProps) {
  const formatValue = (value: number | string | undefined): string => {
    if (value === undefined || value === null) return '-'
    if (typeof value === 'string') return value
    return precision > 0 ? value.toFixed(precision) : Math.round(value).toString()
  }

  const formattedA = formatValue(valueA)
  const formattedB = formatValue(valueB)

  // Calculate difference for numeric values
  let diff: number | null = null
  let diffColor = 'text-gray-600'

  if (typeof valueA === 'number' && typeof valueB === 'number') {
    diff = valueB - valueA
    if (Math.abs(diff) > 0.01) {
      diffColor = diff > 0 ? 'text-agp-accent' : 'text-agp-danger'
    }
  }

  const isDifferent = formattedA !== formattedB

  return (
    <div className={`grid grid-cols-3 gap-4 py-1 px-2 rounded ${isDifferent ? 'bg-agp-accent/5' : ''}`}>
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-center text-sm text-white tabular-nums">
        {formattedA}{unit && formattedA !== '-' ? unit : ''}
      </div>
      <div className="text-center text-sm tabular-nums">
        <span className={isDifferent ? 'text-agp-accent-blue' : 'text-white'}>
          {formattedB}{unit && formattedB !== '-' ? unit : ''}
        </span>
        {diff !== null && Math.abs(diff) > 0.01 && (
          <span className={`text-[10px] ml-1 ${diffColor}`}>
            ({diff > 0 ? '+' : ''}{precision > 0 ? diff.toFixed(precision) : Math.round(diff)})
          </span>
        )}
      </div>
    </div>
  )
}

export default SetupComparison
