"""Data models for strategy calculations"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class TireCompound(Enum):
    """Available tire compounds."""
    SOFT = "soft"
    MEDIUM = "medium"
    HARD = "hard"
    WET = "wet"
    INTERMEDIATE = "intermediate"


class PitStopType(Enum):
    """Type of pit stop."""
    FUEL_ONLY = "fuel_only"
    TIRES_ONLY = "tires_only"
    FUEL_AND_TIRES = "fuel_and_tires"
    DRIVER_CHANGE = "driver_change"
    REPAIR = "repair"


class WeatherCondition(Enum):
    """Weather conditions."""
    DRY = "dry"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"
    MIXED = "mixed"


@dataclass
class FuelState:
    """Current fuel state."""
    current_fuel: float  # liters
    tank_capacity: float  # liters
    consumption_per_lap: float  # liters/lap
    consumption_history: list[float] = field(default_factory=list)

    @property
    def fuel_percentage(self) -> float:
        """Fuel level as percentage."""
        if self.tank_capacity <= 0:
            return 0
        return (self.current_fuel / self.tank_capacity) * 100

    @property
    def laps_remaining(self) -> float:
        """Estimated laps remaining on current fuel."""
        if self.consumption_per_lap <= 0:
            return float('inf')
        return self.current_fuel / self.consumption_per_lap

    @property
    def average_consumption(self) -> float:
        """Average fuel consumption from history."""
        if not self.consumption_history:
            return self.consumption_per_lap
        return sum(self.consumption_history) / len(self.consumption_history)

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_fuel": self.current_fuel,
            "tank_capacity": self.tank_capacity,
            "fuel_percentage": self.fuel_percentage,
            "consumption_per_lap": self.consumption_per_lap,
            "average_consumption": self.average_consumption,
            "laps_remaining": self.laps_remaining,
        }


@dataclass
class TireState:
    """Current tire state for one set."""
    compound: TireCompound
    age_laps: int = 0
    wear_fl: float = 100.0  # percentage remaining
    wear_fr: float = 100.0
    wear_rl: float = 100.0
    wear_rr: float = 100.0
    temp_fl: float = 80.0  # celsius
    temp_fr: float = 80.0
    temp_rl: float = 80.0
    temp_rr: float = 80.0
    grip_level: float = 100.0  # percentage

    @property
    def average_wear(self) -> float:
        """Average wear across all tires."""
        return (self.wear_fl + self.wear_fr + self.wear_rl + self.wear_rr) / 4

    @property
    def worst_wear(self) -> float:
        """Worst (lowest) wear value."""
        return min(self.wear_fl, self.wear_fr, self.wear_rl, self.wear_rr)

    @property
    def estimated_laps_remaining(self) -> int:
        """Estimated laps before tires are worn out."""
        if self.age_laps == 0:
            return 50  # Default estimate
        wear_per_lap = (100 - self.average_wear) / self.age_laps
        if wear_per_lap <= 0:
            return 100
        remaining_wear = self.average_wear - 20  # 20% is minimum
        return int(remaining_wear / wear_per_lap)

    def to_dict(self) -> dict[str, Any]:
        return {
            "compound": self.compound.value,
            "age_laps": self.age_laps,
            "wear": {
                "fl": self.wear_fl,
                "fr": self.wear_fr,
                "rl": self.wear_rl,
                "rr": self.wear_rr,
                "average": self.average_wear,
                "worst": self.worst_wear,
            },
            "grip_level": self.grip_level,
            "estimated_laps_remaining": self.estimated_laps_remaining,
        }


@dataclass
class WeatherForecast:
    """Weather forecast for strategy planning."""
    current_condition: WeatherCondition
    track_temp: float
    air_temp: float
    rain_probability: float  # 0-1
    forecast_changes: list[tuple[int, WeatherCondition]] = field(default_factory=list)  # (lap, condition)

    def get_condition_at_lap(self, lap: int) -> WeatherCondition:
        """Get predicted weather at a specific lap."""
        condition = self.current_condition
        for change_lap, new_condition in self.forecast_changes:
            if lap >= change_lap:
                condition = new_condition
        return condition

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_condition": self.current_condition.value,
            "track_temp": self.track_temp,
            "air_temp": self.air_temp,
            "rain_probability": self.rain_probability,
            "forecast_changes": [(lap, cond.value) for lap, cond in self.forecast_changes],
        }


@dataclass
class PitStop:
    """Planned or completed pit stop."""
    lap: int
    stop_type: PitStopType
    fuel_to_add: float = 0.0  # liters
    tire_compound: TireCompound | None = None
    driver_in: str | None = None
    driver_out: str | None = None
    estimated_duration: float = 25.0  # seconds
    actual_duration: float | None = None
    completed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "lap": self.lap,
            "stop_type": self.stop_type.value,
            "fuel_to_add": self.fuel_to_add,
            "tire_compound": self.tire_compound.value if self.tire_compound else None,
            "driver_in": self.driver_in,
            "driver_out": self.driver_out,
            "estimated_duration": self.estimated_duration,
            "actual_duration": self.actual_duration,
            "completed": self.completed,
        }


@dataclass
class Stint:
    """A stint between pit stops."""
    stint_number: int
    driver: str
    start_lap: int
    end_lap: int | None = None
    tire_compound: TireCompound = TireCompound.MEDIUM
    fuel_start: float = 0.0
    fuel_end: float | None = None
    laps_completed: int = 0
    average_lap_time: float = 0.0
    best_lap_time: float = 0.0

    @property
    def planned_length(self) -> int | None:
        """Planned stint length in laps."""
        if self.end_lap is None:
            return None
        return self.end_lap - self.start_lap

    def to_dict(self) -> dict[str, Any]:
        return {
            "stint_number": self.stint_number,
            "driver": self.driver,
            "start_lap": self.start_lap,
            "end_lap": self.end_lap,
            "tire_compound": self.tire_compound.value,
            "fuel_start": self.fuel_start,
            "fuel_end": self.fuel_end,
            "laps_completed": self.laps_completed,
            "planned_length": self.planned_length,
            "average_lap_time": self.average_lap_time,
            "best_lap_time": self.best_lap_time,
        }


@dataclass
class StrategyPlan:
    """Complete race strategy plan."""
    race_laps: int
    race_duration: float  # hours
    pit_stops: list[PitStop] = field(default_factory=list)
    stints: list[Stint] = field(default_factory=list)
    drivers: list[str] = field(default_factory=list)

    # Constraints
    min_pit_stops: int = 0
    max_stint_time: float = 0  # hours, 0 = no limit
    min_driver_time: float = 0  # hours per driver
    max_driver_time: float = 0  # hours per driver

    # Current state
    current_lap: int = 0
    current_stint: int = 0
    elapsed_time: float = 0.0

    @property
    def laps_remaining(self) -> int:
        """Laps remaining in the race."""
        return max(0, self.race_laps - self.current_lap)

    @property
    def time_remaining(self) -> float:
        """Time remaining in hours."""
        return max(0, self.race_duration - self.elapsed_time)

    @property
    def next_pit_stop(self) -> PitStop | None:
        """Get next planned pit stop."""
        for stop in self.pit_stops:
            if not stop.completed and stop.lap > self.current_lap:
                return stop
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "race_laps": self.race_laps,
            "race_duration": self.race_duration,
            "pit_stops": [stop.to_dict() for stop in self.pit_stops],
            "stints": [stint.to_dict() for stint in self.stints],
            "drivers": self.drivers,
            "current_lap": self.current_lap,
            "current_stint": self.current_stint,
            "laps_remaining": self.laps_remaining,
            "time_remaining": self.time_remaining,
            "next_pit_stop": self.next_pit_stop.to_dict() if self.next_pit_stop else None,
        }
