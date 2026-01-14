"""Diagnostic rules for setup analysis"""

from agp_core.setup.rules.base import Rule, RuleContext, RuleEngine
from agp_core.setup.rules.balance_rules import (
    UndersterrEntryRule,
    UndersterrMidRule,
    OversteerEntryRule,
    OversteerMidRule,
    OversteerExitRule,
)
from agp_core.setup.rules.traction_rules import (
    WheelspinRule,
    PowerOversteerRule,
)
from agp_core.setup.rules.brake_rules import (
    FrontLockupRule,
    RearLockupRule,
    BrakingInstabilityRule,
)


def create_default_engine() -> RuleEngine:
    """Create a RuleEngine with all default rules registered."""
    engine = RuleEngine()

    # Balance rules
    engine.register_rules([
        UndersterrEntryRule(),
        UndersterrMidRule(),
        OversteerEntryRule(),
        OversteerMidRule(),
        OversteerExitRule(),
    ])

    # Traction rules
    engine.register_rules([
        WheelspinRule(),
        PowerOversteerRule(),
    ])

    # Brake rules
    engine.register_rules([
        FrontLockupRule(),
        RearLockupRule(),
        BrakingInstabilityRule(),
    ])

    return engine


__all__ = [
    "Rule",
    "RuleContext",
    "RuleEngine",
    "create_default_engine",
    # Balance
    "UndersterrEntryRule",
    "UndersterrMidRule",
    "OversteerEntryRule",
    "OversteerMidRule",
    "OversteerExitRule",
    # Traction
    "WheelspinRule",
    "PowerOversteerRule",
    # Braking
    "FrontLockupRule",
    "RearLockupRule",
    "BrakingInstabilityRule",
]
