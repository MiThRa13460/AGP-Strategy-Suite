"""
Setup Correlator - Correlate setup parameters with performance metrics.

Analyzes multiple sessions with different setups to find optimal
parameter values based on telemetry data.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import math
import logging

from agp_core.setup.entities.setup import Setup
from agp_core.setup.telemetry_models import (
    SessionData,
    BehaviorStatistics,
    SetupCorrelation,
    AnalysisResult,
)
from agp_core.setup.telemetry_analyzer import TelemetryAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class SessionSetupPair:
    """Pair of session data with corresponding setup."""
    session: SessionData
    setup: Setup
    behavior: BehaviorStatistics | None = None
    best_lap_time: float = 0.0


@dataclass
class ParameterRange:
    """Observed range of a setup parameter."""
    parameter_name: str
    min_value: float
    max_value: float
    optimal_value: float | None = None
    values: list[float] = field(default_factory=list)
    lap_times: list[float] = field(default_factory=list)


class SetupCorrelator:
    """
    Correlates setup parameters with performance metrics.

    Requires multiple sessions with different setups to find correlations
    between setup changes and performance outcomes.
    """

    def __init__(self):
        self.analyzer = TelemetryAnalyzer()
        self.sessions: list[SessionSetupPair] = []
        self.parameter_ranges: dict[str, ParameterRange] = {}

    def add_session(self, session: SessionData, setup: Setup) -> None:
        """Add a session with its corresponding setup for analysis."""
        # Analyze the session
        behavior = self.analyzer.analyze_session(session)

        pair = SessionSetupPair(
            session=session,
            setup=setup,
            behavior=behavior,
            best_lap_time=session.best_lap_time,
        )
        self.sessions.append(pair)

        # Update parameter ranges
        self._update_parameter_ranges(setup, session.best_lap_time)

        logger.info(f"Added session {session.session_id} with setup {setup.name}")

    def analyze_correlations(self) -> list[SetupCorrelation]:
        """
        Analyze correlations between setup parameters and performance.

        Returns list of correlations with statistical significance.
        """
        if len(self.sessions) < 2:
            logger.warning("Need at least 2 sessions to calculate correlations")
            return []

        correlations: list[SetupCorrelation] = []

        # Analyze each parameter
        for param_name, param_range in self.parameter_ranges.items():
            if len(param_range.values) < 2:
                continue

            correlation = self._calculate_parameter_correlation(param_name, param_range)
            if correlation:
                correlations.append(correlation)

        # Sort by confidence
        correlations.sort(key=lambda c: c.confidence, reverse=True)

        return correlations

    def get_optimal_setup_suggestions(self) -> dict[str, Any]:
        """
        Get suggestions for optimal setup based on correlations.

        Returns dictionary with parameter names and suggested values/directions.
        """
        correlations = self.analyze_correlations()

        suggestions: dict[str, Any] = {}

        for corr in correlations:
            if corr.confidence < 50:
                continue  # Not confident enough

            suggestions[corr.parameter_name] = {
                "current_value": corr.parameter_value,
                "suggested_direction": corr.suggested_direction,
                "suggested_change": corr.suggested_change,
                "confidence": corr.confidence,
                "lap_time_impact": corr.lap_time_correlation,
            }

        return suggestions

    def _update_parameter_ranges(self, setup: Setup, best_lap_time: float) -> None:
        """Update parameter ranges with values from a setup."""
        params = self._extract_setup_parameters(setup)

        for name, value in params.items():
            if name not in self.parameter_ranges:
                self.parameter_ranges[name] = ParameterRange(
                    parameter_name=name,
                    min_value=value,
                    max_value=value,
                )

            range_obj = self.parameter_ranges[name]
            range_obj.values.append(value)
            range_obj.lap_times.append(best_lap_time)
            range_obj.min_value = min(range_obj.min_value, value)
            range_obj.max_value = max(range_obj.max_value, value)

    def _extract_setup_parameters(self, setup: Setup) -> dict[str, float]:
        """Extract all numeric parameters from a setup."""
        params: dict[str, float] = {}

        if setup.suspension:
            susp = setup.suspension

            # Front suspension
            params["front_ride_height"] = susp.front_ride_height.mm
            params["rear_ride_height"] = susp.rear_ride_height.mm
            params["rake"] = susp.rake.mm
            params["front_arb"] = float(susp.front_arb)
            params["rear_arb"] = float(susp.rear_arb)
            params["front_camber"] = susp.front_camber_avg.degrees
            params["rear_camber"] = susp.rear_camber_avg.degrees
            params["front_toe"] = susp.front_toe.degrees
            params["rear_toe"] = susp.rear_toe.degrees

            # Individual corners
            for corner in [susp.front_left, susp.front_right, susp.rear_left, susp.rear_right]:
                prefix = corner.position.value.lower()
                params[f"{prefix}_spring"] = corner.spring_rate.nm
                params[f"{prefix}_slow_bump"] = float(corner.slow_bump)
                params[f"{prefix}_fast_bump"] = float(corner.fast_bump)
                params[f"{prefix}_slow_rebound"] = float(corner.slow_rebound)
                params[f"{prefix}_fast_rebound"] = float(corner.fast_rebound)
                params[f"{prefix}_pressure"] = corner.pressure.kpa

        if setup.differential:
            diff = setup.differential
            params["diff_power_lock"] = diff.power_lock.value
            params["diff_coast_lock"] = diff.coast_lock.value
            params["diff_preload"] = diff.preload

        if setup.brakes:
            params["brake_bias"] = setup.brakes.bias.value
            params["brake_pressure"] = setup.brakes.pressure.value

        if setup.aero:
            params["front_wing"] = float(setup.aero.front_wing)
            params["rear_wing"] = float(setup.aero.rear_wing)
            params["aero_balance"] = setup.aero.estimated_balance * 100

        return params

    def _calculate_parameter_correlation(
        self,
        param_name: str,
        param_range: ParameterRange
    ) -> SetupCorrelation | None:
        """Calculate correlation between a parameter and performance."""
        values = param_range.values
        lap_times = param_range.lap_times

        if len(values) < 2:
            return None

        # Calculate Pearson correlation coefficient
        n = len(values)
        sum_x = sum(values)
        sum_y = sum(lap_times)
        sum_xy = sum(x * y for x, y in zip(values, lap_times))
        sum_x2 = sum(x ** 2 for x in values)
        sum_y2 = sum(y ** 2 for y in lap_times)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt(
            (n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)
        )

        if denominator == 0:
            return None

        correlation = numerator / denominator

        # Current value (most recent)
        current_value = values[-1]

        # Determine optimal direction
        # Negative correlation = increasing value decreases lap time (good)
        # Positive correlation = increasing value increases lap time (bad)
        if abs(correlation) < 0.3:
            suggested_direction = "optimal"
            suggested_change = 0.0
        elif correlation < 0:
            # Negative correlation - increasing helps
            suggested_direction = "increase"
            suggested_change = (param_range.max_value - current_value) * 0.5
        else:
            # Positive correlation - decreasing helps
            suggested_direction = "decrease"
            suggested_change = (current_value - param_range.min_value) * 0.5

        # Confidence based on sample size and correlation strength
        confidence = min(100, abs(correlation) * 100 * math.log2(n + 1))

        # Find optimal value (value with best lap time)
        best_idx = lap_times.index(min(lap_times))
        param_range.optimal_value = values[best_idx]

        return SetupCorrelation(
            parameter_name=param_name,
            parameter_value=current_value,
            lap_time_correlation=correlation,
            confidence=confidence,
            sample_count=n,
            suggested_direction=suggested_direction,
            suggested_change=suggested_change,
        )

    def get_behavior_correlations(self) -> dict[str, list[SetupCorrelation]]:
        """
        Get correlations between setup parameters and driving behavior.

        Returns dict with behavior categories and their correlations.
        """
        if len(self.sessions) < 2:
            return {}

        results: dict[str, list[SetupCorrelation]] = {
            "understeer": [],
            "oversteer": [],
            "traction": [],
            "tire_wear": [],
        }

        # Extract behavior metrics
        for param_name, param_range in self.parameter_ranges.items():
            # Understeer correlation
            understeer_values = [
                s.behavior.understeer_tendency
                for s in self.sessions
                if s.behavior
            ]
            if understeer_values:
                corr = self._calculate_behavior_correlation(
                    param_name, param_range.values, understeer_values
                )
                if corr:
                    results["understeer"].append(corr)

            # Oversteer correlation
            oversteer_values = [
                s.behavior.oversteer_tendency
                for s in self.sessions
                if s.behavior
            ]
            if oversteer_values:
                corr = self._calculate_behavior_correlation(
                    param_name, param_range.values, oversteer_values
                )
                if corr:
                    results["oversteer"].append(corr)

            # Traction correlation
            traction_values = [
                s.behavior.traction_on_throttle
                for s in self.sessions
                if s.behavior
            ]
            if traction_values:
                corr = self._calculate_behavior_correlation(
                    param_name, param_range.values, traction_values
                )
                if corr:
                    results["traction"].append(corr)

        # Sort by confidence
        for key in results:
            results[key].sort(key=lambda c: c.confidence, reverse=True)

        return results

    def _calculate_behavior_correlation(
        self,
        param_name: str,
        param_values: list[float],
        behavior_values: list[float]
    ) -> SetupCorrelation | None:
        """Calculate correlation between parameter and behavior metric."""
        if len(param_values) != len(behavior_values) or len(param_values) < 2:
            return None

        n = len(param_values)
        sum_x = sum(param_values)
        sum_y = sum(behavior_values)
        sum_xy = sum(x * y for x, y in zip(param_values, behavior_values))
        sum_x2 = sum(x ** 2 for x in param_values)
        sum_y2 = sum(y ** 2 for y in behavior_values)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt(
            (n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)
        )

        if denominator == 0:
            return None

        correlation = numerator / denominator
        confidence = min(100, abs(correlation) * 100 * math.log2(n + 1))

        if confidence < 30:  # Too low confidence
            return None

        return SetupCorrelation(
            parameter_name=param_name,
            parameter_value=param_values[-1],
            balance_correlation=correlation,
            confidence=confidence,
            sample_count=n,
            suggested_direction="increase" if correlation < 0 else "decrease",
            suggested_change=0.0,
        )

    def generate_report(self) -> dict[str, Any]:
        """Generate comprehensive correlation report."""
        correlations = self.analyze_correlations()
        behavior_correlations = self.get_behavior_correlations()
        suggestions = self.get_optimal_setup_suggestions()

        return {
            "session_count": len(self.sessions),
            "parameter_count": len(self.parameter_ranges),
            "lap_time_correlations": [
                {
                    "parameter": c.parameter_name,
                    "correlation": c.lap_time_correlation,
                    "confidence": c.confidence,
                    "suggestion": c.suggested_direction,
                }
                for c in correlations[:10]  # Top 10
            ],
            "behavior_correlations": {
                key: [
                    {
                        "parameter": c.parameter_name,
                        "correlation": c.balance_correlation,
                        "confidence": c.confidence,
                    }
                    for c in corrs[:5]  # Top 5 per category
                ]
                for key, corrs in behavior_correlations.items()
            },
            "suggestions": suggestions,
            "sessions": [
                {
                    "name": s.session.session_id,
                    "setup": s.setup.name,
                    "best_lap": s.best_lap_time,
                    "understeer": s.behavior.understeer_tendency if s.behavior else 0,
                    "oversteer": s.behavior.oversteer_tendency if s.behavior else 0,
                }
                for s in self.sessions
            ],
        }
