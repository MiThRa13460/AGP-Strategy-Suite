using System;
using System.Collections.Generic;
using AGPStrategy.Models;
using SimHub.Plugins;

namespace AGPStrategy
{
    /// <summary>
    /// Provides AGP Strategy properties to SimHub.
    /// All properties are prefixed with "AGP."
    /// </summary>
    public class PropertyProvider
    {
        private readonly PluginManager _pluginManager;
        private const string PREFIX = "AGP";

        /// <summary>
        /// All registered property names.
        /// </summary>
        public static readonly List<string> PropertyNames = new List<string>
        {
            // Connection
            "Connected",
            "Rf2Connected",

            // Tire Temperatures
            "TireTemp_FL",
            "TireTemp_FR",
            "TireTemp_RL",
            "TireTemp_RR",
            "TireTemp_FrontAvg",
            "TireTemp_RearAvg",

            // Tire Pressures
            "TirePressure_FL",
            "TirePressure_FR",
            "TirePressure_RL",
            "TirePressure_RR",

            // Tire Wear
            "TireWear_FL",
            "TireWear_FR",
            "TireWear_RL",
            "TireWear_RR",
            "TireWear_FrontAvg",
            "TireWear_RearAvg",

            // Tire Grip
            "TireGrip_FL",
            "TireGrip_FR",
            "TireGrip_RL",
            "TireGrip_RR",

            // Brake Temperatures
            "BrakeTemp_FL",
            "BrakeTemp_FR",
            "BrakeTemp_RL",
            "BrakeTemp_RR",

            // Analysis - Behavior
            "Understeer_Pct",
            "Oversteer_Pct",
            "TractionLoss_Pct",
            "BrakeLock_Pct",
            "CornerPhase",
            "BalanceScore",
            "EntryBalance",
            "MidCornerBalance",
            "ExitBalance",

            // Strategy
            "FuelLapsRemaining",
            "TireLapsRemaining",
            "PitWindowStart",
            "PitWindowEnd",
            "InPitWindow",
            "NextPitLap",
            "OptimalPitLap",
            "IsCritical",
            "CurrentStint",
            "CurrentDriver",

            // Recommendations
            "NextRecommendation",
            "NextRecommendationPriority",
            "NextRecommendationAction",
            "RecommendationCount",

            // Live Timing
            "Position",
            "TotalCars",
            "GapAhead",
            "GapBehind",
            "ThreatLevel",
            "NearestThreatName",
            "NearestThreatGap",

            // Calculated
            "BalanceIndicator",  // -100 (understeer) to +100 (oversteer)
            "TireCondition",     // 0-100 overall tire condition
            "FuelUrgency",       // 0-100 how urgent is refueling
        };

        public PropertyProvider(PluginManager pluginManager)
        {
            _pluginManager = pluginManager;
        }

        /// <summary>
        /// Register all AGP properties with SimHub.
        /// </summary>
        public void RegisterProperties()
        {
            foreach (var name in PropertyNames)
            {
                var fullName = $"{PREFIX}.{name}";

                // Determine type based on property name
                if (name.EndsWith("_Pct") || name.Contains("Temp") || name.Contains("Pressure") ||
                    name.Contains("Wear") || name.Contains("Grip") || name.Contains("Gap") ||
                    name.Contains("Balance") || name.Contains("Remaining") || name.Contains("Score") ||
                    name.Contains("Indicator") || name.Contains("Condition") || name.Contains("Urgency"))
                {
                    _pluginManager.AddProperty(fullName, typeof(double), 0.0);
                }
                else if (name.Contains("Connected") || name.Contains("InPit") || name.Contains("IsCritical"))
                {
                    _pluginManager.AddProperty(fullName, typeof(bool), false);
                }
                else if (name.Contains("Lap") || name.Contains("Position") || name.Contains("Count") ||
                         name.Contains("Cars") || name.Contains("Stint") || name.Contains("Window") ||
                         name.Contains("Priority"))
                {
                    _pluginManager.AddProperty(fullName, typeof(int), 0);
                }
                else
                {
                    _pluginManager.AddProperty(fullName, typeof(string), "");
                }
            }
        }

