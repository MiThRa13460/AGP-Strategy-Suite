using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace AGPStrategy.Models
{
    /// <summary>
    /// Complete data structure received from AGP Strategy Suite backend.
    /// </summary>
    public class AGPData
    {
        [JsonProperty("connected")]
        public bool Connected { get; set; }

        [JsonProperty("rf2_connected")]
        public bool Rf2Connected { get; set; }

        [JsonProperty("telemetry")]
        public TelemetryData? Telemetry { get; set; }

        [JsonProperty("analysis")]
        public AnalysisData? Analysis { get; set; }

        [JsonProperty("strategy")]
        public StrategyData? Strategy { get; set; }

        [JsonProperty("recommendations")]
        public List<Recommendation>? Recommendations { get; set; }

        [JsonProperty("live_timing")]
        public LiveTimingData? LiveTiming { get; set; }
    }

    /// <summary>
    /// Real-time telemetry data.
    /// </summary>
    public class TelemetryData
    {
        // Speed & Engine
        [JsonProperty("speed")]
        public double Speed { get; set; }

        [JsonProperty("rpm")]
        public int Rpm { get; set; }

        [JsonProperty("max_rpm")]
        public int MaxRpm { get; set; }

        [JsonProperty("gear")]
        public int Gear { get; set; }

        // Fuel
        [JsonProperty("fuel")]
        public double Fuel { get; set; }

        [JsonProperty("fuel_pct")]
        public double FuelPct { get; set; }

        [JsonProperty("fuel_per_lap")]
        public double FuelPerLap { get; set; }

        // Inputs
        [JsonProperty("throttle_pct")]
        public double ThrottlePct { get; set; }

        [JsonProperty("brake_pct")]
        public double BrakePct { get; set; }

        [JsonProperty("clutch_pct")]
        public double ClutchPct { get; set; }

        // G-Forces
        [JsonProperty("g_lat")]
        public double GLat { get; set; }

        [JsonProperty("g_long")]
        public double GLong { get; set; }

        // Tires - Temperature
        [JsonProperty("tire_temp")]
        public TireCornerData<double>? TireTemp { get; set; }

        // Tires - Pressure
        [JsonProperty("tire_pressure")]
        public TireCornerData<double>? TirePressure { get; set; }

        // Tires - Wear
        [JsonProperty("tire_wear")]
        public TireCornerData<double>? TireWear { get; set; }

        // Tires - Grip
        [JsonProperty("tire_grip")]
        public TireCornerData<double>? TireGrip { get; set; }

        // Brakes - Temperature
        [JsonProperty("brake_temp")]
        public TireCornerData<double>? BrakeTemp { get; set; }

        // Lap info
        [JsonProperty("lap_number")]
        public int LapNumber { get; set; }

        [JsonProperty("last_lap_time")]
        public double LastLapTime { get; set; }

        [JsonProperty("best_lap_time")]
        public double BestLapTime { get; set; }

        [JsonProperty("position")]
        public int Position { get; set; }

        [JsonProperty("total_cars")]
        public int TotalCars { get; set; }

        // Session
        [JsonProperty("vehicle")]
        public string? Vehicle { get; set; }

        [JsonProperty("track")]
        public string? Track { get; set; }
    }

    /// <summary>
    /// Corner data for tires/brakes.
    /// </summary>
    public class TireCornerData<T> where T : struct
    {
        [JsonProperty("FL")]
        public T? FL { get; set; }

        [JsonProperty("FR")]
        public T? FR { get; set; }

        [JsonProperty("RL")]
        public T? RL { get; set; }

        [JsonProperty("RR")]
        public T? RR { get; set; }
    }

    /// <summary>
    /// Real-time behavior analysis.
    /// </summary>
    public class AnalysisData
    {
        [JsonProperty("understeer_pct")]
        public double UndersteerPct { get; set; }

        [JsonProperty("oversteer_pct")]
        public double OversteerPct { get; set; }

        [JsonProperty("traction_loss_pct")]
        public double TractionLossPct { get; set; }

        [JsonProperty("brake_lock_pct")]
        public double BrakeLockPct { get; set; }

        [JsonProperty("corner_phase")]
        public string? CornerPhase { get; set; }

        [JsonProperty("balance_score")]
        public double BalanceScore { get; set; }

        [JsonProperty("entry_balance")]
        public double EntryBalance { get; set; }

        [JsonProperty("mid_corner_balance")]
        public double MidCornerBalance { get; set; }

        [JsonProperty("exit_balance")]
        public double ExitBalance { get; set; }
    }

    /// <summary>
    /// Strategy data for endurance races.
    /// </summary>
    public class StrategyData
    {
        [JsonProperty("current_lap")]
        public int CurrentLap { get; set; }

        [JsonProperty("total_laps")]
        public int TotalLaps { get; set; }

        [JsonProperty("fuel_laps_remaining")]
        public double FuelLapsRemaining { get; set; }

        [JsonProperty("tire_laps_remaining")]
        public int TireLapsRemaining { get; set; }

        [JsonProperty("pit_window_start")]
        public int PitWindowStart { get; set; }

        [JsonProperty("pit_window_end")]
        public int PitWindowEnd { get; set; }

        [JsonProperty("in_pit_window")]
        public bool InPitWindow { get; set; }

        [JsonProperty("next_pit_lap")]
        public int? NextPitLap { get; set; }

        [JsonProperty("optimal_pit_lap")]
        public int OptimalPitLap { get; set; }

        [JsonProperty("is_critical")]
        public bool IsCritical { get; set; }

        [JsonProperty("current_stint")]
        public int CurrentStint { get; set; }

        [JsonProperty("current_driver")]
        public string? CurrentDriver { get; set; }
    }

    /// <summary>
    /// Setup recommendation.
    /// </summary>
    public class Recommendation
    {
        [JsonProperty("title")]
        public string? Title { get; set; }

        [JsonProperty("description")]
        public string? Description { get; set; }

        [JsonProperty("priority")]
        public int Priority { get; set; }

        [JsonProperty("category")]
        public string? Category { get; set; }

        [JsonProperty("confidence")]
        public double Confidence { get; set; }

        [JsonProperty("action")]
        public string? Action { get; set; }
    }

    /// <summary>
    /// Live timing data.
    /// </summary>
    public class LiveTimingData
    {
        [JsonProperty("standings")]
        public List<StandingEntry>? Standings { get; set; }

        [JsonProperty("threats")]
        public List<ThreatInfo>? Threats { get; set; }

        [JsonProperty("gap_ahead")]
        public double GapAhead { get; set; }

        [JsonProperty("gap_behind")]
        public double GapBehind { get; set; }
    }

    /// <summary>
    /// Single standing entry.
    /// </summary>
    public class StandingEntry
    {
        [JsonProperty("position")]
        public int Position { get; set; }

        [JsonProperty("driver_name")]
        public string? DriverName { get; set; }

        [JsonProperty("car_class")]
        public string? CarClass { get; set; }

        [JsonProperty("gap")]
        public string? Gap { get; set; }

        [JsonProperty("interval")]
        public string? Interval { get; set; }

        [JsonProperty("last_lap")]
        public double LastLap { get; set; }

        [JsonProperty("best_lap")]
        public double BestLap { get; set; }

        [JsonProperty("is_player")]
        public bool IsPlayer { get; set; }
    }

    /// <summary>
    /// Threat information for nearby drivers.
    /// </summary>
    public class ThreatInfo
    {
        [JsonProperty("driver_name")]
        public string? DriverName { get; set; }

        [JsonProperty("position")]
        public int Position { get; set; }

        [JsonProperty("gap")]
        public double Gap { get; set; }

        [JsonProperty("threat_level")]
        public string? ThreatLevel { get; set; }  // none, low, medium, high

        [JsonProperty("is_ahead")]
        public bool IsAhead { get; set; }

        [JsonProperty("pace_diff")]
        public double PaceDiff { get; set; }
    }
}
