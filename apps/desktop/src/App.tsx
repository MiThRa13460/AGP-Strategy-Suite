import { useEffect, useState } from 'react'
import { useTelemetryStore } from './stores/telemetryStore'
import { useTelemetry } from './hooks/useTelemetry'
import { TireDisplay } from './components/TireDisplay'
import { BrakeDisplay } from './components/BrakeDisplay'
import { GForceTrace } from './components/GForceTrace'
import { RecommendationCard } from './components/RecommendationCard'
import { UpdateNotification } from './components/UpdateModal'
import { Strategy } from './pages/Strategy'
import { OverlayConfigPage } from './pages/OverlayConfig'
import { TelemetryAnalysis } from './pages/TelemetryAnalysis'

type TabType = 'dashboard' | 'tires' | 'analysis' | 'strategy' | 'overlay' | 'csv-analysis'

function App() {
  const { connect, disconnect } = useTelemetry()
  const {
    connected,
    rf2Connected,
    telemetry,
    analysis,
    recommendations
  } = useTelemetryStore()

  const [activeTab, setActiveTab] = useState<TabType>('dashboard')

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [])

  // Transform telemetry data for components
  const tireTemps = telemetry?.tire_temp || { FL: 0, FR: 0, RL: 0, RR: 0 }
  const tirePressures = telemetry?.tire_pressure || { FL: 175, FR: 175, RL: 175, RR: 175 }
  const tireWear = telemetry?.tire_wear || { FL: 100, FR: 100, RL: 100, RR: 100 }
  const tireGrip = telemetry?.tire_grip || { FL: 100, FR: 100, RL: 100, RR: 100 }
  const brakeTemps = telemetry?.brake_temp || { FL: 300, FR: 300, RL: 300, RR: 300 }

  return (
    <div className="min-h-screen bg-agp-bg">
      {/* Auto-update notification */}
      <UpdateNotification />

      {/* Header */}
      <header className="bg-agp-card border-b border-agp-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-agp-accent to-agp-accent-blue flex items-center justify-center">
                <span className="text-black font-bold text-sm">AGP</span>
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">Strategy Suite</h1>
                <span className="text-[10px] text-gray-500">v1.0.0</span>
              </div>
            </div>

            {/* Tabs */}
            <nav className="flex gap-1 ml-6">
              {[
                { id: 'dashboard', label: 'Dashboard' },
                { id: 'tires', label: 'Pneus & Freins' },
                { id: 'analysis', label: 'Analyse' },
                { id: 'csv-analysis', label: 'CSV Analysis' },
                { id: 'strategy', label: 'Strategie' },
                { id: 'overlay', label: 'Overlays' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as TabType)}
                  className={`px-4 py-2 text-sm rounded-lg transition-all ${
                    activeTab === tab.id
                      ? 'bg-agp-accent/20 text-agp-accent'
                      : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Status indicators */}
          <div className="flex items-center gap-4">
            <StatusIndicator
              active={connected}
              label={connected ? 'Backend' : 'Deconnecte'}
              activeColor="bg-green-500"
              inactiveColor="bg-red-500"
            />
            <StatusIndicator
              active={rf2Connected}
              label={rf2Connected ? 'rFactor 2' : 'Attente rF2'}
              activeColor="bg-agp-accent"
              inactiveColor="bg-yellow-500"
            />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        {/* Strategy, Overlay, and CSV Analysis pages work without rF2 connection */}
        {activeTab === 'strategy' ? (
          <Strategy />
        ) : activeTab === 'overlay' ? (
          <OverlayConfigPage />
        ) : activeTab === 'csv-analysis' ? (
          <TelemetryAnalysis />
        ) : !rf2Connected ? (
          <WaitingScreen />
        ) : telemetry ? (
          <>
            {activeTab === 'dashboard' && (
              <DashboardView
                telemetry={telemetry}
                analysis={analysis}
                tireTemps={tireTemps}
                tirePressures={tirePressures}
                tireWear={tireWear}
                tireGrip={tireGrip}
                brakeTemps={brakeTemps}
                recommendations={recommendations}
              />
            )}
            {activeTab === 'tires' && (
              <TiresView
                tireTemps={tireTemps}
                tirePressures={tirePressures}
                tireWear={tireWear}
                tireGrip={tireGrip}
                brakeTemps={brakeTemps}
                brakePct={telemetry.brake_pct || 0}
              />
            )}
            {activeTab === 'analysis' && (
              <AnalysisView
                analysis={analysis}
                telemetry={telemetry}
                recommendations={recommendations}
              />
            )}
          </>
        ) : (
          <div className="flex items-center justify-center h-96">
            <div className="text-gray-500">Chargement...</div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 bg-agp-card border-t border-agp-border px-6 py-2">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div>
            {telemetry?.vehicle && (
              <span className="text-gray-400">
                {telemetry.vehicle} @ {telemetry.track}
              </span>
            )}
          </div>
          <div className="flex items-center gap-4">
            {telemetry && (
              <>
                <span>Tour {telemetry.lap_number}</span>
                <span className="text-agp-accent">
                  {formatLapTime(telemetry.last_lap_time)}
                </span>
              </>
            )}
          </div>
        </div>
      </footer>
    </div>
  )
}

// Status indicator component
function StatusIndicator({ active, label, activeColor, inactiveColor }: {
  active: boolean
  label: string
  activeColor: string
  inactiveColor: string
}) {
  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${active ? activeColor : inactiveColor}`} />
      <span className="text-sm text-gray-400">{label}</span>
    </div>
  )
}

