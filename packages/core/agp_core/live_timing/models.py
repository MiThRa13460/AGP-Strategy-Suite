"""Data models for live timing"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ThreatLevel(Enum):
    """Threat level for opponents."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SessionType(Enum):
    """Type of racing session."""
    PRACTICE = "practice"
    QUALIFYING = "qualifying"
    WARMUP = "warmup"
    RACE = "race"


class PitStatus(Enum):
    """Pit status for a driver."""
    ON_TRACK = "on_track"
    IN_PIT_LANE = "in_pit_lane"
    IN_GARAGE = "in_garage"


@dataclass
class LapTime:
    """Lap time with sector information."""
    total: float  # seconds
    sector1: float | None = None
    sector2: float | None = None
    sector3: float | None = None
    is_valid: bool = True
    is_personal_best: bool = False
    is_session_best: bool = False

    def __str__(self) -> str:
        if self.total <= 0:
            return "--:--.---"
        mins = int(self.total // 60)
        secs = self.total % 60
        return f"{mins}:{secs:06.3f}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "formatted": str(self),
            "sector1": self.sector1,
            "sector2": self.sector2,
            "sector3": self.sector3,
            "is_valid": self.is_valid,
            "is_personal_best": self.is_personal_best,
            "is_session_best": self.is_session_best,
        }


@dataclass
class Driver:
    """Driver information."""
    id: str
    name: str
    car_number: str = ""
    car_class: str = ""
    car_name: str = ""
    team: str = ""
    is_player: bool = False

    # Performance stats
    best_lap: LapTime | None = None
    last_lap: LapTime | None = None
    current_sector: int = 0
    sector_times: list[float] = field(default_factory=list)

    # Position
    position: int = 0
    class_position: int = 0
    laps_completed: int = 0

    # Status
    pit_status: PitStatus = PitStatus.ON_TRACK
    pit_stops: int = 0
    in_pit: bool = False

    # Gaps
    gap_to_leader: float = 0.0
    gap_to_ahead: float = 0.0
    gap_to_player: float = 0.0

    # Threat analysis
    threat_level: ThreatLevel = ThreatLevel.NONE
    pace_delta: float = 0.0  # vs player, negative = faster

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "car_number": self.car_number,
            "car_class": self.car_class,
            "car_name": self.car_name,
            "team": self.team,
            "is_player": self.is_player,
            "best_lap": self.best_lap.to_dict() if self.best_lap else None,
            "last_lap": self.last_lap.to_dict() if self.last_lap else None,
            "position": self.position,
            "class_position": self.class_position,
            "laps_completed": self.laps_completed,
            "pit_status": self.pit_status.value,
            "pit_stops": self.pit_stops,
            "in_pit": self.in_pit,
            "gap_to_leader": self.gap_to_leader,
            "gap_to_ahead": self.gap_to_ahead,
            "gap_to_player": self.gap_to_player,
            "threat_level": self.threat_level.value,
            "pace_delta": self.pace_delta,
        }


@dataclass
class Standing:
    """Race standings entry."""
    position: int
    driver: Driver
    gap_to_leader: float | str  # Can be laps like "+1 Lap"
    gap_to_ahead: float | str
    interval: float  # Time gap to car ahead
    last_lap: LapTime | None
    best_lap: LapTime | None
    laps: int
    pit_stops: int
    status: str = "running"  # running, pit, dnf, dsq

    def to_dict(self) -> dict[str, Any]:
        return {
            "position": self.position,
            "driver": self.driver.to_dict(),
            "gap_to_leader": self.gap_to_leader,
            "gap_to_ahead": self.gap_to_ahead,
            "interval": self.interval,
            "last_lap": self.last_lap.to_dict() if self.last_lap else None,
            "best_lap": self.best_lap.to_dict() if self.best_lap else None,
            "laps": self.laps,
            "pit_stops": self.pit_stops,
            "status": self.status,
        }


@dataclass
class SessionInfo:
    """Current session information."""
    session_type: SessionType
    session_name: str = ""
    track_name: str = ""
    track_length: float = 0.0  # meters

    # Time
    elapsed_time: float = 0.0
    remaining_time: float = 0.0
    total_time: float = 0.0

    # Laps
    current_lap: int = 0
    total_laps: int = 0

    # Conditions
    air_temp: float = 20.0
    track_temp: float = 25.0
    humidity: float = 50.0
    rain: float = 0.0  # 0-1

    # Flags
    flag: str = "green"  # green, yellow, red, white, checkered

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_type": self.session_type.value,
            "session_name": self.session_name,
            "track_name": self.track_name,
            "track_length": self.track_length,
            "elapsed_time": self.elapsed_time,
            "remaining_time": self.remaining_time,
            "total_time": self.total_time,
            "current_lap": self.current_lap,
            "total_laps": self.total_laps,
            "air_temp": self.air_temp,
            "track_temp": self.track_temp,
            "humidity": self.humidity,
            "rain": self.rain,
            "flag": self.flag,
        }


@dataclass
class GapAnalysis:
    """Gap analysis between two drivers."""
    driver_id: str
    target_id: str
    current_gap: float  # seconds
    gap_trend: float  # positive = increasing, negative = closing
    projected_catch_lap: int | None = None
    pace_difference: float = 0.0  # seconds per lap

    def to_dict(self) -> dict[str, Any]:
        return {
            "driver_id": self.driver_id,
            "target_id": self.target_id,
            "current_gap": self.current_gap,
            "gap_trend": self.gap_trend,
            "projected_catch_lap": self.projected_catch_lap,
            "pace_difference": self.pace_difference,
        }
