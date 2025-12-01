"""Monte Carlo simulation package."""

from .breach_probability import BreachProbabilityAnalyzer, BreachCurves
from .correlation import CorrelatedSampler, CorrelationMatrix, CorrelationMetadata
from .default_flags import DefaultDetector, DefaultFlags
from .merton_integration import TranchePathMetrics, compute_pathwise_pd_lgd, loss_paths_from_pd_lgd
from .monte_carlo import MonteCarloConfig, MonteCarloEngine, MonteCarloResult
from .path_dependent import PathDependentConfig, evaluate_first_passage
from .path_callbacks import build_financial_path_callback
from .pipeline import MonteCarloPipeline, PipelineInputs, PipelineOutputs
from .regime_switching import RegimeConfig, RegimeParams, RegimeSwitchingProcess
from .ratio_simulation import RatioDistributions, RatioSummary
from .stochastic_vars import SampleSummary, StochasticVariables

__all__ = [
    "SampleSummary",
    "StochasticVariables",
    "CorrelatedSampler",
    "CorrelationMatrix",
    "CorrelationMetadata",
    "MonteCarloConfig",
    "MonteCarloEngine",
    "MonteCarloResult",
    "build_financial_path_callback",
    "PathDependentConfig",
    "evaluate_first_passage",
    "RegimeConfig",
    "RegimeParams",
    "RegimeSwitchingProcess",
    "TranchePathMetrics",
    "compute_pathwise_pd_lgd",
    "loss_paths_from_pd_lgd",
    "DefaultDetector",
    "DefaultFlags",
    "RatioDistributions",
    "RatioSummary",
    "MonteCarloPipeline",
    "PipelineInputs",
    "PipelineOutputs",
    "BreachProbabilityAnalyzer",
    "BreachCurves",
]
