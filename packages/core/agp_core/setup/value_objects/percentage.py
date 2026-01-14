"""Percentage value object (diff lock, brake bias)"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class Percentage:
    """Immutable percentage value object."""

    _value: float  # 0-100

    def __post_init__(self) -> None:
        if self._value < 0 or self._value > 100:
            object.__setattr__(self, '_value', max(0, min(100, self._value)))

    @classmethod
    def from_value(cls, value: float) -> Self:
        """Create percentage from 0-100 value."""
        return cls(_value=value)

    @classmethod
    def from_ratio(cls, ratio: float) -> Self:
        """Create percentage from 0-1 ratio."""
        return cls(_value=ratio * 100)

    @property
    def value(self) -> float:
        """Get percentage value (0-100)."""
        return self._value

    @property
    def ratio(self) -> float:
        """Get as ratio (0-1)."""
        return self._value / 100

    def adjust(self, delta: float) -> Percentage:
        """Adjust percentage by delta."""
        return Percentage(_value=self._value + delta)

    def __str__(self) -> str:
        return f"{self._value:.1f}%"

    def __repr__(self) -> str:
        return f"Percentage(value={self._value:.1f})"
