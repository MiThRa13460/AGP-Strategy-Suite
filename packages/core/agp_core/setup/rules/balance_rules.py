"""Balance diagnostic rules (understeer/oversteer)"""

from agp_core.setup.rules.base import Rule, RuleContext
from agp_core.setup.entities.diagnostic import (
    Diagnostic,
    Severity,
    DiagnosticCategory,
    ProblemType,
    CornerPhase,
)


class UndersterrEntryRule(Rule):
    """Diagnose understeer on corner entry."""

    id = "understeer_entry"
    name = "Understeer on Entry"
    category = DiagnosticCategory.BALANCE
    severity = Severity.WARNING
    problem_type = ProblemType.UNDERSTEER_ENTRY
    corner_phase = CornerPhase.ENTRY

    def evaluate(self, context: RuleContext) -> Diagnostic | None:
        feedback_lower = context.driver_feedback.lower()

        if any(kw in feedback_lower for kw in ["understeer entry", "push entry", "sous-virage entree"]):
            diag = self.create_diagnostic(context)
            diag.description = (
                "The car pushes (understeers) when entering corners, especially during "
                "trail braking. The front tires lose grip before the rears."
            )
            return diag

        return None

    def get_recommendations(self, context: RuleContext):
        setup = context.setup
        recs = []

        if setup.suspension:
            recs.append((
                "Front ARB",
                setup.suspension.front_arb,
                max(0, setup.suspension.front_arb - 2),
                "decrease",
                "2-3 clicks",
                0.85,
                "Softer front ARB increases mechanical grip on entry"
            ))

            recs.append((
                "Rear ARB",
                setup.suspension.rear_arb,
                min(20, setup.suspension.rear_arb + 2),
                "increase",
                "2-3 clicks",
                0.75,
                "Stiffer rear ARB reduces rear grip, rotating the car"
            ))

        if setup.brakes:
            new_bias = max(50, setup.brakes.bias.value - 2)
            recs.append((
                "Brake Bias",
                f"{setup.brakes.bias.value:.1f}%",
                f"{new_bias:.1f}%",
                "decrease",
                "-1-2%",
                0.8,
                "More rear braking rotates the car on entry"
            ))

        if setup.differential:
            new_coast = max(10, setup.differential.coast_lock.value - 10)
            recs.append((
                "Diff Coast Lock",
                f"{setup.differential.coast_lock.value:.0f}%",
                f"{new_coast:.0f}%",
                "decrease",
                "-5-10%",
                0.7,
                "Lower coast lock allows more rotation on deceleration"
            ))

        return recs


class UndersterrMidRule(Rule):
    """Diagnose understeer at mid-corner."""

    id = "understeer_mid"
    name = "Understeer at Mid-Corner"
    category = DiagnosticCategory.BALANCE
    severity = Severity.WARNING
    problem_type = ProblemType.UNDERSTEER_MID
    corner_phase = CornerPhase.MID

    def evaluate(self, context: RuleContext) -> Diagnostic | None:
        feedback_lower = context.driver_feedback.lower()

        if any(kw in feedback_lower for kw in ["understeer mid", "push mid", "sous-virage milieu"]):
            diag = self.create_diagnostic(context)
            diag.description = (
                "The car understeers at the apex and through mid-corner. "
                "This is typically a mechanical grip issue at the front."
            )
            return diag

        return None

    def get_recommendations(self, context: RuleContext):
        setup = context.setup
        recs = []

        if setup.suspension:
            fl_spring = setup.suspension.front_left.spring_rate
            recs.append((
                "Front Springs",
                f"{fl_spring.lbs_in:.0f} lbs/in",
                f"{fl_spring.lbs_in * 0.95:.0f} lbs/in",
                "decrease",
                "-5%",
                0.75,
                "Softer front springs increase mechanical grip at apex"
            ))

            front_camber = setup.suspension.front_camber_avg
            recs.append((
                "Front Camber",
                f"{front_camber.degrees:.1f}",
                f"{front_camber.degrees - 0.3:.1f}",
                "increase negative",
                "-0.2 to -0.3",
                0.8,
                "More negative camber improves cornering grip"
            ))

            front_rh = setup.suspension.front_ride_height
            recs.append((
                "Front Ride Height",
                f"{front_rh.mm:.0f}mm",
                f"{max(20, front_rh.mm - 3):.0f}mm",
                "decrease",
                "-2-3mm",
                0.7,
                "Lower front increases front downforce effect"
            ))

        return recs


