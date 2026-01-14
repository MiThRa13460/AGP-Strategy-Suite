"""Telemetry data models for CSV analysis"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from pathlib import Path
import numpy as np


class CornerType(Enum):
    """Type of corner based on characteristics."""
    SLOW = "slow"          # < 80 km/h
    MEDIUM = "medium"      # 80-140 km/h
    FAST = "fast"          # 140-200 km/h
    VERY_FAST = "very_fast"  # > 200 km/h
    CHICANE = "chicane"
    HAIRPIN = "hairpin"


class CornerDirection(Enum):
    """Direction of the corner."""
    LEFT = "left"
    RIGHT = "right"


class CornerPhase(Enum):
    """Phase within a corner."""
    APPROACH = "approach"
    BRAKE_ZONE = "brake_zone"
    TRAIL_BRAKE = "trail_brake"
    TURN_IN = "turn_in"
    APEX = "apex"
    MID_CORNER = "mid_corner"
    EXIT = "exit"
    ACCELERATION = "acceleration"


@dataclass
class TelemetryPoint:
    """Single telemetry sample point."""

    timestamp: float  # seconds from start
    distance: float   # meters from start/finish
    lap: int

    # Vehicle state
    speed: float      # km/h
    rpm: int
    gear: int

    # Inputs
    throttle: float   # 0-100
    brake: float      # 0-100
    steering: float   # degrees (- = left, + = right)
    clutch: float     # 0-100

    # Forces
    g_lat: float      # lateral G
    g_long: float     # longitudinal G

    # Tires
    tire_temp_fl: float
    tire_temp_fr: float
    tire_temp_rl: float
    tire_temp_rr: float

    tire_pressure_fl: float
    tire_pressure_fr: float
    tire_pressure_rl: float
    tire_pressure_rr: float

    tire_wear_fl: float
    tire_wear_fr: float
    tire_wear_rl: float
    tire_wear_rr: float

    # Slip
    slip_angle_fl: float = 0.0
    slip_angle_fr: float = 0.0
    slip_angle_rl: float = 0.0
    slip_angle_rr: float = 0.0

    slip_ratio_fl: float = 0.0
    slip_ratio_fr: float = 0.0
    slip_ratio_rl: float = 0.0
    slip_ratio_rr: float = 0.0

    # Suspension
    ride_height_fl: float = 0.0
    ride_height_fr: float = 0.0
    ride_height_rl: float = 0.0
    ride_height_rr: float = 0.0

    susp_travel_fl: float = 0.0
    susp_travel_fr: float = 0.0
    susp_travel_rl: float = 0.0
    susp_travel_rr: float = 0.0

    # Additional
    fuel: float = 0.0
    brake_temp_fl: float = 0.0
    brake_temp_fr: float = 0.0
    brake_temp_rl: float = 0.0
    brake_temp_rr: float = 0.0

    # Calculated
    corner_phase: CornerPhase | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "distance": self.distance,
            "lap": self.lap,
            "speed": self.speed,
            "rpm": self.rpm,
            "gear": self.gear,
            "throttle": self.throttle,
            "brake": self.brake,
            "steering": self.steering,
            "g_lat": self.g_lat,
            "g_long": self.g_long,
        }


@dataclass
class CornerAnalysis:
    """Analysis results for a single corner."""

    corner_id: int
    corner_name: str
    corner_type: CornerType
    direction: CornerDirection

    # Distance markers
    start_distance: float
    apex_distance: float
    end_distance: float

    # Speed profile
    entry_speed: float
    min_speed: float
    apex_speed: float
    exit_speed: float

    # Braking analysis
    brake_point_distance: float
    brake_pressure_max: float
    brake_duration: float
    trail_brake_duration: float

    # Behavior detection
    understeer_detected: bool = False
    understeer_severity: float = 0.0  # 0-100
    understeer_phase: CornerPhase | None = None

    oversteer_detected: bool = False
    oversteer_severity: float = 0.0   # 0-100
    oversteer_phase: CornerPhase | None = None

    traction_loss_detected: bool = False
    traction_loss_severity: float = 0.0

    # Tire analysis
    tire_temp_front_avg: float = 0.0
    tire_temp_rear_avg: float = 0.0
    slip_angle_front_max: float = 0.0
    slip_angle_rear_max: float = 0.0

    # Time
    time_through_corner: float = 0.0
    theoretical_time: float = 0.0
    time_loss: float = 0.0

    # G-Force
    max_lat_g: float = 0.0
    max_brake_g: float = 0.0
    max_accel_g: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "corner_id": self.corner_id,
            "corner_name": self.corner_name,
            "corner_type": self.corner_type.value,
            "direction": self.direction.value,
            "entry_speed": self.entry_speed,
            "min_speed": self.min_speed,
            "exit_speed": self.exit_speed,
            "understeer_severity": self.understeer_severity,
            "oversteer_severity": self.oversteer_severity,
            "time_loss": self.time_loss,
        }


@dataclass
class LapData:
    """Complete lap telemetry data."""

    lap_number: int
    lap_time: float  # seconds
    is_valid: bool = True
    is_outlap: bool = False
    is_inlap: bool = False

    # Lap classification
    sector_1_time: float = 0.0
    sector_2_time: float = 0.0
    sector_3_time: float = 0.0

    # Aggregated stats
    max_speed: float = 0.0
    avg_speed: float = 0.0
    fuel_used: float = 0.0

    # Tire state at end of lap
    tire_wear_fl: float = 100.0
    tire_wear_fr: float = 100.0
    tire_wear_rl: float = 100.0
    tire_wear_rr: float = 100.0

    tire_temp_fl_avg: float = 0.0
    tire_temp_fr_avg: float = 0.0
    tire_temp_rl_avg: float = 0.0
    tire_temp_rr_avg: float = 0.0

    # Behavior stats (% of lap with issue)
    understeer_percentage: float = 0.0
    oversteer_percentage: float = 0.0
    traction_loss_percentage: float = 0.0
    brake_lock_percentage: float = 0.0

    # Corner analyses
    corners: list[CornerAnalysis] = field(default_factory=list)

    # Raw data reference
    data_points: list[TelemetryPoint] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "lap_number": self.lap_number,
            "lap_time": self.lap_time,
            "is_valid": self.is_valid,
            "max_speed": self.max_speed,
            "avg_speed": self.avg_speed,
            "understeer_percentage": self.understeer_percentage,
            "oversteer_percentage": self.oversteer_percentage,
            "corners": [c.to_dict() for c in self.corners],
        }


@dataclass
class SessionData:
    """Complete session telemetry data."""

    session_id: str
    session_type: str  # practice, qualifying, race

    # Metadata
    track_name: str = ""
    track_length: float = 0.0  # meters
    car_name: str = ""
    driver_name: str = ""

    date: datetime = field(default_factory=datetime.now)
    source_file: Path | None = None

    # Weather
    air_temp: float = 25.0
    track_temp: float = 30.0

    # Setup used (if available)
    setup_name: str = ""

    # Laps
    laps: list[LapData] = field(default_factory=list)

    # Statistics
    best_lap_time: float = 0.0
    best_lap_number: int = 0
    total_laps: int = 0
    total_distance: float = 0.0

    # Track definition (corners)
    track_corners: list[dict] = field(default_factory=list)

    @property
    def valid_laps(self) -> list[LapData]:
        """Get only valid laps (no outlaps, inlaps, or invalid)."""
        return [
            lap for lap in self.laps
            if lap.is_valid and not lap.is_outlap and not lap.is_inlap
        ]

    @property
    def best_valid_lap(self) -> LapData | None:
        """Get the best valid lap."""
        valid = self.valid_laps
        if not valid:
            return None
        return min(valid, key=lambda x: x.lap_time)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "track_name": self.track_name,
            "car_name": self.car_name,
            "best_lap_time": self.best_lap_time,
            "total_laps": self.total_laps,
            "laps": [lap.to_dict() for lap in self.laps],
        }


@dataclass
class BehaviorStatistics:
    """Statistical analysis of driving behavior."""

    # Overall tendencies (average across all corners)
    understeer_tendency: float = 0.0  # 0-100
    oversteer_tendency: float = 0.0   # 0-100
    balance_score: float = 50.0       # 0=understeer, 50=neutral, 100=oversteer

    # By corner phase
    entry_balance: float = 50.0
    mid_corner_balance: float = 50.0
    exit_balance: float = 50.0

    # By corner type
    slow_corner_balance: float = 50.0
    medium_corner_balance: float = 50.0
    fast_corner_balance: float = 50.0

    # Traction
    traction_on_throttle: float = 0.0   # Wheelspin tendency
    traction_off_throttle: float = 0.0  # Lift-off oversteer tendency

    # Braking
    brake_stability: float = 100.0      # Lower = more lockups
    brake_efficiency: float = 100.0     # How well brakes are used

    # Tire usage
    front_tire_stress: float = 0.0
    rear_tire_stress: float = 0.0
    tire_balance: float = 50.0  # 0=front stressed, 100=rear stressed

    # Confidence metrics
    sample_size: int = 0
    consistency: float = 0.0  # Standard deviation of lap times


@dataclass
class SetupCorrelation:
    """Correlation between setup parameter and performance metric."""

    parameter_name: str
    parameter_value: float

    # Performance impact
    lap_time_correlation: float = 0.0   # -1 to 1
    balance_correlation: float = 0.0    # -1 to 1
    tire_wear_correlation: float = 0.0  # -1 to 1

    # Confidence
    confidence: float = 0.0  # 0-100
    sample_count: int = 0

    # Recommendation
    suggested_direction: str = ""  # "increase", "decrease", "optimal"
    suggested_change: float = 0.0


@dataclass
class AnalysisResult:
    """Complete analysis result combining all analyses."""

    session: SessionData
    behavior: BehaviorStatistics

    # Problem areas
    problem_corners: list[CornerAnalysis] = field(default_factory=list)

    # Setup correlations (if multiple sessions with different setups)
    correlations: list[SetupCorrelation] = field(default_factory=list)

    # Generated recommendations
    recommendations: list[dict] = field(default_factory=list)

    # Scores
    overall_score: float = 0.0
    consistency_score: float = 0.0
    pace_score: float = 0.0
    tire_management_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for frontend."""
        return {
            "session": self.session.to_dict(),
            "behavior": {
                "understeer_tendency": self.behavior.understeer_tendency,
                "oversteer_tendency": self.behavior.oversteer_tendency,
                "balance_score": self.behavior.balance_score,
                "entry_balance": self.behavior.entry_balance,
                "mid_corner_balance": self.behavior.mid_corner_balance,
                "exit_balance": self.behavior.exit_balance,
            },
            "problem_corners": [c.to_dict() for c in self.problem_corners],
            "recommendations": self.recommendations,
            "scores": {
                "overall": self.overall_score,
                "consistency": self.consistency_score,
                "pace": self.pace_score,
                "tire_management": self.tire_management_score,
            },
        }
