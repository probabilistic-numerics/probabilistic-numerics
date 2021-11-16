"""Stopping criteria for Bayesian quadrature methods."""

from ._bq_stopping_criterion import BQStoppingCriterion
from ._integral_variance_tol import IntegralVarianceTolerance
from ._rel_mean_change import RelativeMeanChange
from ._max_nevals import MaxNevals

# Public classes and functions. Order is reflected in documentation.
__all__ = [
    "BQStoppingCriterion",
    "IntegralVarianceTolerance",
    "RelativeMeanChange",
    "MaxNevals",
]

# Set correct module paths. Corrects links and module paths in documentation.
BQStoppingCriterion.__module__ = "probnum.quad.solvers.stopping_criteria"
IntegralVarianceTolerance.__module__ = "probnum.quad.solvers.stopping_criteria"
RelativeMeanChange.__module__ = "probnum.quad.solvers.stopping_criteria"
MaxNevals.__module__ = "probnum.quad.solvers.stopping_criteria"
