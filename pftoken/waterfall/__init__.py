"""Payment waterfall analytics."""

from .debt_structure import DebtStructure, Tranche
from .covenants import Covenant, CovenantBreach, CovenantEngine, CovenantSeverity, CovenantType
from .waterfall_engine import ReserveState, WaterfallEngine, WaterfallResult
from .comparator import ComparisonResult, StructureComparator
from .full_waterfall import FullWaterfallResult, WaterfallOrchestrator
from .governance import GovernanceController, LoggingAction, StaticOracle, ThresholdPolicy
from .governance_interfaces import GovernancePolicy, IOracle, IGovernanceAction
from .contingent_amortization import (
    AmortizationType,
    ContingentAmortizationConfig,
    ContingentAmortizationEngine,
    DualStructureComparator,
    PathSimulationResult,
    PeriodPaymentResult,
    StructureComparisonResult,
    TraditionalAmortizationEngine,
)

__all__ = [
    "DebtStructure",
    "Tranche",
    "Covenant",
    "CovenantBreach",
    "CovenantEngine",
    "CovenantSeverity",
    "CovenantType",
    "ReserveState",
    "WaterfallEngine",
    "WaterfallResult",
    "WaterfallOrchestrator",
    "FullWaterfallResult",
    "GovernanceController",
    "GovernancePolicy",
    "IOracle",
    "IGovernanceAction",
    "StaticOracle",
    "ThresholdPolicy",
    "LoggingAction",
    "ComparisonResult",
    "StructureComparator",
    # Contingent amortization (WP-12)
    "AmortizationType",
    "ContingentAmortizationConfig",
    "ContingentAmortizationEngine",
    "DualStructureComparator",
    "PathSimulationResult",
    "PeriodPaymentResult",
    "StructureComparisonResult",
    "TraditionalAmortizationEngine",
]
