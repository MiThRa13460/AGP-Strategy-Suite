"""Setup engineering module for AGP Strategy Suite

Includes:
- Setup entities and value objects
- SVM file parser
- Rule-based diagnostics
- CSV telemetry analysis
- Data-driven recommendation engine
"""

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
from agp_core.setup.parsers import SVMParser
from agp_core.setup.rules.base import Rule, RuleContext, RuleEngine

# CSV Analysis
from agp_core.setup.csv_parser import CSVParser, CSVFormat
from agp_core.setup.telemetry_models import (
    TelemetryPoint,
    LapData,
    SessionData,
    CornerAnalysis,
    CornerType,
    CornerDirection,
    BehaviorStatistics,
    SetupCorrelation,
    AnalysisResult,
)
from agp_core.setup.telemetry_analyzer import TelemetryAnalyzer
from agp_core.setup.setup_correlator import SetupCorrelator
from agp_core.setup.recommendation_engine import (
    RecommendationEngine,
    SetupRecommendation,
    RecommendationPriority,
)

__all__ = [
    # Entities
    "Setup",
    "SuspensionSetup",
    "CornerSetup",
    "CornerPosition",
    "DifferentialSetup",
    "AeroSetup",
    "BrakeSetup",
    # Diagnostics
    "Diagnostic",
    "Severity",
    "DiagnosticCategory",
    "ProblemType",
    "CornerPhase",
    "ParameterRecommendation",
    # Parser
    "SVMParser",
    # Rules
    "Rule",
    "RuleContext",
    "RuleEngine",
    # CSV Analysis
    "CSVParser",
    "CSVFormat",
    "TelemetryPoint",
    "LapData",
    "SessionData",
    "CornerAnalysis",
    "CornerType",
    "CornerDirection",
    "BehaviorStatistics",
    "SetupCorrelation",
    "AnalysisResult",
    "TelemetryAnalyzer",
    "SetupCorrelator",
    "RecommendationEngine",
    "SetupRecommendation",
    "RecommendationPriority",
]
