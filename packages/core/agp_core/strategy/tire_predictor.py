"""Tire degradation prediction for race strategy"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from agp_core.strategy.models import TireState, TireCompound, WeatherCondition


@dataclass
class TirePrediction:
    """Tire life prediction result."""
    laps_remaining: int
    optimal_pit_lap: int
    grip_at_pit: float  # Predicted grip level at optimal pit lap
    lap_time_loss: float  # Cumulative time loss from degradation
    wear_rate: float  # Wear per lap
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "laps_remaining": self.laps_remaining,
            "optimal_pit_lap": self.optimal_pit_lap,
            "grip_at_pit": self.grip_at_pit,
            "lap_time_loss": self.lap_time_loss,
            "wear_rate": self.wear_rate,
            "recommendation": self.recommendation,
        }


class TirePredictor:
    """Predictor for tire degradation and optimal pit timing."""

    # Base degradation rates per compound (% per lap)
    DEGRADATION_RATES = {
        TireCompound.SOFT: 2.5,
        TireCompound.MEDIUM: 1.8,
        TireCompound.HARD: 1.2,
        TireCompound.INTERMEDIATE: 2.0,
        TireCompound.WET: 1.5,
    }

    # Grip vs wear curves (wear% -> grip multiplier)
    GRIP_CURVE = [
        (100, 1.00),  # New tire
        (90, 0.99),
        (80, 0.97),
        (70, 0.94),
        (60, 0.90),
        (50, 0.85),
        (40, 0.78),
        (30, 0.70),
        (20, 0.60),  # Cliff
    ]

    # Lap time loss per grip % lost (seconds)
    TIME_LOSS_PER_GRIP_PERCENT = 0.03

    def __init__(self):
        self.wear_history: list[tuple[int, float]] = []  # (lap, wear)
        self.current_compound: TireCompound = TireCompound.MEDIUM

    def update_wear(self, lap: int, average_wear: float) -> None:
        """Record tire wear for a lap."""
        self.wear_history.append((lap, average_wear))
        # Keep last 30 data points
        self.wear_history = self.wear_history[-30:]

    def get_wear_rate(self, tire_state: TireState) -> float:
        """Calculate actual wear rate from history or use defaults."""
        if len(self.wear_history) < 3:
            return self.DEGRADATION_RATES.get(tire_state.compound, 1.8)

        # Calculate from recent history
        recent = self.wear_history[-5:]
        if len(recent) < 2:
            return self.DEGRADATION_RATES.get(tire_state.compound, 1.8)

        total_wear = recent[0][1] - recent[-1][1]
        total_laps = recent[-1][0] - recent[0][0]

        if total_laps <= 0:
            return self.DEGRADATION_RATES.get(tire_state.compound, 1.8)

        return abs(total_wear / total_laps)

    def get_grip_for_wear(self, wear_percent: float) -> float:
        """Get grip multiplier for a given wear level."""
        for i, (wear, grip) in enumerate(self.GRIP_CURVE):
            if wear_percent >= wear:
                if i == 0:
                    return grip
                # Interpolate
                prev_wear, prev_grip = self.GRIP_CURVE[i - 1]
                ratio = (prev_wear - wear_percent) / (prev_wear - wear)
                return prev_grip - (prev_grip - grip) * ratio

        return 0.60  # Below minimum

    def predict_wear_at_lap(self, tire_state: TireState, laps_ahead: int) -> float:
        """Predict wear level at a future lap."""
        wear_rate = self.get_wear_rate(tire_state)
        predicted_wear = tire_state.average_wear - (wear_rate * laps_ahead)
        return max(0, predicted_wear)

    def calculate_optimal_pit_lap(
        self,
        tire_state: TireState,
        current_lap: int,
        total_laps: int,
        fuel_pit_window: tuple[int, int] | None = None,
    ) -> int:
        """Calculate optimal lap to pit based on tire degradation."""
        wear_rate = self.get_wear_rate(tire_state)

        # Find lap where grip drops below acceptable level (85%)
        target_grip = 0.85
        laps_to_target = 0

        for lap_offset in range(1, total_laps - current_lap + 1):
            predicted_wear = tire_state.average_wear - (wear_rate * lap_offset)
            grip = self.get_grip_for_wear(predicted_wear)

            if grip < target_grip:
                laps_to_target = lap_offset
                break
            laps_to_target = lap_offset

        optimal_lap = current_lap + laps_to_target

        # Consider fuel window if provided
        if fuel_pit_window:
            fuel_start, fuel_end = fuel_pit_window
            # Prefer to pit when both fuel and tires align
            if fuel_start <= optimal_lap <= fuel_end:
                pass  # Already in fuel window
            elif optimal_lap < fuel_start:
                # Tires want to pit earlier than fuel allows
                optimal_lap = fuel_start
            elif optimal_lap > fuel_end:
                # Must pit for fuel before tires
                optimal_lap = fuel_end

        return min(optimal_lap, total_laps - 1)

    def calculate_time_loss(self, tire_state: TireState, laps: int) -> float:
        """Calculate cumulative lap time loss over given laps."""
        total_loss = 0.0
        wear_rate = self.get_wear_rate(tire_state)
        current_wear = tire_state.average_wear

        for lap in range(laps):
            grip = self.get_grip_for_wear(current_wear)
            grip_loss = 1.0 - grip
            lap_loss = grip_loss * 100 * self.TIME_LOSS_PER_GRIP_PERCENT
            total_loss += lap_loss
            current_wear -= wear_rate

        return total_loss

    def predict(
        self,
        tire_state: TireState,
        current_lap: int,
        total_laps: int,
        fuel_pit_window: tuple[int, int] | None = None,
    ) -> TirePrediction:
        """Generate complete tire prediction."""
        wear_rate = self.get_wear_rate(tire_state)

        # Calculate laps until cliff (20% wear)
        cliff_threshold = 20.0
        laps_to_cliff = max(0, int((tire_state.average_wear - cliff_threshold) / wear_rate))
        laps_remaining = min(laps_to_cliff, total_laps - current_lap)

        # Calculate optimal pit lap
        optimal_pit = self.calculate_optimal_pit_lap(
            tire_state, current_lap, total_laps, fuel_pit_window
        )

        # Grip at optimal pit lap
        laps_to_pit = optimal_pit - current_lap
        wear_at_pit = self.predict_wear_at_lap(tire_state, laps_to_pit)
        grip_at_pit = self.get_grip_for_wear(wear_at_pit) * 100

        # Time loss calculation
        time_loss = self.calculate_time_loss(tire_state, laps_to_pit)

        # Generate recommendation
        if tire_state.average_wear < 30:
            recommendation = "CRITIQUE: Pneus uses, pit immediat recommande"
        elif tire_state.average_wear < 50:
            recommendation = "Pneus degrades, preparer le pit stop"
        elif laps_to_pit <= 3:
            recommendation = f"Fenetre de pit dans {laps_to_pit} tours"
        else:
            recommendation = f"Pneus OK, prochain pit tour ~{optimal_pit}"

        return TirePrediction(
            laps_remaining=laps_remaining,
            optimal_pit_lap=optimal_pit,
            grip_at_pit=grip_at_pit,
            lap_time_loss=time_loss,
            wear_rate=wear_rate,
            recommendation=recommendation,
        )

    def suggest_compound(
        self,
        laps_remaining: int,
        weather: WeatherCondition,
        track_temp: float,
    ) -> TireCompound:
        """Suggest tire compound for next stint."""
        # Wet conditions
        if weather == WeatherCondition.HEAVY_RAIN:
            return TireCompound.WET
        if weather == WeatherCondition.LIGHT_RAIN:
            return TireCompound.INTERMEDIATE

        # Dry conditions - based on stint length and track temp
        if laps_remaining <= 15:
            return TireCompound.SOFT
        elif laps_remaining <= 30:
            if track_temp > 35:
                return TireCompound.HARD
            return TireCompound.MEDIUM
        else:
            if track_temp > 30:
                return TireCompound.HARD
            return TireCompound.MEDIUM
