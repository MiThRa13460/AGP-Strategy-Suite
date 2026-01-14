"""Traction diagnostic rules"""

from agp_core.setup.rules.base import Rule, RuleContext
from agp_core.setup.entities.diagnostic import (
    Diagnostic,
    Severity,
    DiagnosticCategory,
    ProblemType,
    CornerPhase,
)


class WheelspinRule(Rule):
    """Diagnose excessive wheelspin."""

    id = "wheelspin"
    name = "Excessive Wheelspin"
    category = DiagnosticCategory.TRACTION
    severity = Severity.WARNING
    problem_type = ProblemType.WHEELSPIN
    corner_phase = CornerPhase.ACCELERATION

    def evaluate(self, context: RuleContext) -> Diagnostic | None:
        feedback_lower = context.driver_feedback.lower()

        if any(kw in feedback_lower for kw in [
            "wheelspin", "patinage", "spinning", "traction",
            "roues qui patinent", "wheel spin"
        ]):
            diag = self.create_diagnostic(context)
            diag.description = (
                "Excessive wheelspin under acceleration, especially exiting slow corners. "
                "This reduces acceleration performance and tire life."
            )
            return diag

        return None

    def get_recommendations(self, context: RuleContext):
        setup = context.setup
        recs = []

        if setup.differential:
            new_power = max(20, setup.differential.power_lock.value - 15)
            recs.append((
                "Diff Power Lock",
                f"{setup.differential.power_lock.value:.0f}%",
                f"{new_power:.0f}%",
                "decrease",
                "-10-15%",
                0.9,
                "Lower power lock allows inside wheel to spin less, reducing wheelspin"
            ))

            new_preload = max(0, setup.differential.preload - 20)
            recs.append((
                "Diff Preload",
                f"{setup.differential.preload:.0f} Nm",
                f"{new_preload:.0f} Nm",
                "decrease",
                "-15-20 Nm",
                0.75,
                "Lower preload reduces initial diff lock effect"
            ))

        recs.append((
            "Traction Control",
            setup.traction_control,
            min(10, setup.traction_control + 2),
            "increase",
            "+2",
            0.95,
            "TC is the most effective way to manage wheelspin"
        ))

        if setup.suspension:
            rear_rh = setup.suspension.rear_ride_height
            recs.append((
                "Rear Ride Height",
                f"{rear_rh.mm:.0f}mm",
                f"{min(80, rear_rh.mm + 3):.0f}mm",
                "increase",
                "+2-3mm",
                0.65,
                "Higher rear can improve mechanical grip"
            ))

            rl_spring = setup.suspension.rear_left.spring_rate
            recs.append((
                "Rear Springs",
                f"{rl_spring.lbs_in:.0f} lbs/in",
                f"{rl_spring.lbs_in * 0.92:.0f} lbs/in",
                "decrease",
                "-5-8%",
                0.7,
                "Softer rear springs improve traction"
            ))

        return recs


class PowerOversteerRule(Rule):
    """Diagnose power oversteer."""

    id = "power_oversteer"
    name = "Power Oversteer"
    category = DiagnosticCategory.TRACTION
    severity = Severity.WARNING
    problem_type = ProblemType.POWER_OVERSTEER
    corner_phase = CornerPhase.EXIT

    def evaluate(self, context: RuleContext) -> Diagnostic | None:
        feedback_lower = context.driver_feedback.lower()

        if any(kw in feedback_lower for kw in [
            "power oversteer", "snap oversteer", "survirage acceleration",
            "rear snap", "arriere part a l'acceleration"
        ]):
            diag = self.create_diagnostic(context)
            diag.description = (
                "The rear snaps out suddenly when applying throttle. "
                "This is dangerous and needs to be addressed for car control."
            )
            diag.severity = Severity.CRITICAL
            return diag

        return None

    def get_recommendations(self, context: RuleContext):
        setup = context.setup
        recs = []

        if setup.differential:
            new_power = max(15, setup.differential.power_lock.value - 20)
            recs.append((
                "Diff Power Lock",
                f"{setup.differential.power_lock.value:.0f}%",
                f"{new_power:.0f}%",
                "decrease",
                "-15-20%",
                0.95,
                "CRITICAL: Lower power lock to reduce snap oversteer"
            ))

        recs.append((
            "Traction Control",
            setup.traction_control,
            min(10, setup.traction_control + 3),
            "increase",
            "+2-3",
            0.9,
            "TC helps prevent sudden power application issues"
        ))

        if setup.suspension:
            recs.append((
                "Rear ARB",
                setup.suspension.rear_arb,
                max(0, setup.suspension.rear_arb - 3),
                "decrease",
                "3-4 clicks",
                0.8,
                "Softer rear ARB gives more progressive rear behavior"
            ))

            rl = setup.suspension.rear_left
            recs.append((
                "Rear Slow Bump",
                rl.slow_bump,
                min(20, rl.slow_bump + 2),
                "increase",
                "+2 clicks",
                0.7,
                "Stiffer bump controls squat under acceleration"
            ))

        if setup.aero:
            recs.append((
                "Rear Wing",
                setup.aero.rear_wing,
                min(40, setup.aero.rear_wing + 3),
                "increase",
                "+2-3",
                0.75,
                "More rear downforce improves stability"
            ))

        return recs
