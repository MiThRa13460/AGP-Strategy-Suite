"""Diagnostic entity for setup analysis results"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class Severity(Enum):
    """Diagnostic severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


class DiagnosticCategory(Enum):
    """Categories of diagnostics."""
    BALANCE = "balance"
    TRACTION = "traction"
    BRAKING = "braking"
    TIRE = "tire"
    SUSPENSION = "suspension"
    AERO = "aero"
    DIFFERENTIAL = "differential"


class CornerPhase(Enum):
    """Phase of the corner where the problem occurs."""
    BRAKING = "braking"
    ENTRY = "entry"
    MID = "mid"
    EXIT = "exit"
    ACCELERATION = "acceleration"
    STRAIGHT = "straight"


class ProblemType(Enum):
    """Types of handling problems."""
    # Understeer
    UNDERSTEER_ENTRY = "understeer_entry"
    UNDERSTEER_MID = "understeer_mid"
    UNDERSTEER_EXIT = "understeer_exit"

    # Oversteer
    OVERSTEER_ENTRY = "oversteer_entry"
    OVERSTEER_MID = "oversteer_mid"
    OVERSTEER_EXIT = "oversteer_exit"

    # Traction
    WHEELSPIN = "wheelspin"
    POWER_OVERSTEER = "power_oversteer"

    # Braking
    FRONT_LOCKUP = "front_lockup"
    REAR_LOCKUP = "rear_lockup"
    INSTABILITY_BRAKING = "instability_braking"

    # Other
    BOTTOMING = "bottoming"
    BOUNCING = "bouncing"
    LACK_OF_GRIP = "lack_of_grip"
    TIRE_OVERHEATING = "tire_overheating"
    TIRE_GRAINING = "tire_graining"


@dataclass
class ParameterRecommendation:
    """A specific parameter change recommendation."""

    parameter: str
    current_value: Any
    recommended_value: Any
    change_direction: str  # "increase", "decrease", "adjust"
    change_amount: str  # e.g., "2-3 clicks", "+5%", "-0.2"
    confidence: float  # 0-1
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter": self.parameter,
            "current": self.current_value,
            "recommended": self.recommended_value,
            "direction": self.change_direction,
            "amount": self.change_amount,
            "confidence": self.confidence,
            "explanation": self.explanation,
        }


@dataclass
class Diagnostic:
    """
    A diagnostic result from setup analysis.

    Contains the problem identified, severity, and recommendations.
    """

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""

    severity: Severity = Severity.INFO
    category: DiagnosticCategory = DiagnosticCategory.BALANCE
    problem_type: ProblemType | None = None
    corner_phase: CornerPhase | None = None

    # Recommendations
    recommendations: list[ParameterRecommendation] = field(default_factory=list)

    # Confidence and priority
    confidence: float = 0.8
    priority: int = 1  # 1 = highest

    # Related data
    affected_parameters: list[str] = field(default_factory=list)
    telemetry_evidence: dict[str, Any] = field(default_factory=dict)

    def add_recommendation(
        self,
        parameter: str,
        current: Any,
        recommended: Any,
        direction: str,
        amount: str,
        confidence: float = 0.8,
        explanation: str = "",
    ) -> None:
        """Add a parameter recommendation."""
        self.recommendations.append(
            ParameterRecommendation(
                parameter=parameter,
                current_value=current,
                recommended_value=recommended,
                change_direction=direction,
                change_amount=amount,
                confidence=confidence,
                explanation=explanation,
            )
        )
        if parameter not in self.affected_parameters:
            self.affected_parameters.append(parameter)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category.value,
            "problem_type": self.problem_type.value if self.problem_type else None,
            "corner_phase": self.corner_phase.value if self.corner_phase else None,
            "confidence": self.confidence,
            "priority": self.priority,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "affected_parameters": self.affected_parameters,
        }
