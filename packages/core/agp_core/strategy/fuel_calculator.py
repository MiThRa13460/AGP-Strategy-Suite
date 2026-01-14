"""Fuel calculations for race strategy"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from agp_core.strategy.models import FuelState, PitStop, PitStopType


@dataclass
class FuelPrediction:
    """Fuel prediction result."""
    laps_remaining: float
    pit_window_start: int  # Earliest optimal pit lap
    pit_window_end: int    # Latest safe pit lap
    fuel_needed_to_finish: float
    recommended_fuel_add: float
    is_critical: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "laps_remaining": self.laps_remaining,
            "pit_window_start": self.pit_window_start,
            "pit_window_end": self.pit_window_end,
            "fuel_needed_to_finish": self.fuel_needed_to_finish,
            "recommended_fuel_add": self.recommended_fuel_add,
            "is_critical": self.is_critical,
        }


class FuelCalculator:
    """Calculator for fuel strategy."""

    def __init__(self):
        self.consumption_history: list[float] = []
        self.safety_margin_laps: float = 1.5  # Extra laps of fuel as safety

    def update_consumption(self, fuel_used: float) -> None:
        """Record fuel consumption for a lap."""
        if fuel_used > 0:
            self.consumption_history.append(fuel_used)
            # Keep last 20 laps
            self.consumption_history = self.consumption_history[-20:]

    def get_average_consumption(self) -> float:
        """Get average fuel consumption per lap."""
        if not self.consumption_history:
            return 0
        return sum(self.consumption_history) / len(self.consumption_history)

    def get_consumption_trend(self) -> float:
        """
        Get consumption trend.
        Positive = increasing consumption
        Negative = decreasing consumption
        """
        if len(self.consumption_history) < 5:
            return 0

        recent = self.consumption_history[-5:]
        older = self.consumption_history[-10:-5] if len(self.consumption_history) >= 10 else self.consumption_history[:5]

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)

        return recent_avg - older_avg

    def calculate_laps_remaining(self, fuel_state: FuelState) -> float:
        """Calculate laps remaining on current fuel."""
        consumption = self.get_average_consumption() or fuel_state.consumption_per_lap
        if consumption <= 0:
            return float('inf')

        # Account for consumption trend
        trend = self.get_consumption_trend()
        adjusted_consumption = consumption + (trend * 0.5)  # Partial trend adjustment

        return fuel_state.current_fuel / max(adjusted_consumption, 0.1)

    def calculate_pit_window(
        self,
        fuel_state: FuelState,
        current_lap: int,
        total_laps: int,
        pit_loss_seconds: float = 25.0,
        lap_time_seconds: float = 120.0,
    ) -> tuple[int, int]:
        """
        Calculate optimal pit window.

        Returns (earliest_lap, latest_lap) for pitting.
        """
        laps_remaining = self.calculate_laps_remaining(fuel_state)

        # Latest safe lap to pit (with safety margin)
        latest_lap = current_lap + int(laps_remaining - self.safety_margin_laps)

        # For strategy, calculate if we should pit early for undercut
        pit_loss_laps = pit_loss_seconds / lap_time_seconds

        # Earliest optimal is when tire deg or fuel makes pitting worthwhile
        # This is simplified - real calculation would consider tire state
        laps_to_half_tank = (fuel_state.tank_capacity / 2) / (self.get_average_consumption() or 3.0)
        earliest_lap = current_lap + max(5, int(laps_to_half_tank * 0.7))

        # Ensure window is valid
        latest_lap = min(latest_lap, total_laps - 1)
        earliest_lap = min(earliest_lap, latest_lap - 3)

        return (max(current_lap + 1, earliest_lap), latest_lap)

    def calculate_fuel_for_laps(
        self,
        laps: int,
        fuel_state: FuelState,
        include_safety: bool = True,
    ) -> float:
        """Calculate fuel needed for a given number of laps."""
        consumption = self.get_average_consumption() or fuel_state.consumption_per_lap
        base_fuel = laps * consumption

        if include_safety:
            base_fuel += self.safety_margin_laps * consumption

        return base_fuel

    def calculate_optimal_fuel_add(
        self,
        fuel_state: FuelState,
        laps_to_end: int,
        next_pit_lap: int | None = None,
    ) -> float:
        """Calculate optimal amount of fuel to add at pit stop."""
        consumption = self.get_average_consumption() or fuel_state.consumption_per_lap

        if next_pit_lap is not None:
            # Fuel to next pit stop
            target_laps = next_pit_lap
        else:
            # Fuel to end of race
            target_laps = laps_to_end

        fuel_needed = (target_laps * consumption) + (self.safety_margin_laps * consumption)
        fuel_to_add = fuel_needed - fuel_state.current_fuel

        # Don't exceed tank capacity
        max_add = fuel_state.tank_capacity - fuel_state.current_fuel
        fuel_to_add = min(fuel_to_add, max_add)

        return max(0, fuel_to_add)

    def predict(
        self,
        fuel_state: FuelState,
        current_lap: int,
        total_laps: int,
        lap_time: float = 120.0,
    ) -> FuelPrediction:
        """Generate complete fuel prediction."""
        laps_remaining = self.calculate_laps_remaining(fuel_state)
        pit_window = self.calculate_pit_window(
            fuel_state, current_lap, total_laps,
            lap_time_seconds=lap_time
        )

        race_laps_remaining = total_laps - current_lap
        fuel_needed = self.calculate_fuel_for_laps(race_laps_remaining, fuel_state)
        recommended_add = self.calculate_optimal_fuel_add(fuel_state, race_laps_remaining)

        is_critical = laps_remaining < 3 or (laps_remaining < race_laps_remaining and pit_window[1] <= current_lap + 2)

        return FuelPrediction(
            laps_remaining=laps_remaining,
            pit_window_start=pit_window[0],
            pit_window_end=pit_window[1],
            fuel_needed_to_finish=fuel_needed,
            recommended_fuel_add=recommended_add,
            is_critical=is_critical,
        )

    def suggest_pit_stop(
        self,
        fuel_state: FuelState,
        current_lap: int,
        total_laps: int,
    ) -> PitStop | None:
        """Suggest a pit stop if needed."""
        prediction = self.predict(fuel_state, current_lap, total_laps)

        if prediction.is_critical:
            return PitStop(
                lap=current_lap + 1,
                stop_type=PitStopType.FUEL_ONLY,
                fuel_to_add=prediction.recommended_fuel_add,
                estimated_duration=12.0 + (prediction.recommended_fuel_add * 0.15),
            )

        # Suggest pit if in optimal window
        if prediction.pit_window_start <= current_lap <= prediction.pit_window_end:
            # Only suggest if we're past halfway through the window
            window_progress = (current_lap - prediction.pit_window_start) / max(1, prediction.pit_window_end - prediction.pit_window_start)
            if window_progress > 0.5:
                return PitStop(
                    lap=current_lap + 2,
                    stop_type=PitStopType.FUEL_AND_TIRES,
                    fuel_to_add=prediction.recommended_fuel_add,
                    estimated_duration=25.0,
                )

        return None
