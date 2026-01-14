"""Base classes for diagnostic rules"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from agp_core.setup.entities.setup import Setup
from agp_core.setup.entities.diagnostic import (
    Diagnostic,
    Severity,
    DiagnosticCategory,
    ProblemType,
    CornerPhase,
)


@dataclass
class RuleContext:
    """Context data for rule evaluation."""

    setup: Setup
    telemetry: dict[str, Any] = field(default_factory=dict)
    driver_feedback: str = ""
    track_id: str = ""
    conditions: str = "dry"  # dry, wet, mixed


class Rule(ABC):
    """Base class for diagnostic rules."""

    id: str
    name: str
    category: DiagnosticCategory
    severity: Severity
    problem_type: ProblemType | None = None
    corner_phase: CornerPhase | None = None

    @abstractmethod
    def evaluate(self, context: RuleContext) -> Diagnostic | None:
        """
        Evaluate the rule against the given context.

        Returns a Diagnostic if the rule matches, None otherwise.
        """
        pass

    @abstractmethod
    def get_recommendations(
        self, context: RuleContext
    ) -> list[tuple[str, Any, Any, str, str, float, str]]:
        """
        Get parameter recommendations.

        Returns list of tuples:
        (parameter, current, recommended, direction, amount, confidence, explanation)
        """
        pass

    def create_diagnostic(self, context: RuleContext) -> Diagnostic:
        """Create a diagnostic with recommendations."""
        diag = Diagnostic(
            title=self.name,
            severity=self.severity,
            category=self.category,
            problem_type=self.problem_type,
            corner_phase=self.corner_phase,
        )

        for rec in self.get_recommendations(context):
            diag.add_recommendation(*rec)

        return diag


class RuleEngine:
    """Engine that runs diagnostic rules against a setup."""

    def __init__(self) -> None:
        self.rules: list[Rule] = []

    def register_rule(self, rule: Rule) -> None:
        """Register a rule with the engine."""
        self.rules.append(rule)

    def register_rules(self, rules: list[Rule]) -> None:
        """Register multiple rules."""
        self.rules.extend(rules)

    def evaluate(self, context: RuleContext) -> list[Diagnostic]:
        """
        Evaluate all rules against the context.

        Returns a list of diagnostics, sorted by priority.
        """
        diagnostics: list[Diagnostic] = []

        for rule in self.rules:
            diagnostic = rule.evaluate(context)
            if diagnostic:
                diagnostics.append(diagnostic)

        # Sort by severity (critical first) then by priority
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.WARNING: 1,
            Severity.INFO: 2,
            Severity.SUCCESS: 3,
        }

        diagnostics.sort(
            key=lambda d: (severity_order.get(d.severity, 99), d.priority)
        )

        return diagnostics

    def evaluate_for_problem(
        self,
        context: RuleContext,
        problem_type: ProblemType,
    ) -> list[Diagnostic]:
        """Evaluate only rules for a specific problem type."""
        diagnostics: list[Diagnostic] = []

        for rule in self.rules:
            if rule.problem_type == problem_type:
                diagnostic = rule.evaluate(context)
                if diagnostic:
                    diagnostics.append(diagnostic)

        return diagnostics
