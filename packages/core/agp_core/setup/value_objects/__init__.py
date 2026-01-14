"""Immutable value objects for domain modeling"""

from agp_core.setup.value_objects.pressure import Pressure
from agp_core.setup.value_objects.temperature import Temperature
from agp_core.setup.value_objects.angle import Angle
from agp_core.setup.value_objects.distance import Distance
from agp_core.setup.value_objects.rate import Rate
from agp_core.setup.value_objects.percentage import Percentage

__all__ = [
    "Pressure",
    "Temperature",
    "Angle",
    "Distance",
    "Rate",
    "Percentage",
]
