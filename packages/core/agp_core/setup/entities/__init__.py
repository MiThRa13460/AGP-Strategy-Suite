"""Domain entities for setup engineering"""

from agp_core.setup.entities.setup import (
    Setup,
    SuspensionSetup,
    CornerSetup,
    CornerPosition,
    DifferentialSetup,
    AeroSetup,
    BrakeSetup,
)
from agp_core.setup.entities.diagnostic import (
    Diagnostic,
    Severity,
    DiagnosticCategory,
    ProblemType,
    CornerPhase,
    ParameterRecommendation,
)

__all__ = [
    "Setup",
    "SuspensionSetup",
    "CornerSetup",
    "CornerPosition",
    "DifferentialSetup",
    "AeroSetup",
    "BrakeSetup",
    "Diagnostic",
    "Severity",
    "DiagnosticCategory",
    "ProblemType",
    "CornerPhase",
    "ParameterRecommendation",
]
