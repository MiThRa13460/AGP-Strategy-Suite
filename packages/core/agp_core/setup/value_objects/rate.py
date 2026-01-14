"""Rate value object (spring rate, damper rate)"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class Rate:
    """Immutable rate value object for spring/damper rates."""

    _nm: float  # N/m for springs, N*s/m for dampers

    @classmethod
    def from_nm(cls, value: float) -> Self:
        """Create rate from N/m."""
        return cls(_nm=value)

    @classmethod
    def from_lbs_in(cls, value: float) -> Self:
        """Create rate from lbs/in."""
        return cls(_nm=value * 175.127)

    @classmethod
    def from_kgf_mm(cls, value: float) -> Self:
        """Create rate from kgf/mm."""
        return cls(_nm=value * 9806.65)

    @property
    def nm(self) -> float:
        """Get rate in N/m."""
        return self._nm

    @property
    def lbs_in(self) -> float:
        """Get rate in lbs/in."""
        return self._nm / 175.127

    @property
    def kgf_mm(self) -> float:
        """Get rate in kgf/mm."""
        return self._nm / 9806.65

    def adjust_percent(self, percent: float) -> Rate:
        """Adjust rate by percentage."""
        return Rate(_nm=self._nm * (1 + percent / 100))

    def __str__(self) -> str:
        return f"{self.lbs_in:.0f} lbs/in"

    def __repr__(self) -> str:
        return f"Rate(nm={self._nm:.0f})"