        /// <summary>
        /// Update all properties from AGP data.
        /// </summary>
        public void UpdateProperties(AGPData data)
        {
            if (data == null) return;

            // Connection
            SetProperty("Connected", data.Connected);
            SetProperty("Rf2Connected", data.Rf2Connected);

            // Telemetry
            if (data.Telemetry != null)
            {
                UpdateTelemetryProperties(data.Telemetry);
            }

            // Analysis
            if (data.Analysis != null)
            {
                UpdateAnalysisProperties(data.Analysis);
            }

            // Strategy
            if (data.Strategy != null)
            {
                UpdateStrategyProperties(data.Strategy);
            }

            // Recommendations
            if (data.Recommendations != null && data.Recommendations.Count > 0)
            {
                UpdateRecommendationProperties(data.Recommendations);
            }

            // Live Timing
            if (data.LiveTiming != null)
            {
                UpdateLiveTimingProperties(data.LiveTiming);
            }

            // Calculated properties
            UpdateCalculatedProperties(data);
        }

        private void UpdateTelemetryProperties(TelemetryData telemetry)
        {
            // Tire temps
            if (telemetry.TireTemp != null)
            {
                SetProperty("TireTemp_FL", telemetry.TireTemp.FL ?? 0);
                SetProperty("TireTemp_FR", telemetry.TireTemp.FR ?? 0);
                SetProperty("TireTemp_RL", telemetry.TireTemp.RL ?? 0);
                SetProperty("TireTemp_RR", telemetry.TireTemp.RR ?? 0);

                var frontAvg = ((telemetry.TireTemp.FL ?? 0) + (telemetry.TireTemp.FR ?? 0)) / 2;
                var rearAvg = ((telemetry.TireTemp.RL ?? 0) + (telemetry.TireTemp.RR ?? 0)) / 2;
                SetProperty("TireTemp_FrontAvg", frontAvg);
                SetProperty("TireTemp_RearAvg", rearAvg);
            }

            // Tire pressures
            if (telemetry.TirePressure != null)
            {
                SetProperty("TirePressure_FL", telemetry.TirePressure.FL ?? 0);
                SetProperty("TirePressure_FR", telemetry.TirePressure.FR ?? 0);
                SetProperty("TirePressure_RL", telemetry.TirePressure.RL ?? 0);
                SetProperty("TirePressure_RR", telemetry.TirePressure.RR ?? 0);
            }

            // Tire wear
            if (telemetry.TireWear != null)
            {
                SetProperty("TireWear_FL", telemetry.TireWear.FL ?? 100);
                SetProperty("TireWear_FR", telemetry.TireWear.FR ?? 100);
                SetProperty("TireWear_RL", telemetry.TireWear.RL ?? 100);
                SetProperty("TireWear_RR", telemetry.TireWear.RR ?? 100);

                var frontAvg = ((telemetry.TireWear.FL ?? 100) + (telemetry.TireWear.FR ?? 100)) / 2;
                var rearAvg = ((telemetry.TireWear.RL ?? 100) + (telemetry.TireWear.RR ?? 100)) / 2;
                SetProperty("TireWear_FrontAvg", frontAvg);
                SetProperty("TireWear_RearAvg", rearAvg);
            }

            // Tire grip
            if (telemetry.TireGrip != null)
            {
                SetProperty("TireGrip_FL", telemetry.TireGrip.FL ?? 100);
                SetProperty("TireGrip_FR", telemetry.TireGrip.FR ?? 100);
                SetProperty("TireGrip_RL", telemetry.TireGrip.RL ?? 100);
                SetProperty("TireGrip_RR", telemetry.TireGrip.RR ?? 100);
            }

            // Brake temps
            if (telemetry.BrakeTemp != null)
            {
                SetProperty("BrakeTemp_FL", telemetry.BrakeTemp.FL ?? 0);
                SetProperty("BrakeTemp_FR", telemetry.BrakeTemp.FR ?? 0);
                SetProperty("BrakeTemp_RL", telemetry.BrakeTemp.RL ?? 0);
                SetProperty("BrakeTemp_RR", telemetry.BrakeTemp.RR ?? 0);
            }

            // Position
            SetProperty("Position", telemetry.Position);
            SetProperty("TotalCars", telemetry.TotalCars);
        }

