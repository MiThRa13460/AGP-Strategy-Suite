"""Brake diagnostic rules"""

from agp_core.setup.rules.base import Rule, RuleContext
from agp_core.setup.entities.diagnostic import (
    Diagnostic,
    Severity,
    DiagnosticCategory,
    ProblemType,
    CornerPhase,
)


class FrontLockupRule(Rule):
    """Diagnose front wheel lockup under braking."""

    id = "front_lockup"
    name = "Front Wheel Lockup"
    category = DiagnosticCategory.BRAKING
    severity = Severity.WARNING
    problem_type = ProblemType.FRONT_LOCKUP
    corner_phase = CornerPhase.BRAKING

    def evaluate(self, context: RuleContext) -> Diagnostic | None:
        feedback_lower = context.driver_feedback.lower()

        if any(kw in feedback_lower for kw in [
            "front lock", "front lockup", "blocage avant",
            "front wheels lock", "avant bloque"
        ]):
            diag = self.create_diagnostic(context)
            diag.description = (
                "The front wheels are locking under braking. "
                "This causes flat spots, reduces steering, and extends braking distance."
            )
            return diag

        return None

    def get_recommendations(self, context: RuleContext):
        setup = context.setup
        recs = []

        if setup.brakes:
            new_bias = max(50, setup.brakes.bias.value - 3)
            recs.append((
                "Brake Bias",
                f"{setup.brakes.bias.value:.1f}%",
                f"{new_bias:.1f}%",
                "decrease",
                "-2-3%",
                0.9,
                "Less front brake pressure prevents front lockup"
            ))

            if setup.brakes.pressure.value > 90:
                new_pressure = setup.brakes.pressure.value - 5
                recs.append((
                    "Brake Pressure",
                    f"{setup.brakes.pressure.value:.0f}%",
                    f"{new_pressure:.0f}%",
                    "decrease",
                    "-5%",
                    0.7,
                    "Lower overall pressure if modulation is difficult"
                ))

        if setup.suspension:
            front_rh = setup.suspension.front_ride_height
            recs.append((
                "Front Ride Height",
                f"{front_rh.mm:.0f}mm",
                f"{min(80, front_rh.mm + 2):.0f}mm",
                "increase",
                "+2mm",
                0.5,
                "Slightly higher front can reduce dive and lockup tendency"
            ))

        return recs


class RearLockupRule(Rule):
    """Diagnose rear wheel lockup under braking."""

    id = "rear_lockup"
    name = "Rear Wheel Lockup"
    category = DiagnosticCategory.BRAKING
    severity = Severity.CRITICAL
    problem_type = ProblemType.REAR_LOCKUP
    corner_phase = CornerPhase.BRAKING

    def evaluate(self, context: RuleContext) -> Diagnostic | None:
        feedback_lower = context.driver_feedback.lower()

        if any(kw in feedback_lower for kw in [
            "rear lock", "rear lockup", "blocage arriere",
            "rear wheels lock", "arriere bloque", "spin braking"
        ]):
            diag = self.create_diagnostic(context)
            diag.description = (
                "The rear wheels are locking under braking. "
                "This is DANGEROUS and causes spins. Must be fixed immediately."
            )
            diag.severity = Severity.CRITICAL
            return diag

        return None

    def get_recommendations(self, context: RuleContext):
        setup = context.setup
        recs = []

        if setup.brakes:
            new_bias = min(65, setup.brakes.bias.value + 4)
            recs.append((
                "Brake Bias",
                f"{setup.brakes.bias.value:.1f}%",
                f"{new_bias:.1f}%",
                "increase",
                "+3-4%",
                0.95,
                "CRITICAL: More front bias prevents dangerous rear lockup"
            ))

        if setup.differential:
            new_coast = min(80, setup.differential.coast_lock.value + 15)
            recs.append((
                "Diff Coast Lock",
                f"{setup.differential.coast_lock.value:.0f}%",
                f"{new_coast:.0f}%",
                "increase",
                "+10-15%",
                0.8,
                "Higher coast lock prevents inside rear from locking"
            ))

        if setup.suspension:
            recs.append((
                "Rear ARB",
                setup.suspension.rear_arb,
                max(0, setup.suspension.rear_arb - 2),
                "decrease",
                "2-3 clicks",
                0.7,
                "Softer rear ARB gives more rear grip under braking"
            ))

        return recs


class BrakingInstabilityRule(Rule):
    """Diagnose general instability under braking."""

    id = "braking_instability"
    name = "Braking Instability"
    category = DiagnosticCategory.BRAKING
    severity = Severity.WARNING
    problem_type = ProblemType.INSTABILITY_BRAKING
    corner_phase = CornerPhase.BRAKING

    def evaluate(self, context: RuleContext) -> Diagnostic | None:
        feedback_lower = context.driver_feedback.lower()

        if any(kw in feedback_lower for kw in [
            "unstable braking", "instable freinage", "dancing",
            "brake instability", "nervous braking"
        ]):
            diag = self.create_diagnostic(context)
            diag.description = (
                "The car feels unstable and nervous under heavy braking. "
                "This makes it hard to brake late and accurately."
            )
            return diag

        return None

    def get_recommendations(self, context: RuleContext):
        setup = context.setup
        recs = []

        if setup.suspension:
            fl = setup.suspension.front_left
            recs.append((
                "Front Slow Rebound",
                fl.slow_rebound,
                min(20, fl.slow_rebound + 2),
                "increase",
                "+2 clicks",
                0.75,
                "Stiffer rebound controls front dive oscillation"
            ))

            rl = setup.suspension.rear_left
            recs.append((
                "Rear Slow Bump",
                rl.slow_bump,
                min(20, rl.slow_bump + 2),
                "increase",
                "+2 clicks",
                0.7,
                "Stiffer rear bump controls lift under braking"
            ))

        if setup.differential:
            new_coast = min(80, setup.differential.coast_lock.value + 10)
            recs.append((
                "Diff Coast Lock",
                f"{setup.differential.coast_lock.value:.0f}%",
                f"{new_coast:.0f}%",
                "increase",
                "+5-10%",
                0.8,
                "Higher coast lock improves straight-line stability"
            ))

        return recs
