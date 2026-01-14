import { create } from 'zustand'

interface TireData {
  FL: number
  FR: number
  RL: number
  RR: number
}

interface Telemetry {
  timestamp: number
  vehicle: string
  track: string
  speed: number
  rpm: number
  rpm_max: number
  max_rpm: number
  gear: number
  fuel: number
  fuel_pct: number
  fuel_per_lap: number
  throttle: number
  throttle_pct: number
  brake: number
  brake_pct: number
  steering: number
  clutch: number
  clutch_pct: number
  g_lat: number
  g_long: number
  tire_temp: TireData
  tire_pressure: TireData
  tire_wear: TireData
  tire_grip: TireData
  grip: TireData
  brake_temp: TireData
  ride_height_front: number
  ride_height_rear: number
  rake: number
  front_downforce: number
  rear_downforce: number
  water_temp: number
  oil_temp: number
  lap_number: number
  sector: number
  pos_x: number
  pos_y: number
  pos_z: number
  last_lap_time: number
  best_lap_time: number
  position: number
  total_cars: number
  session?: {
    track_temp: number
    ambient_temp: number
    rain: number
    wetness: number
    session_type: number
    game_phase: number
  }
}

interface Analysis {
  status: string
  lap_number: number
  samples: number
  vehicle: string
  category: string
  understeer_pct: number
  oversteer_pct: number
  traction_loss_pct: number
  stability_score: number
  wheelspin_pct: number
  lockup_pct: number
  brake_lock_pct: number
  corner_phase: string
}

interface Recommendation {
  parameter: string
  direction: string
  value: string | null
  reason: string
  priority: number
  side_effects: string[]
  confidence: number
}

interface TelemetryStore {
  connected: boolean
  rf2Connected: boolean
  telemetry: Telemetry | null
  analysis: Analysis | null
  recommendations: Recommendation[]
  setConnected: (connected: boolean) => void
  setRf2Connected: (connected: boolean) => void
  setTelemetry: (telemetry: Telemetry) => void
  setAnalysis: (analysis: Analysis) => void
  setRecommendations: (recommendations: Recommendation[]) => void
  reset: () => void
}

export const useTelemetryStore = create<TelemetryStore>((set) => ({
  connected: false,
  rf2Connected: false,
  telemetry: null,
  analysis: null,
  recommendations: [],

  setConnected: (connected) => set({ connected }),
  setRf2Connected: (rf2Connected) => set({ rf2Connected }),
  setTelemetry: (telemetry) => set({ telemetry }),
  setAnalysis: (analysis) => set({ analysis }),
  setRecommendations: (recommendations) => set({ recommendations }),
  reset: () => set({
    connected: false,
    rf2Connected: false,
    telemetry: null,
    analysis: null,
    recommendations: [],
  }),
}))
