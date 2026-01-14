"""Tire pressure value object"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class Pressure:
    """Immutable tire pressure value object."""

    _kpa: float

    # Constants
    KPA_TO_PSI: float = 0.145038
    PSI_TO_KPA: float = 6.89476

    MIN_KPA: float = 100.0
    MAX_KPA: float = 250.0

    def __post_init__(self) -> None:
        if not self.MIN_KPA <= self._kpa <= self.MAX_KPA:
            object.__setattr__(self, '_kpa', max(self.MIN_KPA, min(self.MAX_KPA, self._kpa)))

    @classmethod
    def from_kpa(cls, value: float) -> Self:
        """Create pressure from kPa value."""
        return cls(_kpa=value)

    @classmethod
    def from_psi(cls, value: float) -> Self:
        """Create pressure from PSI value."""
        return cls(_kpa=value * cls.PSI_TO_KPA)

    @classmethod
    def from_bar(cls, value: float) -> Self:
        """Create pressure from bar value."""
        return cls(_kpa=value * 100.0)

    @property
    def kpa(self) -> float:
        """Get pressure in kPa."""
        return self._kpa

    @property
    def psi(self) -> float:
        """Get pressure in PSI."""
        return self._kpa * self.KPA_TO_PSI

    @property
    def bar(self) -> float:
        """Get pressure in bar."""
        return self._kpa / 100.0

    def increase(self, delta_kpa: float) -> Pressure:
        """Increase pressure by delta kPa."""
        return Pressure(_kpa=self._kpa + delta_kpa)

    def increase_percent(self, percent: float) -> Pressure:
        """Increase pressure by percentage."""
        return Pressure(_kpa=self._kpa * (1 + percent / 100))

    def __str__(self) -> str:
        return f"{self.psi:.1f} PSI ({self.kpa:.0f} kPa)"

    def __repr__(self) -> str:
        return f"Pressure(kpa={self._kpa:.1f})"
