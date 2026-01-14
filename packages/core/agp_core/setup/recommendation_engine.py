"""
Recommendation Engine - Generate data-driven setup recommendations.

Combines telemetry analysis, setup correlations, and expert rules to
generate actionable setup recommendations with confidence levels.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import logging

from agp_core.setup.entities.setup import Setup
from agp_core.setup.entities.diagnostic import (
    Diagnostic,
    Severity,
    DiagnosticCategory,
    ProblemType,
    CornerPhase,
    ParameterRecommendation,
)
from agp_core.setup.telemetry_models import (
    SessionData,
    BehaviorStatistics,
    CornerAnalysis,
    CornerType,
    AnalysisResult,
)
from agp_core.setup.telemetry_analyzer import TelemetryAnalyzer
from agp_core.setup.setup_correlator import SetupCorrelator

logger = logging.getLogger(__name__)


class RecommendationPriority(Enum):
    """Priority level for recommendations."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    OPTIONAL = 5


@dataclass
class SetupRecommendation:
    """A single setup recommendation."""

    title: str
    description: str
    priority: RecommendationPriority
    category: DiagnosticCategory

    # What to change
    parameter_changes: list[ParameterRecommendation] = field(default_factory=list)

    # Why (evidence)
    evidence: list[str] = field(default_factory=list)
    affected_corners: list[str] = field(default_factory=list)

    # Impact prediction
    expected_improvement: str = ""
    confidence: float = 0.0  # 0-100

    # Data backing
    data_driven: bool = False
    correlation_strength: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for frontend."""
        return {
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "category": self.category.value,
            "parameter_changes": [
                {
                    "parameter": p.parameter_name,
                    "direction": p.direction,
                    "amount": p.suggested_change,
                    "current": p.current_value,
                    "target": p.target_value,
                }
                for p in self.parameter_changes
            ],
            "evidence": self.evidence,
            "affected_corners": self.affected_corners,
            "expected_improvement": self.expected_improvement,
            "confidence": self.confidence,
            "data_driven": self.data_driven,
        }


class RecommendationEngine:
    """
    Generates intelligent setup recommendations from telemetry analysis.

    Combines:
    1. Telemetry-based behavior detection
    2. Setup correlation analysis (if multiple sessions)
    3. Expert rule-based recommendations
    4. Corner-specific analysis
    """

    # Thresholds for recommendations
    UNDERSTEER_THRESHOLD = 30.0
    OVERSTEER_THRESHOLD = 30.0
    TRACTION_LOSS_THRESHOLD = 20.0
    TIRE_TEMP_IMBALANCE_THRESHOLD = 8.0  # degrees
    CONFIDENCE_THRESHOLD = 40.0

    def __init__(self):
        self.analyzer = TelemetryAnalyzer()
        self.correlator = SetupCorrelator()

    def analyze_and_recommend(
        self,
        session: SessionData,
        setup: Setup | None = None,
    ) -> AnalysisResult:
        """
        Analyze session and generate recommendations.

        Args:
            session: Telemetry session data
            setup: Current setup (optional, for context)

        Returns:
            AnalysisResult with recommendations
        """
        logger.info(f"Analyzing session {session.session_id}")

        # Run telemetry analysis
        behavior = self.analyzer.analyze_session(session)

        # Get problem corners
        problem_corners = self._identify_problem_corners(session)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            session, behavior, setup, problem_corners
        )

        # Calculate scores
        scores = self._calculate_scores(session, behavior)

        result = AnalysisResult(
            session=session,
            behavior=behavior,
            problem_corners=problem_corners,
            recommendations=[r.to_dict() for r in recommendations],
            overall_score=scores["overall"],
            consistency_score=scores["consistency"],
            pace_score=scores["pace"],
            tire_management_score=scores["tire_management"],
        )

        return result

    def add_session_for_correlation(
        self,
        session: SessionData,
        setup: Setup
    ) -> None:
        """Add a session for multi-session correlation analysis."""
        self.correlator.add_session(session, setup)

    def get_correlation_recommendations(self) -> list[SetupRecommendation]:
        """Get recommendations based on multi-session correlations."""
        if len(self.correlator.sessions) < 2:
            return []

        correlations = self.correlator.analyze_correlations()
        recommendations: list[SetupRecommendation] = []

        for corr in correlations:
            if corr.confidence < self.CONFIDENCE_THRESHOLD:
                continue

            # Create recommendation from correlation
            rec = self._correlation_to_recommendation(corr)
            if rec:
                recommendations.append(rec)

        return recommendations

    def _identify_problem_corners(self, session: SessionData) -> list[CornerAnalysis]:
        """Identify corners with consistent issues."""
        if not session.valid_laps:
            return []

        # Aggregate corner data across laps
        corner_issues: dict[int, dict] = {}

        for lap in session.valid_laps:
            for corner in lap.corners:
                if corner.corner_id not in corner_issues:
                    corner_issues[corner.corner_id] = {
                        "corner": corner,
                        "understeer_count": 0,
                        "oversteer_count": 0,
                        "traction_count": 0,
                        "total_time_loss": 0.0,
                        "lap_count": 0,
                    }

                issues = corner_issues[corner.corner_id]
                issues["lap_count"] += 1

                if corner.understeer_detected:
                    issues["understeer_count"] += 1
                if corner.oversteer_detected:
                    issues["oversteer_count"] += 1
                if corner.traction_loss_detected:
                    issues["traction_count"] += 1
                issues["total_time_loss"] += corner.time_loss

        # Filter to corners with consistent issues (>50% of laps)
        problem_corners: list[CornerAnalysis] = []

        for corner_id, issues in corner_issues.items():
            if issues["lap_count"] < 2:
                continue

            issue_rate = max(
                issues["understeer_count"],
                issues["oversteer_count"],
                issues["traction_count"]
            ) / issues["lap_count"]

            if issue_rate > 0.5:
                problem_corners.append(issues["corner"])

        # Sort by time loss
        problem_corners.sort(key=lambda c: c.time_loss, reverse=True)

        return problem_corners[:5]  # Top 5 problem corners

    def _generate_recommendations(
        self,
        session: SessionData,
        behavior: BehaviorStatistics,
        setup: Setup | None,
        problem_corners: list[CornerAnalysis],
    ) -> list[SetupRecommendation]:
        """Generate all recommendations from analysis."""
        recommendations: list[SetupRecommendation] = []

        # 1. Overall balance recommendations
        balance_recs = self._generate_balance_recommendations(behavior, setup)
        recommendations.extend(balance_recs)

        # 2. Corner-phase specific recommendations
        phase_recs = self._generate_phase_recommendations(behavior, setup)
        recommendations.extend(phase_recs)

        # 3. Corner-type specific recommendations
        type_recs = self._generate_corner_type_recommendations(behavior, setup)
        recommendations.extend(type_recs)

        # 4. Traction recommendations
        traction_recs = self._generate_traction_recommendations(behavior, setup)
        recommendations.extend(traction_recs)

        # 5. Corner-specific recommendations
        corner_recs = self._generate_corner_specific_recommendations(
            problem_corners, setup
        )
        recommendations.extend(corner_recs)

        # 6. Tire management recommendations
        tire_recs = self._generate_tire_recommendations(session, behavior, setup)
        recommendations.extend(tire_recs)

        # 7. Correlation-based recommendations (if available)
        corr_recs = self.get_correlation_recommendations()
        recommendations.extend(corr_recs)

        # Sort by priority
        recommendations.sort(key=lambda r: r.priority.value)

        return recommendations

    def _generate_balance_recommendations(
        self,
        behavior: BehaviorStatistics,
        setup: Setup | None
    ) -> list[SetupRecommendation]:
        """Generate recommendations for overall balance."""
        recs: list[SetupRecommendation] = []

        # Understeer dominant
        if behavior.understeer_tendency > self.UNDERSTEER_THRESHOLD:
            changes = []

            if setup and setup.suspension:
                # Soften front
                changes.append(ParameterRecommendation(
                    parameter_name="Front ARB",
                    direction="decrease",
                    suggested_change=1,
                    reason="Reduce front roll stiffness",
                ))
                # More front camber
                changes.append(ParameterRecommendation(
                    parameter_name="Front Camber",
                    direction="increase",
                    suggested_change=0.2,
                    reason="Increase front grip in corners",
                ))

            if setup and setup.aero:
                changes.append(ParameterRecommendation(
                    parameter_name="Front Wing",
                    direction="increase",
                    suggested_change=1,
                    reason="Increase front downforce",
                ))

            recs.append(SetupRecommendation(
                title="Reduire le sous-virage",
                description=f"Tendance au sous-virage detectee ({behavior.understeer_tendency:.0f}%). "
                           "Le train avant manque d'adherence en virage.",
                priority=RecommendationPriority.HIGH if behavior.understeer_tendency > 50 else RecommendationPriority.MEDIUM,
                category=DiagnosticCategory.BALANCE,
                parameter_changes=changes,
                evidence=[
                    f"Sous-virage: {behavior.understeer_tendency:.0f}%",
                    f"Balance globale: {behavior.balance_score:.0f}/100",
                ],
                expected_improvement="Meilleure rotation en entree de virage",
                confidence=min(90, 50 + behavior.understeer_tendency),
                data_driven=True,
            ))

        # Oversteer dominant
        if behavior.oversteer_tendency > self.OVERSTEER_THRESHOLD:
            changes = []

            if setup and setup.suspension:
                # Stiffen front or soften rear
                changes.append(ParameterRecommendation(
                    parameter_name="Rear ARB",
                    direction="decrease",
                    suggested_change=1,
                    reason="Reduce rear roll stiffness",
                ))
                # Less rear camber
                changes.append(ParameterRecommendation(
                    parameter_name="Rear Camber",
                    direction="decrease",
                    suggested_change=0.2,
                    reason="Increase rear contact patch",
                ))

            if setup and setup.aero:
                changes.append(ParameterRecommendation(
                    parameter_name="Rear Wing",
                    direction="increase",
                    suggested_change=1,
                    reason="Increase rear downforce",
                ))

            recs.append(SetupRecommendation(
                title="Reduire le survirage",
                description=f"Tendance au survirage detectee ({behavior.oversteer_tendency:.0f}%). "
                           "Le train arriere decroche en virage.",
                priority=RecommendationPriority.HIGH if behavior.oversteer_tendency > 50 else RecommendationPriority.MEDIUM,
                category=DiagnosticCategory.BALANCE,
                parameter_changes=changes,
                evidence=[
                    f"Survirage: {behavior.oversteer_tendency:.0f}%",
                    f"Balance globale: {behavior.balance_score:.0f}/100",
                ],
                expected_improvement="Plus de stabilite en virage",
                confidence=min(90, 50 + behavior.oversteer_tendency),
                data_driven=True,
            ))

        return recs

    def _generate_phase_recommendations(
        self,
        behavior: BehaviorStatistics,
        setup: Setup | None
    ) -> list[SetupRecommendation]:
        """Generate recommendations for specific corner phases."""
        recs: list[SetupRecommendation] = []

        # Entry phase issues
        if behavior.entry_balance < 35:  # Understeer on entry
            changes = []
            if setup and setup.brakes:
                changes.append(ParameterRecommendation(
                    parameter_name="Brake Bias",
                    direction="decrease",
                    suggested_change=1.0,
                    reason="Less front brake pressure",
                ))

            recs.append(SetupRecommendation(
                title="Sous-virage en entree de virage",
                description="La voiture pousse en entree de virage lors du freinage appuye.",
                priority=RecommendationPriority.MEDIUM,
                category=DiagnosticCategory.BALANCE,
                parameter_changes=changes,
                evidence=[f"Balance entree: {behavior.entry_balance:.0f}/100"],
                expected_improvement="Meilleure rotation au freinage",
                confidence=70,
                data_driven=True,
            ))

        elif behavior.entry_balance > 65:  # Oversteer on entry
            changes = []
            if setup and setup.brakes:
                changes.append(ParameterRecommendation(
                    parameter_name="Brake Bias",
                    direction="increase",
                    suggested_change=1.0,
                    reason="More front brake pressure",
                ))

            recs.append(SetupRecommendation(
                title="Survirage en entree de virage",
                description="L'arriere decroche en entree de virage lors du freinage.",
                priority=RecommendationPriority.MEDIUM,
                category=DiagnosticCategory.BALANCE,
                parameter_changes=changes,
                evidence=[f"Balance entree: {behavior.entry_balance:.0f}/100"],
                expected_improvement="Plus de stabilite au freinage",
                confidence=70,
                data_driven=True,
            ))

        # Exit phase issues
        if behavior.exit_balance < 35:  # Understeer on exit
            changes = []
            if setup and setup.differential:
                changes.append(ParameterRecommendation(
                    parameter_name="Diff Power Lock",
                    direction="decrease",
                    suggested_change=5.0,
                    reason="Allow more differential slip",
                ))

            recs.append(SetupRecommendation(
                title="Sous-virage en sortie de virage",
                description="La voiture pousse a l'acceleration en sortie de virage.",
                priority=RecommendationPriority.MEDIUM,
                category=DiagnosticCategory.BALANCE,
                parameter_changes=changes,
                evidence=[f"Balance sortie: {behavior.exit_balance:.0f}/100"],
                expected_improvement="Meilleure motricite en sortie",
                confidence=70,
                data_driven=True,
            ))

        return recs

    def _generate_corner_type_recommendations(
        self,
        behavior: BehaviorStatistics,
        setup: Setup | None
    ) -> list[SetupRecommendation]:
        """Generate recommendations based on corner speed types."""
        recs: list[SetupRecommendation] = []

        # Slow corners
        if behavior.slow_corner_balance < 35:
            changes = []
            if setup and setup.suspension:
                changes.append(ParameterRecommendation(
                    parameter_name="Front Slow Rebound",
                    direction="decrease",
                    suggested_change=2,
                    reason="Faster weight transfer",
                ))

            recs.append(SetupRecommendation(
                title="Sous-virage en virage lent",
                description="Manque de rotation dans les virages lents (< 80 km/h).",
                priority=RecommendationPriority.LOW,
                category=DiagnosticCategory.BALANCE,
                parameter_changes=changes,
                evidence=[f"Balance virages lents: {behavior.slow_corner_balance:.0f}/100"],
                expected_improvement="Meilleure agilite en epingle",
                confidence=60,
                data_driven=True,
            ))

        # Fast corners
        if behavior.fast_corner_balance > 65:
            changes = []
            if setup and setup.aero:
                changes.append(ParameterRecommendation(
                    parameter_name="Rear Wing",
                    direction="increase",
                    suggested_change=1,
                    reason="More rear downforce at speed",
                ))
            if setup and setup.suspension:
                changes.append(ParameterRecommendation(
                    parameter_name="Rake",
                    direction="decrease",
                    suggested_change=1.0,
                    reason="More rear stability at speed",
                ))

            recs.append(SetupRecommendation(
                title="Instabilite en virage rapide",
                description="L'arriere est nerveux dans les virages rapides (> 150 km/h).",
                priority=RecommendationPriority.HIGH,
                category=DiagnosticCategory.STABILITY,
                parameter_changes=changes,
                evidence=[f"Balance virages rapides: {behavior.fast_corner_balance:.0f}/100"],
                expected_improvement="Plus de confiance a haute vitesse",
                confidence=75,
                data_driven=True,
            ))

        return recs

    def _generate_traction_recommendations(
        self,
        behavior: BehaviorStatistics,
        setup: Setup | None
    ) -> list[SetupRecommendation]:
        """Generate recommendations for traction issues."""
        recs: list[SetupRecommendation] = []

        if behavior.traction_on_throttle > self.TRACTION_LOSS_THRESHOLD:
            changes = []

            if setup and setup.differential:
                changes.append(ParameterRecommendation(
                    parameter_name="Diff Power Lock",
                    direction="decrease",
                    suggested_change=5.0,
                    reason="Allow wheels to spin more independently",
                ))

            if setup and setup.suspension:
                changes.append(ParameterRecommendation(
                    parameter_name="Rear Springs",
                    direction="decrease",
                    suggested_change=5000,
                    reason="More rear grip on bumps",
                ))

            recs.append(SetupRecommendation(
                title="Perte de traction a l'acceleration",
                description=f"Patinage detecte ({behavior.traction_on_throttle:.0f}%) "
                           "lors de l'acceleration en sortie de virage.",
                priority=RecommendationPriority.HIGH,
                category=DiagnosticCategory.TRACTION,
                parameter_changes=changes,
                evidence=[
                    f"Traction loss: {behavior.traction_on_throttle:.0f}%",
                ],
                expected_improvement="Meilleure motricite, temps au tour reduit",
                confidence=min(85, 50 + behavior.traction_on_throttle),
                data_driven=True,
            ))

        return recs

    def _generate_corner_specific_recommendations(
        self,
        problem_corners: list[CornerAnalysis],
        setup: Setup | None
    ) -> list[SetupRecommendation]:
        """Generate recommendations for specific problem corners."""
        recs: list[SetupRecommendation] = []

        for corner in problem_corners[:3]:  # Top 3 problem corners
            issue_type = ""
            changes = []

            if corner.understeer_severity > corner.oversteer_severity:
                issue_type = "sous-virage"
                if setup and setup.suspension:
                    if corner.corner_type == CornerType.SLOW:
                        changes.append(ParameterRecommendation(
                            parameter_name="Front ARB",
                            direction="decrease",
                            suggested_change=1,
                        ))
                    else:
                        changes.append(ParameterRecommendation(
                            parameter_name="Front Wing",
                            direction="increase",
                            suggested_change=1,
                        ))
            else:
                issue_type = "survirage"
                if setup and setup.suspension:
                    changes.append(ParameterRecommendation(
                        parameter_name="Rear ARB",
                        direction="decrease",
                        suggested_change=1,
                    ))

            recs.append(SetupRecommendation(
                title=f"Probleme au {corner.corner_name}",
                description=f"{issue_type.capitalize()} recurrent dans ce virage "
                           f"({corner.corner_type.value}, {corner.direction.value}).",
                priority=RecommendationPriority.MEDIUM,
                category=DiagnosticCategory.BALANCE,
                parameter_changes=changes,
                affected_corners=[corner.corner_name],
                evidence=[
                    f"Sous-virage: {corner.understeer_severity:.0f}%",
                    f"Survirage: {corner.oversteer_severity:.0f}%",
                    f"Perte temps: {corner.time_loss:.2f}s",
                ],
                expected_improvement=f"~{corner.time_loss:.2f}s par tour",
                confidence=70,
                data_driven=True,
            ))

        return recs

    def _generate_tire_recommendations(
        self,
        session: SessionData,
        behavior: BehaviorStatistics,
        setup: Setup | None
    ) -> list[SetupRecommendation]:
        """Generate recommendations for tire management."""
        recs: list[SetupRecommendation] = []

        # Check tire balance
        temp_diff = abs(behavior.front_tire_stress - behavior.rear_tire_stress)

        if temp_diff > 20:
            if behavior.front_tire_stress > behavior.rear_tire_stress:
                changes = []
                if setup and setup.suspension:
                    changes.append(ParameterRecommendation(
                        parameter_name="Front Camber",
                        direction="decrease",
                        suggested_change=0.1,
                        reason="Reduce front tire stress",
                    ))
                    changes.append(ParameterRecommendation(
                        parameter_name="Front Pressure",
                        direction="increase",
                        suggested_change=1.0,
                        reason="Reduce front tire deformation",
                    ))

                recs.append(SetupRecommendation(
                    title="Usure excessive pneus avant",
                    description="Les pneus avant surchauffent par rapport aux arrieres.",
                    priority=RecommendationPriority.MEDIUM,
                    category=DiagnosticCategory.TIRE_WEAR,
                    parameter_changes=changes,
                    evidence=[
                        f"Stress avant: {behavior.front_tire_stress:.0f}%",
                        f"Stress arriere: {behavior.rear_tire_stress:.0f}%",
                    ],
                    expected_improvement="Meilleur equilibre d'usure",
                    confidence=65,
                    data_driven=True,
                ))
            else:
                changes = []
                if setup and setup.suspension:
                    changes.append(ParameterRecommendation(
                        parameter_name="Rear Camber",
                        direction="decrease",
                        suggested_change=0.1,
                        reason="Reduce rear tire stress",
                    ))

                recs.append(SetupRecommendation(
                    title="Usure excessive pneus arriere",
                    description="Les pneus arriere surchauffent par rapport aux avants.",
                    priority=RecommendationPriority.MEDIUM,
                    category=DiagnosticCategory.TIRE_WEAR,
                    parameter_changes=changes,
                    evidence=[
                        f"Stress avant: {behavior.front_tire_stress:.0f}%",
                        f"Stress arriere: {behavior.rear_tire_stress:.0f}%",
                    ],
                    expected_improvement="Meilleur equilibre d'usure",
                    confidence=65,
                    data_driven=True,
                ))

        return recs

    def _correlation_to_recommendation(
        self,
        corr
    ) -> SetupRecommendation | None:
        """Convert a correlation to a recommendation."""
        if corr.suggested_direction == "optimal":
            return None

        return SetupRecommendation(
            title=f"Ajuster {corr.parameter_name}",
            description=f"L'analyse de {corr.sample_count} sessions montre une correlation "
                       f"entre {corr.parameter_name} et le temps au tour.",
            priority=RecommendationPriority.MEDIUM,
            category=DiagnosticCategory.PERFORMANCE,
            parameter_changes=[
                ParameterRecommendation(
                    parameter_name=corr.parameter_name,
                    direction=corr.suggested_direction,
                    suggested_change=corr.suggested_change,
                    current_value=corr.parameter_value,
                )
            ],
            evidence=[
                f"Correlation: {corr.lap_time_correlation:.2f}",
                f"Sessions analysees: {corr.sample_count}",
            ],
            expected_improvement="Basee sur correlation statistique",
            confidence=corr.confidence,
            data_driven=True,
            correlation_strength=abs(corr.lap_time_correlation),
        )

    def _calculate_scores(
        self,
        session: SessionData,
        behavior: BehaviorStatistics
    ) -> dict[str, float]:
        """Calculate performance scores."""
        scores = {
            "overall": 50.0,
            "consistency": behavior.consistency,
            "pace": 50.0,
            "tire_management": 50.0,
        }

        # Pace score based on lap time variation from theoretical
        if session.valid_laps:
            lap_times = [lap.lap_time for lap in session.valid_laps]
            best = min(lap_times)
            avg = sum(lap_times) / len(lap_times)
            # Better pace = lower avg/best ratio
            pace_ratio = avg / best if best > 0 else 1
            scores["pace"] = max(0, min(100, 100 - (pace_ratio - 1) * 500))

        # Tire management based on wear balance
        tire_balance = 100 - abs(behavior.front_tire_stress - behavior.rear_tire_stress)
        scores["tire_management"] = max(0, tire_balance)

        # Overall is weighted average
        scores["overall"] = (
            scores["consistency"] * 0.3 +
            scores["pace"] * 0.4 +
            scores["tire_management"] * 0.3
        )

        return scores