// Waiting screen
function WaitingScreen() {
  return (
    <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)]">
      <div className="text-8xl mb-6 animate-pulse">🏎️</div>
      <h2 className="text-2xl text-white mb-2">En attente de rFactor 2</h2>
      <p className="text-gray-500 text-center max-w-md">
        Lance rFactor 2 et entre en piste pour voir la telemetrie en temps reel
      </p>
      <div className="mt-8 flex items-center gap-2 text-sm text-gray-600">
        <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
        <span>Recherche du jeu...</span>
      </div>
    </div>
  )
}

// Dashboard view - main overview
interface DashboardViewProps {
  telemetry: any
  analysis: any
  tireTemps: any
  tirePressures: any
  tireWear: any
  tireGrip: any
  brakeTemps: any
  recommendations: any[]
}

function DashboardView({
  telemetry,
  analysis,
  tireTemps,
  tirePressures,
  tireWear,
  tireGrip,
  brakeTemps,
  recommendations
}: DashboardViewProps) {
  return (
    <div className="grid grid-cols-12 gap-4">
      {/* Left column - Main telemetry */}
      <div className="col-span-12 lg:col-span-4 space-y-4">
        {/* Speed & Engine */}
        <div className="bg-agp-card border border-agp-border rounded-lg p-6">
          <div className="flex items-end justify-between mb-4">
            <div>
              <div className="text-6xl font-bold text-agp-accent tabular-nums">
                {telemetry.speed}
              </div>
              <div className="text-sm text-gray-500">km/h</div>
            </div>
            <div className="text-right">
              <div className="text-4xl font-bold text-white tabular-nums">
                {telemetry.gear === 0 ? 'N' : telemetry.gear === -1 ? 'R' : telemetry.gear}
              </div>
              <div className="text-sm text-gray-500">Gear</div>
            </div>
          </div>

          {/* RPM Bar */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-gray-500">
              <span>RPM</span>
              <span className="tabular-nums">{telemetry.rpm}</span>
            </div>
            <div className="h-3 bg-agp-border rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-75"
                style={{
                  width: `${(telemetry.rpm / (telemetry.max_rpm || 8000)) * 100}%`,
                  background: telemetry.rpm > (telemetry.max_rpm || 8000) * 0.9
                    ? 'linear-gradient(90deg, #00ff88, #ff3366)'
                    : 'linear-gradient(90deg, #00ff88, #00aaff)'
                }}
              />
            </div>
          </div>
        </div>

        {/* Fuel */}
        <div className="bg-agp-card border border-agp-border rounded-lg p-6">
          <h3 className="text-sm text-gray-400 mb-4">Carburant</h3>
          <div className="flex items-end justify-between mb-4">
            <div>
              <div className="text-4xl font-bold text-white tabular-nums">
                {telemetry.fuel.toFixed(1)}
              </div>
              <div className="text-sm text-gray-500">Litres</div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-agp-accent tabular-nums">
                {telemetry.fuel_pct.toFixed(0)}%
              </div>
              {telemetry.fuel_per_lap > 0 && (
                <div className="text-sm text-gray-500">
                  ~{Math.floor(telemetry.fuel / telemetry.fuel_per_lap)} tours
                </div>
              )}
            </div>
          </div>
          <div className="h-2 bg-agp-border rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${telemetry.fuel_pct}%`,
                background: telemetry.fuel_pct < 15
                  ? '#ff3366'
                  : telemetry.fuel_pct < 30
                    ? '#ffaa00'
                    : '#00ff88'
              }}
            />
          </div>
        </div>

        {/* Pedals */}
        <div className="bg-agp-card border border-agp-border rounded-lg p-6">
          <h3 className="text-sm text-gray-400 mb-4">Pedales</h3>
          <div className="space-y-3">
            <PedalBar label="Throttle" value={telemetry.throttle_pct || 0} color="#00ff88" />
            <PedalBar label="Brake" value={telemetry.brake_pct || 0} color="#ff3366" />
            <PedalBar label="Clutch" value={telemetry.clutch_pct || 0} color="#ffaa00" />
          </div>
        </div>
      </div>

      {/* Middle column - Tires & G-Force */}
      <div className="col-span-12 lg:col-span-4 space-y-4">
        <TireDisplay
          temps={tireTemps}
          pressures={tirePressures}
          wear={tireWear}
          grip={tireGrip}
        />
        <GForceTrace
          gLat={telemetry.g_lat || 0}
          gLong={telemetry.g_long || 0}
          maxG={3}
        />
      </div>

      {/* Right column - Brakes & Recommendations */}
      <div className="col-span-12 lg:col-span-4 space-y-4">
        <BrakeDisplay
          temps={brakeTemps}
          brakePct={telemetry.brake_pct || 0}
        />

        {/* Quick Analysis */}
        {analysis && (
          <div className="bg-agp-card border border-agp-border rounded-lg p-6">
            <h3 className="text-sm text-gray-400 mb-4">Comportement</h3>
            <div className="grid grid-cols-3 gap-2">
              <AnalysisStat
                label="Understeer"
                value={analysis.understeer_pct || 0}
                threshold={25}
              />
              <AnalysisStat
                label="Oversteer"
                value={analysis.oversteer_pct || 0}
                threshold={25}
              />
              <AnalysisStat
                label="Patinage"
                value={analysis.traction_loss_pct || 0}
                threshold={15}
              />
            </div>
          </div>
        )}

        <RecommendationCard recommendations={recommendations} />
      </div>
    </div>
  )
}