        private void UpdateAnalysisProperties(AnalysisData analysis)
        {
            SetProperty("Understeer_Pct", analysis.UndersteerPct);
            SetProperty("Oversteer_Pct", analysis.OversteerPct);
            SetProperty("TractionLoss_Pct", analysis.TractionLossPct);
            SetProperty("BrakeLock_Pct", analysis.BrakeLockPct);
            SetProperty("CornerPhase", analysis.CornerPhase ?? "");
            SetProperty("BalanceScore", analysis.BalanceScore);
            SetProperty("EntryBalance", analysis.EntryBalance);
            SetProperty("MidCornerBalance", analysis.MidCornerBalance);
            SetProperty("ExitBalance", analysis.ExitBalance);
        }

        private void UpdateStrategyProperties(StrategyData strategy)
        {
            SetProperty("FuelLapsRemaining", strategy.FuelLapsRemaining);
            SetProperty("TireLapsRemaining", strategy.TireLapsRemaining);
            SetProperty("PitWindowStart", strategy.PitWindowStart);
            SetProperty("PitWindowEnd", strategy.PitWindowEnd);
            SetProperty("InPitWindow", strategy.InPitWindow);
            SetProperty("NextPitLap", strategy.NextPitLap ?? 0);
            SetProperty("OptimalPitLap", strategy.OptimalPitLap);
            SetProperty("IsCritical", strategy.IsCritical);
            SetProperty("CurrentStint", strategy.CurrentStint);
            SetProperty("CurrentDriver", strategy.CurrentDriver ?? "");
        }

        private void UpdateRecommendationProperties(List<Recommendation> recommendations)
        {
            var next = recommendations[0];
            SetProperty("NextRecommendation", next.Title ?? "");
            SetProperty("NextRecommendationPriority", next.Priority);
            SetProperty("NextRecommendationAction", next.Action ?? "");
            SetProperty("RecommendationCount", recommendations.Count);
        }

        private void UpdateLiveTimingProperties(LiveTimingData liveTiming)
        {
            SetProperty("GapAhead", liveTiming.GapAhead);
            SetProperty("GapBehind", liveTiming.GapBehind);

            if (liveTiming.Threats != null && liveTiming.Threats.Count > 0)
            {
                var nearestThreat = liveTiming.Threats[0];
                SetProperty("ThreatLevel", nearestThreat.ThreatLevel ?? "none");
                SetProperty("NearestThreatName", nearestThreat.DriverName ?? "");
                SetProperty("NearestThreatGap", nearestThreat.Gap);
            }
            else
            {
                SetProperty("ThreatLevel", "none");
                SetProperty("NearestThreatName", "");
                SetProperty("NearestThreatGap", 0.0);
            }
        }

        private void UpdateCalculatedProperties(AGPData data)
        {
            // Balance indicator: -100 (understeer) to +100 (oversteer)
            if (data.Analysis != null)
            {
                var balance = (data.Analysis.OversteerPct - data.Analysis.UndersteerPct);
                balance = Math.Max(-100, Math.Min(100, balance));
                SetProperty("BalanceIndicator", balance);
            }

            // Tire condition: average of all wear values
            if (data.Telemetry?.TireWear != null)
            {
                var wear = data.Telemetry.TireWear;
                var avgWear = ((wear.FL ?? 100) + (wear.FR ?? 100) + (wear.RL ?? 100) + (wear.RR ?? 100)) / 4;
                SetProperty("TireCondition", avgWear);
            }

            // Fuel urgency: 0 (plenty) to 100 (critical)
            if (data.Strategy != null)
            {
                double urgency = 0;
                if (data.Strategy.FuelLapsRemaining <= 0)
                {
                    urgency = 100;
                }
                else if (data.Strategy.FuelLapsRemaining < 3)
                {
                    urgency = 100 - (data.Strategy.FuelLapsRemaining / 3 * 50);
                }
                else if (data.Strategy.FuelLapsRemaining < 10)
                {
                    urgency = 50 - ((data.Strategy.FuelLapsRemaining - 3) / 7 * 30);
                }
                else
                {
                    urgency = Math.Max(0, 20 - data.Strategy.FuelLapsRemaining);
                }
                SetProperty("FuelUrgency", urgency);
            }
        }

        private void SetProperty(string name, object value)
        {
            _pluginManager.SetPropertyValue($"{PREFIX}.{name}", value);
        }
    }
}
