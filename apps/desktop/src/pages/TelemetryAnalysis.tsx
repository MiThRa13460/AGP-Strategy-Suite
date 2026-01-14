import { useState, useCallback } from 'react'

// Types matching Python backend
interface TelemetryPoint {
  timestamp: number
  distance: number
  lap: number
  speed: number
  throttle: number
  brake: number
  steering: number
  g_lat: number
  g_long: number
}

interface CornerAnalysis {
  corner_id: number
  corner_name: string
  corner_type: string
  direction: string
  entry_speed: number
  min_speed: number
  exit_speed: number
  understeer_severity: number
  oversteer_severity: number
  traction_loss_severity: number
  time_loss: number
}

interface LapData {
  lap_number: number
  lap_time: number
  is_valid: boolean
  max_speed: number
  avg_speed: number
  understeer_percentage: number
  oversteer_percentage: number
  corners: CornerAnalysis[]
}

interface BehaviorStats {
  understeer_tendency: number
  oversteer_tendency: number
  balance_score: number
  entry_balance: number
  mid_corner_balance: number
  exit_balance: number
  slow_corner_balance: number
  medium_corner_balance: number
  fast_corner_balance: number
  traction_on_throttle: number
  consistency: number
}

interface SetupRecommendation {
  title: string
  description: string
  priority: number
  category: string
  parameter_changes: Array<{
    parameter: string
    direction: string
    amount: number
  }>
  evidence: string[]
  confidence: number
  data_driven: boolean
}

interface AnalysisResult {
  session: {
    session_id: string
    track_name: string
    car_name: string
    best_lap_time: number
    total_laps: number
  }
  behavior: BehaviorStats
  problem_corners: CornerAnalysis[]
  recommendations: SetupRecommendation[]
  scores: {
    overall: number
    consistency: number
    pace: number
    tire_management: number
  }
}

// Mock analysis result for development
const mockAnalysisResult: AnalysisResult = {
  session: {
    session_id: 'practice_20240114',
    track_name: 'Spa-Francorchamps',
    car_name: 'Porsche 911 GT3 R',
    best_lap_time: 138.456,
    total_laps: 15,
  },
  behavior: {
    understeer_tendency: 35,
    oversteer_tendency: 18,
    balance_score: 42,
    entry_balance: 45,
    mid_corner_balance: 40,
    exit_balance: 55,
    slow_corner_balance: 35,
    medium_corner_balance: 45,
    fast_corner_balance: 50,
    traction_on_throttle: 22,
    consistency: 78,
  },
  problem_corners: [
    {
      corner_id: 1, corner_name: 'La Source', corner_type: 'slow', direction: 'right',
      entry_speed: 85, min_speed: 62, exit_speed: 95, understeer_severity: 45,
      oversteer_severity: 10, traction_loss_severity: 25, time_loss: 0.35,
    },
    {
      corner_id: 8, corner_name: 'Pouhon', corner_type: 'fast', direction: 'left',
      entry_speed: 245, min_speed: 198, exit_speed: 220, understeer_severity: 30,
      oversteer_severity: 15, traction_loss_severity: 5, time_loss: 0.18,
    },
    {
      corner_id: 14, corner_name: 'Blanchimont', corner_type: 'very_fast', direction: 'left',
      entry_speed: 285, min_speed: 268, exit_speed: 275, understeer_severity: 12,
      oversteer_severity: 28, traction_loss_severity: 8, time_loss: 0.22,
    },
  ],
  recommendations: [
    {
      title: 'Reduire le sous-virage',
      description: 'Tendance au sous-virage detectee (35%). Le train avant manque d\'adherence en virage.',
      priority: 2,
      category: 'balance',
      parameter_changes: [
        { parameter: 'Front ARB', direction: 'decrease', amount: 1 },
        { parameter: 'Front Camber', direction: 'increase', amount: 0.2 },
      ],
      evidence: ['Sous-virage: 35%', 'Balance globale: 42/100'],
      confidence: 78,
      data_driven: true,
    },
    {
      title: 'Perte de traction a l\'acceleration',
      description: 'Patinage detecte (22%) lors de l\'acceleration en sortie de virage.',
      priority: 2,
      category: 'traction',
      parameter_changes: [
        { parameter: 'Diff Power Lock', direction: 'decrease', amount: 5 },
      ],
      evidence: ['Traction loss: 22%'],
      confidence: 72,
      data_driven: true,
    },
    {
      title: 'Probleme a La Source',
      description: 'Sous-virage recurrent dans ce virage (slow, right).',
      priority: 3,
      category: 'balance',
      parameter_changes: [
        { parameter: 'Front ARB', direction: 'decrease', amount: 1 },
      ],
      evidence: ['Sous-virage: 45%', 'Perte temps: 0.35s'],
      confidence: 70,
      data_driven: true,
    },
  ],
  scores: {
    overall: 72,
    consistency: 78,
    pace: 68,
    tire_management: 75,
  },
}