// Pedal bar component
function PedalBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-gray-500 w-14">{label}</span>
      <div className="flex-1 h-2 bg-agp-border rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-75"
          style={{ width: `${value}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs tabular-nums w-10 text-right" style={{ color }}>
        {Math.round(value)}%
      </span>
    </div>
  )
}

// Analysis stat component
function AnalysisStat({ label, value, threshold }: { label: string; value: number; threshold: number }) {
  const isWarning = value > threshold
  return (
    <div className="text-center">
      <div className="text-[10px] text-gray-500 mb-1">{label}</div>
      <div className={`text-lg font-bold ${isWarning ? 'text-agp-warning' : 'text-white'}`}>
        {value.toFixed(0)}%
      </div>
    </div>
  )
}

// Tires view - detailed tire and brake info
interface TiresViewProps {
  tireTemps: any
  tirePressures: any
  tireWear: any
  tireGrip: any
  brakeTemps: any
  brakePct: number
}

function TiresView({ tireTemps, tirePressures, tireWear, tireGrip, brakeTemps, brakePct }: TiresViewProps) {
  return (
    <div className="grid grid-cols-12 gap-4">
      <div className="col-span-12 lg:col-span-6">
        <TireDisplay
          temps={tireTemps}
          pressures={tirePressures}
          wear={tireWear}
          grip={tireGrip}
        />
      </div>
      <div className="col-span-12 lg:col-span-6">
        <BrakeDisplay temps={brakeTemps} brakePct={brakePct} />
      </div>

      {/* Detailed tire stats */}
      <div className="col-span-12 bg-agp-card border border-agp-border rounded-lg p-6">
        <h3 className="text-sm text-gray-400 mb-4">Details par roue</h3>
        <div className="grid grid-cols-4 gap-4">
          {['FL', 'FR', 'RL', 'RR'].map(corner => (
            <div key={corner} className="text-center">
              <div className="text-sm font-medium text-white mb-2">{corner}</div>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-500">Temp</span>
                  <span className={getTempTextColor(tireTemps[corner])}>
                    {Math.round(tireTemps[corner])}°C
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Pression</span>
                  <span className="text-white">{Math.round(tirePressures[corner])} kPa</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Usure</span>
                  <span className={getWearTextColor(tireWear[corner])}>
                    {Math.round(tireWear[corner])}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Grip</span>
                  <span className={getGripTextColor(tireGrip[corner])}>
                    {Math.round(tireGrip[corner])}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Frein</span>
                  <span className={getBrakeTextColor(brakeTemps[corner])}>
                    {Math.round(brakeTemps[corner])}°C
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Analysis view - detailed analysis and recommendations
interface AnalysisViewProps {
  analysis: any
  telemetry: any
  recommendations: any[]
}

function AnalysisView({ analysis, telemetry, recommendations }: AnalysisViewProps) {
  return (
    <div className="grid grid-cols-12 gap-4">
      {/* G-Force */}
      <div className="col-span-12 lg:col-span-4">
        <GForceTrace
          gLat={telemetry?.g_lat || 0}
          gLong={telemetry?.g_long || 0}
          maxG={4}
        />
      </div>

      {/* Behavior analysis */}
      <div className="col-span-12 lg:col-span-4">
        <div className="bg-agp-card border border-agp-border rounded-lg p-6 h-full">
          <h3 className="text-sm text-gray-400 mb-4">Analyse du comportement</h3>

          {analysis ? (
            <div className="space-y-4">
              <BehaviorBar
                label="Sous-virage"
                value={analysis.understeer_pct || 0}
                color="#ff3366"
                description="Avant qui pousse"
              />
              <BehaviorBar
                label="Survirage"
                value={analysis.oversteer_pct || 0}
                color="#ffaa00"
                description="Arriere qui glisse"
              />
              <BehaviorBar
                label="Perte de traction"
                value={analysis.traction_loss_pct || 0}
                color="#ff8844"
                description="Patinage acceleration"
              />
              <BehaviorBar
                label="Blocage freins"
                value={analysis.brake_lock_pct || 0}
                color="#ff3366"
                description="Roues bloquees au freinage"
              />

              {analysis.corner_phase && (
                <div className="mt-4 pt-4 border-t border-agp-border">
                  <div className="text-xs text-gray-500 mb-1">Phase actuelle</div>
                  <div className="text-lg font-medium text-agp-accent">
                    {getCornerPhaseLabel(analysis.corner_phase)}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              Analyse en cours...
            </div>
          )}
        </div>
      </div>

      {/* Recommendations */}
      <div className="col-span-12 lg:col-span-4">
        <RecommendationCard recommendations={recommendations} />
      </div>

      {/* Session stats */}
      <div className="col-span-12 bg-agp-card border border-agp-border rounded-lg p-6">
        <h3 className="text-sm text-gray-400 mb-4">Statistiques session</h3>
        <div className="grid grid-cols-4 gap-6">
          <SessionStat
            label="Tours completes"
            value={telemetry?.lap_number || 0}
            unit="tours"
          />
          <SessionStat
            label="Meilleur tour"
            value={formatLapTime(telemetry?.best_lap_time)}
            isTime
          />
          <SessionStat
            label="Dernier tour"
            value={formatLapTime(telemetry?.last_lap_time)}
            isTime
          />
          <SessionStat
            label="Position"
            value={telemetry?.position || '-'}
            suffix={telemetry?.total_cars ? `/${telemetry.total_cars}` : ''}
          />
        </div>
      </div>
    </div>
  )
}

// Behavior bar component
function BehaviorBar({ label, value, color, description }: {
  label: string
  value: number
  color: string
  description: string
}) {
  return (
    <div>
      <div className="flex justify-between items-baseline mb-1">
        <span className="text-sm text-white">{label}</span>
        <span className="text-xs tabular-nums" style={{ color }}>
          {value.toFixed(0)}%
        </span>
      </div>
      <div className="h-2 bg-agp-border rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-300"
          style={{ width: `${Math.min(value, 100)}%`, backgroundColor: color }}
        />
      </div>
      <div className="text-[10px] text-gray-600 mt-1">{description}</div>
    </div>
  )
}

// Session stat component
function SessionStat({ label, value, unit, suffix, isTime }: {
  label: string
  value: string | number
  unit?: string
  suffix?: string
  isTime?: boolean
}) {
  return (
    <div>
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${isTime ? 'text-agp-accent' : 'text-white'} tabular-nums`}>
        {value}{suffix}
      </div>
      {unit && <div className="text-xs text-gray-600">{unit}</div>}
    </div>
  )
}

