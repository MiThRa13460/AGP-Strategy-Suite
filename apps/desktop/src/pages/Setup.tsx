import { useState, useRef } from 'react'
import { DiagnosticCard } from '../components/DiagnosticCard'
import { SetupComparison } from '../components/SetupComparison'

interface SetupData {
  id: string
  name: string
  car_id: string
  track_id: string
  created_at: string
  tire_compound: string
  fuel_load: number
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
  recommendations: any[]
  affected_parameters: string[]
}

export function SetupPage() {
  const [currentSetup, setCurrentSetup] = useState<SetupData | null>(null)
  const [compareSetup, setCompareSetup] = useState<SetupData | null>(null)
  const [diagnostics, setDiagnostics] = useState<Diagnostic[]>([])
  const [driverFeedback, setDriverFeedback] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [activeTab, setActiveTab] = useState<'analysis' | 'compare'>('analysis')

  const fileInputRef = useRef<HTMLInputElement>(null)
  const compareInputRef = useRef<HTMLInputElement>(null)

  const handleLoadSetup = async (file: File, isCompare: boolean = false) => {
    // In production, this would call the Python backend to parse the file
    // For now, we'll create a mock setup
    const mockSetup: SetupData = {
      id: crypto.randomUUID(),
      name: file.name.replace('.svm', ''),
      car_id: 'Unknown',
      track_id: 'Unknown',
      created_at: new Date().toISOString(),
      tire_compound: 'Medium',
      fuel_load: 60,
      suspension: {
        front_ride_height_mm: 30,
        rear_ride_height_mm: 45,
        rake_mm: 15,
        front_arb: 5,
        rear_arb: 7,
        front_camber_deg: -3.2,
        rear_camber_deg: -2.1,
      },
      differential: {
        power_lock: 50,
        coast_lock: 40,
        preload: 50,
      },
      brakes: {
        bias_front: 56,
        pressure: 90,
      },
      aero: {
        front_wing: 12,
        rear_wing: 18,
      },
    }

    if (isCompare) {
      setCompareSetup(mockSetup)
    } else {
      setCurrentSetup(mockSetup)
      setDiagnostics([]) // Clear diagnostics when loading new setup
    }
  }

  const handleAnalyze = async () => {
    if (!currentSetup || !driverFeedback.trim()) return

    setIsAnalyzing(true)

    // Simulate API call to Python backend
    // In production, this would send the setup and feedback to the rule engine
    setTimeout(() => {
      const mockDiagnostics: Diagnostic[] = []

      const feedback = driverFeedback.toLowerCase()

      if (feedback.includes('understeer') || feedback.includes('sous-virage') || feedback.includes('push')) {
        mockDiagnostics.push({
          id: crypto.randomUUID(),
          title: 'Understeer Detected',
          description: 'Based on your feedback, the car is pushing through corners. This is typically caused by front grip issues.',
          severity: 'warning',
          category: 'balance',
          problem_type: 'understeer_entry',
          corner_phase: 'entry',
          confidence: 0.85,
          priority: 1,
          recommendations: [
            {
              parameter: 'Front ARB',
              current: currentSetup.suspension?.front_arb,
              recommended: Math.max(0, (currentSetup.suspension?.front_arb || 5) - 2),
              direction: 'decrease',
              amount: '-2 clicks',
              confidence: 0.85,
              explanation: 'Softer front ARB increases mechanical grip on entry',
            },
            {
              parameter: 'Brake Bias',
              current: `${currentSetup.brakes?.bias_front}%`,
              recommended: `${Math.max(50, (currentSetup.brakes?.bias_front || 56) - 2)}%`,
              direction: 'decrease',
              amount: '-2%',
              confidence: 0.8,
              explanation: 'More rear braking rotates the car on entry',
            },
          ],
          affected_parameters: ['Front ARB', 'Brake Bias'],
        })
      }

      if (feedback.includes('oversteer') || feedback.includes('survirage') || feedback.includes('loose')) {
        mockDiagnostics.push({
          id: crypto.randomUUID(),
          title: 'Oversteer Detected',
          description: 'The rear of the car is unstable and slides. This needs to be addressed for consistent lap times.',
          severity: 'warning',
          category: 'balance',
          problem_type: 'oversteer_exit',
          corner_phase: 'exit',
          confidence: 0.82,
          priority: 2,
          recommendations: [
            {
              parameter: 'Diff Power Lock',
              current: `${currentSetup.differential?.power_lock}%`,
              recommended: `${Math.max(20, (currentSetup.differential?.power_lock || 50) - 10)}%`,
              direction: 'decrease',
              amount: '-10%',
              confidence: 0.85,
              explanation: 'Lower power lock reduces wheelspin and snap oversteer',
            },
            {
              parameter: 'Rear Wing',
              current: currentSetup.aero?.rear_wing,
              recommended: Math.min(40, (currentSetup.aero?.rear_wing || 18) + 2),
              direction: 'increase',
              amount: '+2',
              confidence: 0.7,
              explanation: 'More rear downforce increases rear stability',
            },
          ],
          affected_parameters: ['Diff Power Lock', 'Rear Wing'],
        })
      }

      if (feedback.includes('wheelspin') || feedback.includes('patinage') || feedback.includes('traction')) {
        mockDiagnostics.push({
          id: crypto.randomUUID(),
          title: 'Excessive Wheelspin',
          description: 'The rear wheels are spinning too much under acceleration, reducing exit speed.',
          severity: 'warning',
          category: 'traction',
          problem_type: 'wheelspin',
          corner_phase: 'acceleration',
          confidence: 0.9,
          priority: 1,
          recommendations: [
            {
              parameter: 'Traction Control',
              current: 0,
              recommended: 2,
              direction: 'increase',
              amount: '+2',
              confidence: 0.95,
              explanation: 'TC is the most effective way to manage wheelspin',
            },
            {
              parameter: 'Diff Power Lock',
              current: `${currentSetup.differential?.power_lock}%`,
              recommended: `${Math.max(20, (currentSetup.differential?.power_lock || 50) - 15)}%`,
              direction: 'decrease',
              amount: '-15%',
              confidence: 0.9,
              explanation: 'Lower power lock reduces aggressive diff behavior',
            },
          ],
          affected_parameters: ['Traction Control', 'Diff Power Lock'],
        })
      }

      if (feedback.includes('blocage') || feedback.includes('lock')) {
        mockDiagnostics.push({
          id: crypto.randomUUID(),
          title: 'Brake Lockup',
          description: 'Wheels are locking under braking, causing flat spots and reduced control.',
          severity: 'critical',
          category: 'braking',
          problem_type: 'front_lockup',
          corner_phase: 'braking',
          confidence: 0.88,
          priority: 1,
          recommendations: [
            {
              parameter: 'Brake Bias',
              current: `${currentSetup.brakes?.bias_front}%`,
              recommended: `${Math.max(50, (currentSetup.brakes?.bias_front || 56) - 3)}%`,
              direction: 'decrease',
              amount: '-3%',
              confidence: 0.9,
              explanation: 'Less front bias prevents front lockup',
            },
          ],
          affected_parameters: ['Brake Bias'],
        })
      }

      // If no specific issues found, add a generic success
      if (mockDiagnostics.length === 0) {
        mockDiagnostics.push({
          id: crypto.randomUUID(),
          title: 'Setup Analysis Complete',
          description: 'No specific issues detected based on your feedback. Consider providing more details about the car behavior.',
          severity: 'info',
          category: 'balance',
          problem_type: null,
          corner_phase: null,
          confidence: 0.5,
          priority: 10,
          recommendations: [],
          affected_parameters: [],
        })
      }

      setDiagnostics(mockDiagnostics)
      setIsAnalyzing(false)
    }, 1500)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Setup Engineering</h2>
          <p className="text-sm text-gray-500">Analyse et optimise ton setup rF2</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('analysis')}
            className={`px-4 py-2 text-sm rounded-lg transition-all ${
              activeTab === 'analysis'
                ? 'bg-agp-accent/20 text-agp-accent'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            Analyse
          </button>
          <button
            onClick={() => setActiveTab('compare')}
            className={`px-4 py-2 text-sm rounded-lg transition-all ${
              activeTab === 'compare'
                ? 'bg-agp-accent/20 text-agp-accent'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            Comparer
          </button>
        </div>
      </div>

      {activeTab === 'analysis' ? (
        <div className="grid grid-cols-12 gap-6">
          {/* Left: Setup loader and feedback */}
          <div className="col-span-12 lg:col-span-5 space-y-4">
            {/* Load Setup */}
            <div className="bg-agp-card border border-agp-border rounded-lg p-6">
              <h3 className="text-sm text-gray-400 mb-4">Charger un Setup</h3>

              <input
                ref={fileInputRef}
                type="file"
                accept=".svm"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) handleLoadSetup(file)
                }}
              />

              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full py-4 border-2 border-dashed border-agp-border rounded-lg hover:border-agp-accent/50 transition-colors"
              >
                <div className="text-center">
                  <div className="text-2xl mb-2">📁</div>
                  <p className="text-sm text-gray-400">
                    {currentSetup ? currentSetup.name : 'Clique pour charger un .svm'}
                  </p>
                </div>
              </button>

              {currentSetup && (
                <div className="mt-4 p-3 bg-black/20 rounded-lg">
                  <div className="text-sm text-white font-medium">{currentSetup.name}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {currentSetup.tire_compound} | {currentSetup.fuel_load}L
                  </div>
                </div>
              )}
            </div>

            {/* Driver Feedback */}
            <div className="bg-agp-card border border-agp-border rounded-lg p-6">
              <h3 className="text-sm text-gray-400 mb-4">Retour Pilote</h3>

              <textarea
                value={driverFeedback}
                onChange={(e) => setDriverFeedback(e.target.value)}
                placeholder="Decris le comportement de la voiture...&#10;Ex: 'understeer entry', 'oversteer exit', 'wheelspin', 'blocage avant'"
                className="w-full h-32 bg-black/20 border border-agp-border rounded-lg p-3 text-sm text-white placeholder-gray-600 resize-none focus:outline-none focus:border-agp-accent/50"
              />

              <div className="mt-3 flex flex-wrap gap-2">
                {['Understeer', 'Oversteer', 'Wheelspin', 'Blocage'].map(tag => (
                  <button
                    key={tag}
                    onClick={() => setDriverFeedback(prev => prev + (prev ? ' ' : '') + tag.toLowerCase())}
                    className="text-xs px-2 py-1 rounded bg-agp-border text-gray-400 hover:text-white hover:bg-agp-accent/20 transition-colors"
                  >
                    {tag}
                  </button>
                ))}
              </div>

              <button
                onClick={handleAnalyze}
                disabled={!currentSetup || !driverFeedback.trim() || isAnalyzing}
                className="w-full mt-4 py-3 rounded-lg bg-agp-accent text-black font-medium hover:bg-agp-accent/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isAnalyzing ? 'Analyse en cours...' : 'Analyser'}
              </button>
            </div>

            {/* Quick Setup Overview */}
            {currentSetup?.suspension && (
              <div className="bg-agp-card border border-agp-border rounded-lg p-6">
                <h3 className="text-sm text-gray-400 mb-4">Apercu Setup</h3>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-xs text-gray-500">Hauteur AV</div>
                    <div className="text-white">{currentSetup.suspension.front_ride_height_mm}mm</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Hauteur AR</div>
                    <div className="text-white">{currentSetup.suspension.rear_ride_height_mm}mm</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">ARB AV/AR</div>
                    <div className="text-white">{currentSetup.suspension.front_arb}/{currentSetup.suspension.rear_arb}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Rake</div>
                    <div className="text-white">{currentSetup.suspension.rake_mm}mm</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Diff Power</div>
                    <div className="text-white">{currentSetup.differential?.power_lock}%</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Brake Bias</div>
                    <div className="text-white">{currentSetup.brakes?.bias_front}%</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right: Diagnostics */}
          <div className="col-span-12 lg:col-span-7 space-y-4">
            <h3 className="text-sm text-gray-400">Diagnostics ({diagnostics.length})</h3>

            {diagnostics.length === 0 ? (
              <div className="bg-agp-card border border-agp-border rounded-lg p-8 text-center">
                <div className="text-4xl mb-3">🔍</div>
                <p className="text-gray-500">
                  Charge un setup et decris le comportement pour recevoir des diagnostics
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {diagnostics.map(diag => (
                  <DiagnosticCard key={diag.id} diagnostic={diag} />
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Compare Tab */
        <div className="grid grid-cols-12 gap-6">
          {/* Load setups */}
          <div className="col-span-12 lg:col-span-4 space-y-4">
            <div className="bg-agp-card border border-agp-border rounded-lg p-6">
              <h3 className="text-sm text-gray-400 mb-4">Setup A</h3>
              <input
                ref={fileInputRef}
                type="file"
                accept=".svm"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) handleLoadSetup(file, false)
                }}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full py-3 border-2 border-dashed border-agp-border rounded-lg hover:border-agp-accent/50 transition-colors"
              >
                <span className="text-sm text-gray-400">
                  {currentSetup ? currentSetup.name : 'Charger Setup A'}
                </span>
              </button>
            </div>

            <div className="bg-agp-card border border-agp-border rounded-lg p-6">
              <h3 className="text-sm text-gray-400 mb-4">Setup B</h3>
              <input
                ref={compareInputRef}
                type="file"
                accept=".svm"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) handleLoadSetup(file, true)
                }}
              />
              <button
                onClick={() => compareInputRef.current?.click()}
                className="w-full py-3 border-2 border-dashed border-agp-border rounded-lg hover:border-agp-accent-blue/50 transition-colors"
              >
                <span className="text-sm text-gray-400">
                  {compareSetup ? compareSetup.name : 'Charger Setup B'}
                </span>
              </button>
            </div>
          </div>

          {/* Comparison */}
          <div className="col-span-12 lg:col-span-8">
            <SetupComparison setupA={currentSetup} setupB={compareSetup} />
          </div>
        </div>
      )}
    </div>
  )
}

export default SetupPage
