interface ParameterRecommendation {
  parameter: string
  current: any
  recommended: any
  direction: string
  amount: string
  confidence: number
  explanation: string
}

interface Diagnostic {
  id: string
  title: string
  description: string
  severity: 'critical' | 'warning' | 'info' | 'success'
  category: string
  problem_type: string | null
  corner_phase: string | null
  confidence: number
  priority: number
  recommendations: ParameterRecommendation[]
  affected_parameters: string[]
}

interface DiagnosticCardProps {
  diagnostic: Diagnostic
  onApplyRecommendation?: (param: string, value: any) => void
}

export function DiagnosticCard({ diagnostic, onApplyRecommendation }: DiagnosticCardProps) {
  const severityConfig = getSeverityConfig(diagnostic.severity)
  const phaseLabel = getPhaseLabel(diagnostic.corner_phase)

  return (
    <div
      className="bg-agp-card border rounded-lg p-4 transition-all hover:border-opacity-100"
      style={{
        borderColor: `${severityConfig.color}44`,
        background: `linear-gradient(135deg, ${severityConfig.color}08, transparent)`
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{severityConfig.icon}</span>
          <div>
            <h4 className="font-medium text-white">{diagnostic.title}</h4>
            {phaseLabel && (
              <span className="text-xs text-gray-500">Phase: {phaseLabel}</span>
            )}
          </div>
        </div>
        <SeverityBadge severity={diagnostic.severity} />
      </div>

      {/* Description */}
      <p className="text-sm text-gray-400 mb-4">
        {diagnostic.description}
      </p>

      {/* Recommendations */}
      {diagnostic.recommendations.length > 0 && (
        <div className="space-y-2">
          <h5 className="text-xs text-gray-500 uppercase tracking-wide">Recommandations</h5>
          {diagnostic.recommendations.map((rec, index) => (
            <RecommendationItem
              key={index}
              recommendation={rec}
              onApply={onApplyRecommendation}
            />
          ))}
        </div>
      )}

      {/* Confidence */}
      <div className="mt-3 pt-3 border-t border-agp-border flex items-center justify-between">
        <span className="text-xs text-gray-500">
          Confiance: {Math.round(diagnostic.confidence * 100)}%
        </span>
        <span className="text-xs text-gray-600">
          Priorite: {diagnostic.priority}
        </span>
      </div>
    </div>
  )
}

interface RecommendationItemProps {
  recommendation: ParameterRecommendation
  onApply?: (param: string, value: any) => void
}

function RecommendationItem({ recommendation, onApply }: RecommendationItemProps) {
  const { parameter, current, recommended, direction, amount, confidence, explanation } = recommendation

  const directionIcon = direction === 'increase' ? '↑' : direction === 'decrease' ? '↓' : '↔'
  const directionColor = direction === 'increase' ? 'text-agp-accent' : direction === 'decrease' ? 'text-agp-danger' : 'text-yellow-500'

  return (
    <div className="p-2 rounded bg-black/20 border border-agp-border/50">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className={`text-lg ${directionColor}`}>{directionIcon}</span>
          <span className="text-sm text-white font-medium">{parameter}</span>
        </div>
        <span className="text-xs text-agp-accent">{amount}</span>
      </div>

      <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
        <span>{current}</span>
        <span className="text-gray-600">→</span>
        <span className={directionColor}>{recommended}</span>
      </div>

      {explanation && (
        <p className="text-[10px] text-gray-600 mt-1">{explanation}</p>
      )}

      {onApply && (
        <button
          onClick={() => onApply(parameter, recommended)}
          className="mt-2 text-xs px-2 py-1 rounded bg-agp-accent/20 text-agp-accent hover:bg-agp-accent/30 transition-colors"
        >
          Appliquer
        </button>
      )}
    </div>
  )
}

function SeverityBadge({ severity }: { severity: string }) {
  const config = getSeverityConfig(severity)

  return (
    <span
      className="text-[10px] px-2 py-0.5 rounded-full font-medium"
      style={{ backgroundColor: `${config.color}22`, color: config.color }}
    >
      {config.label}
    </span>
  )
}

function getSeverityConfig(severity: string): { icon: string; color: string; label: string } {
  switch (severity) {
    case 'critical':
      return { icon: '🔴', color: '#ff3366', label: 'Critique' }
    case 'warning':
      return { icon: '🟡', color: '#ffaa00', label: 'Attention' }
    case 'info':
      return { icon: '🔵', color: '#00aaff', label: 'Info' }
    case 'success':
      return { icon: '🟢', color: '#00ff88', label: 'OK' }
    default:
      return { icon: '⚪', color: '#666666', label: 'Unknown' }
  }
}

function getPhaseLabel(phase: string | null): string | null {
  if (!phase) return null

  const labels: Record<string, string> = {
    'braking': 'Freinage',
    'entry': 'Entree',
    'mid': 'Milieu',
    'exit': 'Sortie',
    'acceleration': 'Acceleration',
    'straight': 'Ligne droite',
  }

  return labels[phase] || phase
}

export default DiagnosticCard