class OversteerEntryRule(Rule):
    """Diagnose oversteer on corner entry."""

    id = "oversteer_entry"
    name = "Oversteer on Entry"
    category = DiagnosticCategory.BALANCE
    severity = Severity.WARNING
    problem_type = ProblemType.OVERSTEER_ENTRY
    corner_phase = CornerPhase.ENTRY

    def evaluate(self, context: RuleContext) -> Diagnostic | None:
        feedback_lower = context.driver_feedback.lower()

        if any(kw in feedback_lower for kw in ["oversteer entry", "loose entry", "survirage entree"]):
            diag = self.create_diagnostic(context)
            diag.description = (
                "The rear of the car becomes loose/slides when entering corners, "
                "especially under braking. This can lead to spins."
            )
            return diag

        return None

    def get_recommendations(self, context: RuleContext):
        setup = context.setup
        recs = []

        if setup.suspension:
            recs.append((
                "Rear ARB",
                setup.suspension.rear_arb,
                max(0, setup.suspension.rear_arb - 2),
                "decrease",
                "2-3 clicks",
                0.85,
                "Softer rear ARB increases rear grip on entry"
            ))

            recs.append((
                "Front ARB",
                setup.suspension.front_arb,
                min(20, setup.suspension.front_arb + 2),
                "increase",
                "2-3 clicks",
                0.75,
                "Stiffer front ARB reduces front grip transfer"
            ))

        if setup.brakes:
            new_bias = min(65, setup.brakes.bias.value + 2)
            recs.append((
                "Brake Bias",
                f"{setup.brakes.bias.value:.1f}%",
                f"{new_bias:.1f}%",
                "increase",
                "+1-2%",
                0.85,
                "More front braking stabilizes rear on entry"
            ))

        if setup.differential:
            new_coast = min(80, setup.differential.coast_lock.value + 10)
            recs.append((
                "Diff Coast Lock",
                f"{setup.differential.coast_lock.value:.0f}%",
                f"{new_coast:.0f}%",
                "increase",
                "+5-10%",
                0.75,
                "Higher coast lock stabilizes rear under decel"
            ))

        return recs


class OversteerMidRule(Rule):
    """Diagnose oversteer at mid-corner."""

    id = "oversteer_mid"
    name = "Oversteer at Mid-Corner"
    category = DiagnosticCategory.BALANCE
    severity = Severity.WARNING
    problem_type = ProblemType.OVERSTEER_MID
    corner_phase = CornerPhase.MID

    def evaluate(self, context: RuleContext) -> Diagnostic | None:
        feedback_lower = context.driver_feedback.lower()

        if any(kw in feedback_lower for kw in ["oversteer mid", "loose mid", "survirage milieu"]):
            diag = self.create_diagnostic(context)
            diag.description = (
                "The rear slides at mid-corner during steady-state cornering. "
                "This indicates a mechanical grip imbalance."
            )
            return diag

        return None

    def get_recommendations(self, context: RuleContext):
        setup = context.setup
        recs = []

        if setup.suspension:
            rl_spring = setup.suspension.rear_left.spring_rate
            recs.append((
                "Rear Springs",
                f"{rl_spring.lbs_in:.0f} lbs/in",
                f"{rl_spring.lbs_in * 0.95:.0f} lbs/in",
                "decrease",
                "-5%",
                0.75,
                "Softer rear springs increase mechanical rear grip"
            ))

            rear_camber = setup.suspension.rear_camber_avg
            recs.append((
                "Rear Camber",
                f"{rear_camber.degrees:.1f}",
                f"{rear_camber.degrees - 0.2:.1f}",
                "increase negative",
                "-0.2",
                0.8,
                "More negative camber improves rear cornering grip"
            ))

        if setup.aero:
            recs.append((
                "Rear Wing",
                setup.aero.rear_wing,
                min(40, setup.aero.rear_wing + 2),
                "increase",
                "+1-2",
                0.7,
                "More rear downforce increases rear grip"
            ))

        return recs


class OversteerExitRule(Rule):
    """Diagnose oversteer on corner exit."""

    id = "oversteer_exit"
    name = "Oversteer on Exit (Power Oversteer)"
    category = DiagnosticCategory.BALANCE
    severity = Severity.WARNING
    problem_type = ProblemType.OVERSTEER_EXIT
    corner_phase = CornerPhase.EXIT

    def evaluate(self, context: RuleContext) -> Diagnostic | None:
        feedback_lower = context.driver_feedback.lower()

        if any(kw in feedback_lower for kw in [
            "oversteer exit", "loose exit", "survirage sortie",
            "power oversteer", "wheelspin exit"
        ]):
            diag = self.create_diagnostic(context)
            diag.description = (
                "The rear slides when applying power exiting corners. "
                "This is often due to differential settings or traction issues."
            )
            return diag

        return None

    def get_recommendations(self, context: RuleContext):
        setup = context.setup
        recs = []

        if setup.differential:
            new_power = max(20, setup.differential.power_lock.value - 10)
            recs.append((
                "Diff Power Lock",
                f"{setup.differential.power_lock.value:.0f}%",
                f"{new_power:.0f}%",
                "decrease",
                "-5-10%",
                0.85,
                "Lower power lock reduces wheelspin tendency"
            ))

            new_preload = max(0, setup.differential.preload - 10)
            recs.append((
                "Diff Preload",
                f"{setup.differential.preload:.0f} Nm",
                f"{new_preload:.0f} Nm",
                "decrease",
                "-10 Nm",
                0.7,
                "Lower preload allows more wheel speed difference"
            ))

        if setup.suspension:
            rear_rh = setup.suspension.rear_ride_height
            recs.append((
                "Rear Ride Height",
                f"{rear_rh.mm:.0f}mm",
                f"{min(80, rear_rh.mm + 2):.0f}mm",
                "increase",
                "+2mm",
                0.6,
                "Higher rear can improve traction"
            ))

        recs.append((
            "Traction Control",
            setup.traction_control,
            min(10, setup.traction_control + 1),
            "increase",
            "+1",
            0.9,
            "TC helps manage wheelspin on exit"
        ))

        return recs
