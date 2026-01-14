interface Recommendation {
  parameter: string
  direction: string
  value: string | null
  reason: string
  priority: number
  side_effects: string[]
  confidence: number
}

interface RecommendationCardProps {
  recommendations: Recommendation[]
  onRequestRecommendations?: () => void
}

export function RecommendationCard({ recommendations, onRequestRecommendations }: RecommendationCardProps) {
  return (
    <div className="bg-agp-card border border-agp-border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm text-gray-400">Recommandations</h3>
        {onRequestRecommendations && (
          <button
            onClick={onRequestRecommendations}
            className="text-xs text-agp-accent hover:text-agp-accent-blue transition-colors"
          >
            Actualiser
          </button>
        )}
      </div>

      {recommendations.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-3xl mb-2">🔍</div>
          <p className="text-sm">Roule quelques tours pour recevoir des recommandations</p>
        </div>
      ) : (
        <div className="space-y-3">
          {recommendations.slice(0, 5).map((rec, index) => (
            <RecommendationItem key={index} recommendation={rec} index={index} />
          ))}
        </div>
      )}
    </div>
  )
}

interface RecommendationItemProps {
  recommendation: Recommendation
  index: number
}

function RecommendationItem({ recommendation, index }: RecommendationItemProps) {
  const { parameter, direction, value, reason, priority, side_effects, confidence } = recommendation

  const priorityColor = getPriorityColor(priority)
  const directionIcon = direction === 'increase' ? '↑' : '↓'
  const directionText = direction === 'increase' ? 'Augmenter' : 'Diminuer'

  return (
    <div
      className="p-3 rounded-lg border transition-all hover:border-agp-accent/50"
      style={{ borderColor: `${priorityColor}33`, background: `${priorityColor}08` }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span
            className="text-lg"
            style={{ color: priorityColor }}
          >
            {directionIcon}
          </span>
          <div>
            <div className="font-medium text-white">
              {directionText} {parameter}
            </div>
            {value && (
              <div className="text-xs text-agp-accent">
                → {value}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <ConfidenceBadge confidence={confidence} />
          <PriorityBadge priority={priority} />
        </div>
      </div>

      <p className="mt-2 text-xs text-gray-400">
        {reason}
      </p>

      {side_effects.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {side_effects.map((effect, i) => (
            <span
              key={i}
              className="text-[10px] px-1.5 py-0.5 rounded bg-agp-warning/10 text-agp-warning"
            >
              ⚠️ {effect}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100)
  const color = confidence > 0.7 ? 'text-agp-accent' : confidence > 0.4 ? 'text-agp-warning' : 'text-gray-500'

  return (
    <span className={`text-[10px] ${color}`}>
      {pct}%
    </span>
  )
}

function PriorityBadge({ priority }: { priority: number }) {
  const color = getPriorityColor(priority)
  const label = priority <= 3 ? 'Urgent' : priority <= 6 ? 'Important' : 'Mineur'

  return (
    <span
      className="text-[10px] px-1.5 py-0.5 rounded"
      style={{ backgroundColor: `${color}22`, color }}
    >
      {label}
    </span>
  )
}

function getPriorityColor(priority: number): string {
  if (priority <= 3) return '#ff3366'   // Red - urgent
  if (priority <= 6) return '#ffaa00'   // Yellow - important
  return '#00ff88'                       // Green - minor
}

export default RecommendationCard
