"""Main strategy engine for race strategy planning and execution"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

from agp_core.strategy.models import (
    FuelState,
    TireState,
    TireCompound,
    WeatherForecast,
    WeatherCondition,
    PitStop,
    PitStopType,
    Stint,
    StrategyPlan,
)
from agp_core.strategy.fuel_calculator import FuelCalculator, FuelPrediction
from agp_core.strategy.tire_predictor import TirePredictor, TirePrediction


@dataclass
class StrategyRecommendation:
    """Strategy recommendation from the engine."""
    action: str  # "pit_now", "pit_soon", "stay_out", "prepare_wet"
    priority: int  # 1 = highest
    reason: str
    pit_stop: PitStop | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "priority": self.priority,
            "reason": self.reason,
            "pit_stop": self.pit_stop.to_dict() if self.pit_stop else None,
            "details": self.details,
        }


@dataclass
class UndercutAnalysis:
    """Analysis for undercut/overcut opportunities."""
    target_driver: str
    current_gap: float  # seconds
    can_undercut: bool
    undercut_window: tuple[int, int]  # (start_lap, end_lap)
    potential_gain: float  # seconds
    risk_level: str  # low, medium, high

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_driver": self.target_driver,
            "current_gap": self.current_gap,
            "can_undercut": self.can_undercut,
            "undercut_window": self.undercut_window,
            "potential_gain": self.potential_gain,
            "risk_level": self.risk_level,
        }


class StrategyEngine:
    """
    Main strategy engine that coordinates all strategy calculations.

    Combines fuel, tire, weather, and race position data to generate
    optimal pit stop strategies and real-time recommendations.
    """

    def __init__(self):
        self.fuel_calculator = FuelCalculator()
        self.tire_predictor = TirePredictor()

        # Current state
        self.fuel_state: FuelState | None = None
        self.tire_state: TireState | None = None
        self.weather: WeatherForecast | None = None
        self.strategy_plan: StrategyPlan | None = None

        # Race info
        self.current_lap: int = 0
        self.total_laps: int = 0
        self.race_duration_hours: float = 0
        self.average_lap_time: float = 120.0  # seconds
        self.pit_loss_time: float = 25.0  # seconds

        # Callbacks
        self.on_recommendation: Callable[[StrategyRecommendation], None] | None = None

    def update_fuel(self, fuel_state: FuelState) -> None:
        """Update current fuel state."""
        # Record consumption if we have previous data
        if self.fuel_state and fuel_state.current_fuel < self.fuel_state.current_fuel:
            consumption = self.fuel_state.current_fuel - fuel_state.current_fuel
            self.fuel_calculator.update_consumption(consumption)

        self.fuel_state = fuel_state

    def update_tires(self, tire_state: TireState) -> None:
        """Update current tire state."""
        if self.tire_state:
            self.tire_predictor.update_wear(self.current_lap, tire_state.average_wear)

        self.tire_state = tire_state
        self.tire_predictor.current_compound = tire_state.compound

    def update_weather(self, weather: WeatherForecast) -> None:
        """Update weather forecast."""
        self.weather = weather

    def update_lap(self, lap: int) -> None:
        """Update current lap number."""
        self.current_lap = lap

    def set_race_info(
        self,
        total_laps: int = 0,
        duration_hours: float = 0,
        average_lap_time: float = 120.0,
        pit_loss: float = 25.0,
    ) -> None:
        """Set race information."""
        self.total_laps = total_laps
        self.race_duration_hours = duration_hours
        self.average_lap_time = average_lap_time
        self.pit_loss_time = pit_loss

    def get_fuel_prediction(self) -> FuelPrediction | None:
        """Get current fuel prediction."""
        if not self.fuel_state:
            return None

        return self.fuel_calculator.predict(
            self.fuel_state,
            self.current_lap,
            self.total_laps,
            self.average_lap_time,
        )

    def get_tire_prediction(self) -> TirePrediction | None:
        """Get current tire prediction."""
        if not self.tire_state:
            return None

        fuel_window = None
        fuel_pred = self.get_fuel_prediction()
        if fuel_pred:
            fuel_window = (fuel_pred.pit_window_start, fuel_pred.pit_window_end)

        return self.tire_predictor.predict(
            self.tire_state,
            self.current_lap,
            self.total_laps,
            fuel_window,
        )

    def calculate_optimal_strategy(
        self,
        min_stops: int = 0,
        max_stops: int = 10,
        drivers: list[str] | None = None,
    ) -> StrategyPlan:
        """Calculate optimal pit stop strategy for the race."""
        drivers = drivers or ["Driver 1"]

        # Calculate number of stops needed
        if self.fuel_state:
            fuel_per_lap = self.fuel_calculator.get_average_consumption() or self.fuel_state.consumption_per_lap
            total_fuel_needed = self.total_laps * fuel_per_lap
            fuel_stops = max(0, int(total_fuel_needed / self.fuel_state.tank_capacity))
        else:
            fuel_stops = 0

        # Consider tire stops
        if self.tire_state:
            tire_life = self.tire_predictor.predict(
                self.tire_state, 0, self.total_laps
            ).laps_remaining
            tire_stops = max(0, int(self.total_laps / max(tire_life, 20)) - 1)
        else:
            tire_stops = 0

        num_stops = max(min_stops, fuel_stops, tire_stops, 1)
        num_stops = min(num_stops, max_stops)

        # Calculate stint lengths
        laps_per_stint = self.total_laps // (num_stops + 1)

        # Build strategy plan
        plan = StrategyPlan(
            race_laps=self.total_laps,
            race_duration=self.race_duration_hours,
            drivers=drivers,
            min_pit_stops=min_stops,
        )

        # Generate pit stops and stints
        current_lap = 0
        for i in range(num_stops):
            pit_lap = current_lap + laps_per_stint

            # Determine tire compound for next stint
            remaining = self.total_laps - pit_lap
            weather_at_pit = WeatherCondition.DRY
            if self.weather:
                weather_at_pit = self.weather.get_condition_at_lap(pit_lap)

            compound = self.tire_predictor.suggest_compound(
                remaining,
                weather_at_pit,
                self.weather.track_temp if self.weather else 25.0,
            )

            # Calculate fuel to add
            fuel_to_add = 0.0
            if self.fuel_state:
                laps_to_next = laps_per_stint if i < num_stops - 1 else self.total_laps - pit_lap
                fuel_to_add = self.fuel_calculator.calculate_fuel_for_laps(
                    laps_to_next,
                    self.fuel_state,
                )

            pit_stop = PitStop(
                lap=pit_lap,
                stop_type=PitStopType.FUEL_AND_TIRES,
                fuel_to_add=fuel_to_add,
                tire_compound=compound,
                estimated_duration=self.pit_loss_time,
            )
            plan.pit_stops.append(pit_stop)

            # Create stint
            stint = Stint(
                stint_number=i + 1,
                driver=drivers[i % len(drivers)],
                start_lap=current_lap,
                end_lap=pit_lap,
                tire_compound=self.tire_state.compound if self.tire_state else TireCompound.MEDIUM,
            )
            plan.stints.append(stint)

            current_lap = pit_lap

        # Final stint
        final_stint = Stint(
            stint_number=num_stops + 1,
            driver=drivers[num_stops % len(drivers)],
            start_lap=current_lap,
            end_lap=self.total_laps,
        )
        plan.stints.append(final_stint)

        self.strategy_plan = plan
        return plan

    def analyze_undercut(
        self,
        target_driver: str,
        gap_to_target: float,
        target_tire_age: int = 0,
    ) -> UndercutAnalysis:
        """Analyze undercut opportunity against a target driver."""
        # Undercut works best when:
        # 1. Gap is within pit loss window
        # 2. Target has older tires
        # 3. We haven't pitted recently

        can_undercut = False
        potential_gain = 0.0
        risk = "medium"

        tire_pred = self.get_tire_prediction()
        fuel_pred = self.get_fuel_prediction()

        # Check if undercut is feasible
        if gap_to_target < self.pit_loss_time * 1.5:
            # Close enough for undercut
            if tire_pred and target_tire_age > self.tire_state.age_laps + 5:
                # Target has older tires
                can_undercut = True
                # Fresh tire advantage ~0.5s per lap
                laps_until_target_pits = max(1, target_tire_age - 30)  # Assume they pit soon
                potential_gain = 0.5 * laps_until_target_pits
                risk = "low" if potential_gain > gap_to_target else "medium"

        window_start = self.current_lap + 1
        window_end = self.current_lap + 5

        if fuel_pred:
            window_start = max(window_start, fuel_pred.pit_window_start)
            window_end = min(window_end, fuel_pred.pit_window_end)

        return UndercutAnalysis(
            target_driver=target_driver,
            current_gap=gap_to_target,
            can_undercut=can_undercut,
            undercut_window=(window_start, window_end),
            potential_gain=potential_gain,
            risk_level=risk,
        )

    def get_recommendations(self) -> list[StrategyRecommendation]:
        """Get current strategy recommendations."""
        recommendations = []

        fuel_pred = self.get_fuel_prediction()
        tire_pred = self.get_tire_prediction()

        # Critical fuel warning
        if fuel_pred and fuel_pred.is_critical:
            recommendations.append(StrategyRecommendation(
                action="pit_now",
                priority=1,
                reason="Carburant critique - pit immediat requis",
                pit_stop=PitStop(
                    lap=self.current_lap + 1,
                    stop_type=PitStopType.FUEL_ONLY,
                    fuel_to_add=fuel_pred.recommended_fuel_add,
                ),
                details={"fuel_laps_remaining": fuel_pred.laps_remaining}
            ))

        # Critical tire warning
        if tire_pred and self.tire_state and self.tire_state.average_wear < 30:
            recommendations.append(StrategyRecommendation(
                action="pit_now",
                priority=1,
                reason="Pneus critiques - pit immediat recommande",
                pit_stop=PitStop(
                    lap=self.current_lap + 1,
                    stop_type=PitStopType.TIRES_ONLY,
                    tire_compound=self.tire_predictor.suggest_compound(
                        self.total_laps - self.current_lap,
                        self.weather.current_condition if self.weather else WeatherCondition.DRY,
                        self.weather.track_temp if self.weather else 25.0,
                    ),
                ),
                details={"tire_wear": self.tire_state.average_wear}
            ))

        # Weather change incoming
        if self.weather and self.weather.rain_probability > 0.7:
            recommendations.append(StrategyRecommendation(
                action="prepare_wet",
                priority=2,
                reason="Pluie probable - preparer pneus pluie",
                details={"rain_probability": self.weather.rain_probability}
            ))

        # Optimal pit window
        if fuel_pred and tire_pred:
            in_fuel_window = fuel_pred.pit_window_start <= self.current_lap <= fuel_pred.pit_window_end
            near_tire_optimal = abs(tire_pred.optimal_pit_lap - self.current_lap) <= 3

            if in_fuel_window and near_tire_optimal:
                compound = self.tire_predictor.suggest_compound(
                    self.total_laps - self.current_lap,
                    self.weather.current_condition if self.weather else WeatherCondition.DRY,
                    self.weather.track_temp if self.weather else 25.0,
                )

                recommendations.append(StrategyRecommendation(
                    action="pit_soon",
                    priority=3,
                    reason="Fenetre optimale de pit stop",
                    pit_stop=PitStop(
                        lap=self.current_lap + 2,
                        stop_type=PitStopType.FUEL_AND_TIRES,
                        fuel_to_add=fuel_pred.recommended_fuel_add,
                        tire_compound=compound,
                    ),
                    details={
                        "fuel_window": (fuel_pred.pit_window_start, fuel_pred.pit_window_end),
                        "tire_optimal": tire_pred.optimal_pit_lap,
                    }
                ))

        # Default: stay out
        if not recommendations:
            recommendations.append(StrategyRecommendation(
                action="stay_out",
                priority=10,
                reason="Continuer le stint actuel",
                details={
                    "fuel_laps": fuel_pred.laps_remaining if fuel_pred else None,
                    "tire_laps": tire_pred.laps_remaining if tire_pred else None,
                }
            ))

        return sorted(recommendations, key=lambda r: r.priority)

    def to_dict(self) -> dict[str, Any]:
        """Export current state as dictionary."""
        return {
            "current_lap": self.current_lap,
            "total_laps": self.total_laps,
            "fuel": self.fuel_state.to_dict() if self.fuel_state else None,
            "tires": self.tire_state.to_dict() if self.tire_state else None,
            "weather": self.weather.to_dict() if self.weather else None,
            "fuel_prediction": self.get_fuel_prediction().to_dict() if self.get_fuel_prediction() else None,
            "tire_prediction": self.get_tire_prediction().to_dict() if self.get_tire_prediction() else None,
            "strategy_plan": self.strategy_plan.to_dict() if self.strategy_plan else None,
            "recommendations": [r.to_dict() for r in self.get_recommendations()],
        }
