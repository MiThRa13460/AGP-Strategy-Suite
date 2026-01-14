"""Temperature value object"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class Temperature:
    """Immutable temperature value object."""

    _celsius: float

    @classmethod
    def from_celsius(cls, value: float) -> Self:
        """Create temperature from Celsius."""
        return cls(_celsius=value)

    @classmethod
    def from_fahrenheit(cls, value: float) -> Self:
        """Create temperature from Fahrenheit."""
        return cls(_celsius=(value - 32) * 5 / 9)

    @classmethod
    def from_kelvin(cls, value: float) -> Self:
        """Create temperature from Kelvin."""
        return cls(_celsius=value - 273.15)

    @property
    def celsius(self) -> float:
        """Get temperature in Celsius."""
        return self._celsius

    @property
    def fahrenheit(self) -> float:
        """Get temperature in Fahrenheit."""
        return self._celsius * 9 / 5 + 32

    @property
    def kelvin(self) -> float:
        """Get temperature in Kelvin."""
        return self._celsius + 273.15

    def is_optimal_tire(self, min_c: float = 85.0, max_c: float = 105.0) -> bool:
        """Check if temperature is in optimal tire range."""
        return min_c <= self._celsius <= max_c

    def __str__(self) -> str:
        return f"{self._celsius:.1f}C"

    def __repr__(self) -> str:
        return f"Temperature(celsius={self._celsius:.1f})"
