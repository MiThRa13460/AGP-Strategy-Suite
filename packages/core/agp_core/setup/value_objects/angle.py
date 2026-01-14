"""Angle value object (camber, toe, caster)"""

from __future__ import annotations
from dataclasses import dataclass
from math import radians, degrees as to_degrees
from typing import Self


@dataclass(frozen=True, slots=True)
class Angle:
    """Immutable angle value object for camber, toe, caster."""

    _degrees: float

    @classmethod
    def from_degrees(cls, value: float) -> Self:
        """Create angle from degrees."""
        return cls(_degrees=value)

    @classmethod
    def from_radians(cls, value: float) -> Self:
        """Create angle from radians."""
        return cls(_degrees=to_degrees(value))

    @property
    def degrees(self) -> float:
        """Get angle in degrees."""
        return self._degrees

    @property
    def radians(self) -> float:
        """Get angle in radians."""
        return radians(self._degrees)

    def adjust(self, delta_deg: float) -> Angle:
        """Adjust angle by delta degrees."""
        return Angle(_degrees=self._degrees + delta_deg)

    def is_negative(self) -> bool:
        """Check if angle is negative (typical for camber)."""
        return self._degrees < 0

    def __str__(self) -> str:
        return f"{self._degrees:.2f}"

    def __repr__(self) -> str:
        return f"Angle(degrees={self._degrees:.2f})"
