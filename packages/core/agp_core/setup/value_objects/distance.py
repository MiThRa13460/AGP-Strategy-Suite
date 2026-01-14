"""Distance value object (ride height, track width)"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class Distance:
    """Immutable distance value object for ride height, track width."""

    _mm: float

    @classmethod
    def from_mm(cls, value: float) -> Self:
        """Create distance from millimeters."""
        return cls(_mm=value)

    @classmethod
    def from_m(cls, value: float) -> Self:
        """Create distance from meters."""
        return cls(_mm=value * 1000)

    @classmethod
    def from_inches(cls, value: float) -> Self:
        """Create distance from inches."""
        return cls(_mm=value * 25.4)

    @property
    def mm(self) -> float:
        """Get distance in millimeters."""
        return self._mm

    @property
    def m(self) -> float:
        """Get distance in meters."""
        return self._mm / 1000

    @property
    def inches(self) -> float:
        """Get distance in inches."""
        return self._mm / 25.4

    def adjust(self, delta_mm: float) -> Distance:
        """Adjust distance by delta mm."""
        return Distance(_mm=self._mm + delta_mm)

    def __str__(self) -> str:
        return f"{self._mm:.1f}mm"

    def __repr__(self) -> str:
        return f"Distance(mm={self._mm:.1f})"