// Helper functions
function formatLapTime(seconds: number | undefined): string {
  if (!seconds || seconds <= 0) return '--:--.---'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toFixed(3).padStart(6, '0')}`
}

function getCornerPhaseLabel(phase: string): string {
  const labels: Record<string, string> = {
    'straight': 'Ligne droite',
    'brake_zone': 'Zone de freinage',
    'trail_brake': 'Freinage degressif',
    'apex': 'Point de corde',
    'exit': 'Sortie de virage'
  }
  return labels[phase] || phase
}

function getTempTextColor(temp: number): string {
  if (temp < 70) return 'text-blue-400'
  if (temp < 95) return 'text-agp-accent'
  if (temp < 105) return 'text-agp-warning'
  return 'text-agp-danger'
}

function getWearTextColor(wear: number): string {
  if (wear > 70) return 'text-agp-accent'
  if (wear > 40) return 'text-agp-warning'
  return 'text-agp-danger'
}

function getGripTextColor(grip: number): string {
  if (grip > 85) return 'text-agp-accent'
  if (grip > 60) return 'text-agp-warning'
  return 'text-agp-danger'
}

function getBrakeTextColor(temp: number): string {
  if (temp < 400) return 'text-blue-400'
  if (temp < 600) return 'text-agp-accent'
  if (temp < 750) return 'text-agp-warning'
  return 'text-agp-danger'
}

export default App