export function TelemetryAnalysis() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'corners' | 'recommendations'>('overview')

  const handleFileSelect = useCallback(async () => {
    // In production, this would use Tauri's file dialog
    // For now, simulate file selection
    setSelectedFile('practice_spa_20240114.csv')
    setIsAnalyzing(true)

    // Simulate analysis
    setTimeout(() => {
      setAnalysisResult(mockAnalysisResult)
      setIsAnalyzing(false)
    }, 2000)
  }, [])

  return (
    <div className="min-h-screen bg-agp-bg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Analyse Telemetrie CSV</h1>
          <p className="text-sm text-gray-500">
            Importez vos fichiers CSV pour une analyse approfondie
          </p>
        </div>

        <button
          onClick={handleFileSelect}
          disabled={isAnalyzing}
          className="px-4 py-2 bg-agp-accent text-black rounded-lg font-medium hover:bg-agp-accent/80 disabled:opacity-50 transition-colors"
        >
          {isAnalyzing ? 'Analyse en cours...' : 'Importer CSV'}
        </button>
      </div>

      {/* File info */}
      {selectedFile && (
        <div className="mb-6 p-4 bg-agp-card border border-agp-border rounded-lg">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-agp-accent/20 rounded-lg flex items-center justify-center">
              <span className="text-agp-accent text-xl">📊</span>
            </div>
            <div className="flex-1">
              <div className="text-white font-medium">{selectedFile}</div>
              {analysisResult && (
                <div className="text-sm text-gray-500">
                  {analysisResult.session.track_name} • {analysisResult.session.car_name} • {analysisResult.session.total_laps} tours
                </div>
              )}
            </div>
            {isAnalyzing && (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-agp-accent border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-gray-400">Analyse...</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Analysis results */}
      {analysisResult && !isAnalyzing && (
        <>
          {/* Tabs */}
          <div className="flex gap-2 mb-6">
            {(['overview', 'corners', 'recommendations'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab
                    ? 'bg-agp-accent text-black'
                    : 'bg-agp-card text-gray-400 hover:bg-agp-border'
                }`}
              >
                {tab === 'overview' ? 'Vue Generale' : tab === 'corners' ? 'Analyse Virages' : 'Recommandations'}
              </button>
            ))}
          </div>

          {/* Content */}
          {activeTab === 'overview' && (
            <OverviewTab result={analysisResult} />
          )}
          {activeTab === 'corners' && (
            <CornersTab corners={analysisResult.problem_corners} />
          )}
          {activeTab === 'recommendations' && (
            <RecommendationsTab recommendations={analysisResult.recommendations} />
          )}
        </>
      )}

      {/* Empty state */}
      {!selectedFile && (
        <div className="flex flex-col items-center justify-center h-96 bg-agp-card border border-agp-border rounded-lg">
          <div className="text-6xl mb-4">📈</div>
          <h3 className="text-xl text-white mb-2">Aucun fichier selectionne</h3>
          <p className="text-gray-500 text-center max-w-md mb-4">
            Importez un fichier CSV de telemetrie (MoTeC, rF2, ACC) pour analyser
            votre comportement et recevoir des recommandations de setup.
          </p>
          <button
            onClick={handleFileSelect}
            className="px-6 py-3 bg-agp-accent text-black rounded-lg font-medium hover:bg-agp-accent/80 transition-colors"
          >
            Selectionner un fichier CSV
          </button>
        </div>
      )}
    </div>
  )
}

// Overview Tab Component
function OverviewTab({ result }: { result: AnalysisResult }) {
  const { behavior, scores } = result

  return (
    <div className="space-y-6">
      {/* Scores */}
      <div className="grid grid-cols-4 gap-4">
        <ScoreCard label="Score Global" value={scores.overall} />
        <ScoreCard label="Consistance" value={scores.consistency} />
        <ScoreCard label="Rythme" value={scores.pace} />
        <ScoreCard label="Gestion Pneus" value={scores.tire_management} />
      </div>

      {/* Behavior analysis */}
      <div className="grid grid-cols-2 gap-6">
        {/* Balance visualization */}
        <div className="bg-agp-card border border-agp-border rounded-lg p-6">
          <h3 className="text-sm text-gray-400 mb-4">Equilibre Sous-virage / Survirage</h3>

          <BalanceBar
            label="Global"
            value={behavior.balance_score}
            understeer={behavior.understeer_tendency}
            oversteer={behavior.oversteer_tendency}
          />
          <BalanceBar
            label="Entree virage"
            value={behavior.entry_balance}
          />
          <BalanceBar
            label="Mi-virage"
            value={behavior.mid_corner_balance}
          />
          <BalanceBar
            label="Sortie virage"
            value={behavior.exit_balance}
          />
        </div>

        {/* Corner type balance */}
        <div className="bg-agp-card border border-agp-border rounded-lg p-6">
          <h3 className="text-sm text-gray-400 mb-4">Equilibre par Type de Virage</h3>

          <BalanceBar
            label="Virages lents"
            value={behavior.slow_corner_balance}
          />
          <BalanceBar
            label="Virages moyens"
            value={behavior.medium_corner_balance}
          />
          <BalanceBar
            label="Virages rapides"
            value={behavior.fast_corner_balance}
          />

          <div className="mt-4 pt-4 border-t border-agp-border">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Traction en sortie</span>
              <span className={behavior.traction_on_throttle > 20 ? 'text-agp-warning' : 'text-agp-success'}>
                {behavior.traction_on_throttle.toFixed(0)}% patinage
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Best lap info */}
      <div className="bg-agp-card border border-agp-border rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm text-gray-400">Meilleur Tour</h3>
            <div className="text-3xl font-bold text-agp-accent font-mono mt-1">
              {formatLapTime(result.session.best_lap_time)}
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">Consistance</div>
            <div className="text-xl font-bold text-white">{behavior.consistency.toFixed(0)}%</div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Corners Tab Component
function CornersTab({ corners }: { corners: CornerAnalysis[] }) {
  return (
    <div className="space-y-4">
      <div className="bg-agp-card border border-agp-border rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">Virages Problematiques</h3>
        <p className="text-sm text-gray-500 mb-6">
          Ces virages montrent des problemes recurrents sur plusieurs tours.
        </p>

        <div className="space-y-4">
          {corners.map((corner) => (
            <CornerCard key={corner.corner_id} corner={corner} />
          ))}
        </div>
      </div>
    </div>
  )
}

function CornerCard({ corner }: { corner: CornerAnalysis }) {
  const mainIssue = corner.understeer_severity > corner.oversteer_severity
    ? { type: 'Sous-virage', severity: corner.understeer_severity, color: 'agp-danger' }
    : { type: 'Survirage', severity: corner.oversteer_severity, color: 'agp-warning' }

  return (
    <div className="p-4 bg-black/30 rounded-lg border border-agp-border">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-agp-accent/20 flex items-center justify-center">
            <span className="text-agp-accent font-bold">{corner.corner_id}</span>
          </div>
          <div>
            <div className="text-white font-medium">{corner.corner_name}</div>
            <div className="text-xs text-gray-500 capitalize">
              {corner.corner_type} • {corner.direction}
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className={`text-lg font-bold text-${mainIssue.color}`}>
            {mainIssue.severity.toFixed(0)}%
          </div>
          <div className="text-xs text-gray-500">{mainIssue.type}</div>
        </div>
      </div>

      {/* Speed profile */}
      <div className="grid grid-cols-3 gap-4 mb-3">
        <div className="text-center">
          <div className="text-xs text-gray-500">Entree</div>
          <div className="text-white font-mono">{corner.entry_speed.toFixed(0)} km/h</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500">Minimum</div>
          <div className="text-agp-accent font-mono font-bold">{corner.min_speed.toFixed(0)} km/h</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500">Sortie</div>
          <div className="text-white font-mono">{corner.exit_speed.toFixed(0)} km/h</div>
        </div>
      </div>

      {/* Issue bars */}
      <div className="space-y-2">
        <IssueBar label="Sous-virage" value={corner.understeer_severity} color="#ff3366" />
        <IssueBar label="Survirage" value={corner.oversteer_severity} color="#ffaa00" />
        <IssueBar label="Patinage" value={corner.traction_loss_severity} color="#ff8844" />
      </div>

      {/* Time loss */}
      <div className="mt-3 pt-3 border-t border-agp-border flex justify-between">
        <span className="text-sm text-gray-500">Perte de temps estimee</span>
        <span className="text-sm font-bold text-agp-danger">+{corner.time_loss.toFixed(2)}s</span>
      </div>
    </div>
  )
}

// Recommendations Tab Component
function RecommendationsTab({ recommendations }: { recommendations: SetupRecommendation[] }) {
  const priorityColors = {
    1: 'border-agp-danger bg-agp-danger/10',
    2: 'border-agp-warning bg-agp-warning/10',
    3: 'border-agp-accent bg-agp-accent/10',
    4: 'border-gray-600 bg-gray-600/10',
    5: 'border-gray-700 bg-gray-700/10',
  }

  return (
    <div className="space-y-4">
      {recommendations.map((rec, idx) => (
        <div
          key={idx}
          className={`p-6 rounded-lg border ${priorityColors[rec.priority as keyof typeof priorityColors] || priorityColors[3]}`}
        >
          <div className="flex items-start justify-between mb-3">
            <div>
              <h4 className="text-white font-bold">{rec.title}</h4>
              <p className="text-sm text-gray-400 mt-1">{rec.description}</p>
            </div>
            <div className="flex items-center gap-2">
              {rec.data_driven && (
                <span className="text-[10px] px-2 py-1 bg-agp-accent/20 text-agp-accent rounded">
                  DATA-DRIVEN
                </span>
              )}
              <span className="text-sm text-gray-500">
                {rec.confidence.toFixed(0)}% confiance
              </span>
            </div>
          </div>

          {/* Parameter changes */}
          {rec.parameter_changes.length > 0 && (
            <div className="mt-4 p-3 bg-black/30 rounded-lg">
              <div className="text-xs text-gray-500 uppercase tracking-wide mb-2">
                Modifications suggerees
              </div>
              <div className="space-y-2">
                {rec.parameter_changes.map((change, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="text-white">{change.parameter}</span>
                    <span className={`font-mono ${
                      change.direction === 'increase' ? 'text-agp-success' : 'text-agp-danger'
                    }`}>
                      {change.direction === 'increase' ? '+' : '-'}{change.amount}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Evidence */}
          <div className="mt-3 flex flex-wrap gap-2">
            {rec.evidence.map((ev, i) => (
              <span key={i} className="text-xs px-2 py-1 bg-black/30 text-gray-400 rounded">
                {ev}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// Helper Components
function ScoreCard({ label, value }: { label: string; value: number }) {
  const getColor = (v: number) => {
    if (v >= 80) return 'text-agp-success'
    if (v >= 60) return 'text-agp-accent'
    if (v >= 40) return 'text-agp-warning'
    return 'text-agp-danger'
  }

  return (
    <div className="bg-agp-card border border-agp-border rounded-lg p-4">
      <div className="text-xs text-gray-500 uppercase tracking-wide">{label}</div>
      <div className={`text-3xl font-bold mt-1 ${getColor(value)}`}>
        {value.toFixed(0)}
      </div>
      <div className="h-1 bg-gray-800 rounded-full mt-2 overflow-hidden">
        <div
          className={`h-full rounded-full ${getColor(value).replace('text-', 'bg-')}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  )
}

interface BalanceBarProps {
  label: string
  value: number
  understeer?: number
  oversteer?: number
}

function BalanceBar({ label, value, understeer, oversteer }: BalanceBarProps) {
  // value: 0 = full understeer, 50 = neutral, 100 = full oversteer
  const position = value

  return (
    <div className="mb-4">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-agp-danger">Sous-virage{understeer !== undefined && ` (${understeer.toFixed(0)}%)`}</span>
        <span className="text-gray-400">{label}</span>
        <span className="text-agp-warning">Survirage{oversteer !== undefined && ` (${oversteer.toFixed(0)}%)`}</span>
      </div>
      <div className="h-3 bg-gradient-to-r from-agp-danger via-gray-600 to-agp-warning rounded-full relative">
        {/* Center marker */}
        <div className="absolute top-0 bottom-0 left-1/2 w-0.5 bg-white/50" />
        {/* Position indicator */}
        <div
          className="absolute top-0 bottom-0 w-2 bg-white rounded-full shadow-lg transition-all"
          style={{ left: `calc(${position}% - 4px)` }}
        />
      </div>
    </div>
  )
}

function IssueBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 w-20">{label}</span>
      <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${value}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs tabular-nums w-8 text-right" style={{ color }}>
        {value.toFixed(0)}%
      </span>
    </div>
  )
}

function formatLapTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toFixed(3).padStart(6, '0')}`
}

export default TelemetryAnalysis
