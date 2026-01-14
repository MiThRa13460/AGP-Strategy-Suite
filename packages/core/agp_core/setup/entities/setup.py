"""Setup entity - Aggregate root for car setup"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from agp_core.setup.value_objects import (
    Angle,
    Distance,
    Percentage,
    Pressure,
    Rate,
)


class CornerPosition(Enum):
    """Wheel corner positions."""
    FRONT_LEFT = "FL"
    FRONT_RIGHT = "FR"
    REAR_LEFT = "RL"
    REAR_RIGHT = "RR"


@dataclass
class CornerSetup:
    """Setup parameters for a single corner."""

    position: CornerPosition
    camber: Angle
    pressure: Pressure
    spring_rate: Rate
    ride_height: Distance
    slow_bump: int
    fast_bump: int
    slow_rebound: int
    fast_rebound: int
    toe: Angle | None = None
    packer: Distance | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "position": self.position.value,
            "camber_deg": self.camber.degrees,
            "pressure_kpa": self.pressure.kpa,
            "spring_rate_nm": self.spring_rate.nm,
            "ride_height_mm": self.ride_height.mm,
            "slow_bump": self.slow_bump,
            "fast_bump": self.fast_bump,
            "slow_rebound": self.slow_rebound,
            "fast_rebound": self.fast_rebound,
        }


@dataclass
class SuspensionSetup:
    """Full suspension configuration."""

    front_left: CornerSetup
    front_right: CornerSetup
    rear_left: CornerSetup
    rear_right: CornerSetup
    front_arb: int
    rear_arb: int
    front_toe: Angle
    rear_toe: Angle

    @property
    def front_ride_height(self) -> Distance:
        """Average front ride height."""
        return Distance.from_mm(
            (self.front_left.ride_height.mm + self.front_right.ride_height.mm) / 2
        )

    @property
    def rear_ride_height(self) -> Distance:
        """Average rear ride height."""
        return Distance.from_mm(
            (self.rear_left.ride_height.mm + self.rear_right.ride_height.mm) / 2
        )

    @property
    def rake(self) -> Distance:
        """Rake (rear - front ride height)."""
        return Distance.from_mm(
            self.rear_ride_height.mm - self.front_ride_height.mm
        )

    @property
    def front_camber_avg(self) -> Angle:
        """Average front camber."""
        return Angle.from_degrees(
            (self.front_left.camber.degrees + self.front_right.camber.degrees) / 2
        )

    @property
    def rear_camber_avg(self) -> Angle:
        """Average rear camber."""
        return Angle.from_degrees(
            (self.rear_left.camber.degrees + self.rear_right.camber.degrees) / 2
        )

    def get_corner(self, position: CornerPosition) -> CornerSetup:
        """Get corner setup by position."""
        mapping = {
            CornerPosition.FRONT_LEFT: self.front_left,
            CornerPosition.FRONT_RIGHT: self.front_right,
            CornerPosition.REAR_LEFT: self.rear_left,
            CornerPosition.REAR_RIGHT: self.rear_right,
        }
        return mapping[position]


@dataclass
class DifferentialSetup:
    """Differential configuration."""

    power_lock: Percentage
    coast_lock: Percentage
    preload: float  # Nm


@dataclass
class AeroSetup:
    """Aerodynamic configuration."""

    front_wing: int
    rear_wing: int

    @property
    def estimated_balance(self) -> float:
        """Estimate aero balance (% front)."""
        total = self.front_wing + self.rear_wing
        if total == 0:
            return 0.5
        return self.front_wing / total


@dataclass
class BrakeSetup:
    """Brake configuration."""

    bias: Percentage  # Front percentage
    pressure: Percentage


@dataclass
class Setup:
    """
    Setup aggregate root.

    This is the main entity representing a complete car setup.
    """

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    source_path: Path | None = None

    # Metadata
    car_id: str = ""
    track_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    notes: str = ""

    # Setup sections
    suspension: SuspensionSetup | None = None
    differential: DifferentialSetup | None = None
    aero: AeroSetup | None = None
    brakes: BrakeSetup | None = None

    # Additional settings
    tire_compound: str = "Medium"
    fuel_load: float = 0.0
    traction_control: int = 0

    # Version tracking
    version: int = 1
    parent_id: UUID | None = None

    @property
    def is_symmetric(self) -> bool:
        """Check if setup is symmetric (left = right)."""
        if not self.suspension:
            return True

        fl = self.suspension.front_left
        fr = self.suspension.front_right
        rl = self.suspension.rear_left
        rr = self.suspension.rear_right

        return (
            abs(fl.camber.degrees - fr.camber.degrees) < 0.01
            and abs(fl.pressure.kpa - fr.pressure.kpa) < 0.1
            and abs(rl.camber.degrees - rr.camber.degrees) < 0.01
            and abs(rl.pressure.kpa - rr.pressure.kpa) < 0.1
        )

    def clone(self, new_name: str | None = None) -> Setup:
        """Create a copy of this setup."""
        import copy

        cloned = copy.deepcopy(self)
        cloned.id = uuid4()
        cloned.parent_id = self.id
        cloned.version = self.version + 1
        cloned.created_at = datetime.now()
        cloned.modified_at = datetime.now()

        if new_name:
            cloned.name = new_name
        else:
            cloned.name = f"{self.name}_v{cloned.version}"

        return cloned

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {
            "id": str(self.id),
            "name": self.name,
            "car_id": self.car_id,
            "track_id": self.track_id,
            "created_at": self.created_at.isoformat(),
            "tire_compound": self.tire_compound,
            "fuel_load": self.fuel_load,
        }

        if self.suspension:
            result["suspension"] = {
                "front_ride_height_mm": self.suspension.front_ride_height.mm,
                "rear_ride_height_mm": self.suspension.rear_ride_height.mm,
                "rake_mm": self.suspension.rake.mm,
                "front_arb": self.suspension.front_arb,
                "rear_arb": self.suspension.rear_arb,
                "front_camber_deg": self.suspension.front_camber_avg.degrees,
                "rear_camber_deg": self.suspension.rear_camber_avg.degrees,
            }

        if self.differential:
            result["differential"] = {
                "power_lock": self.differential.power_lock.value,
                "coast_lock": self.differential.coast_lock.value,
                "preload": self.differential.preload,
            }

        if self.brakes:
            result["brakes"] = {
                "bias_front": self.brakes.bias.value,
                "pressure": self.brakes.pressure.value,
            }

        if self.aero:
            result["aero"] = {
                "front_wing": self.aero.front_wing,
                "rear_wing": self.aero.rear_wing,
            }

        return result
