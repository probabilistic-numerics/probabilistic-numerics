"""ODE residual information operators."""

from typing import Callable, Tuple

import numpy as np

from probnum import problems, statespace
from probnum.diffeq.odefiltsmooth.information_operators import _information_operator
from probnum.typing import FloatArgType, IntArgType

__all__ = ["ODEResidual"]


class ODEResidual(_information_operator.ODEInformationOperator):
    """Information operator that measures the residual of an explicit ODE."""

    def __init__(self, prior_ordint: IntArgType, prior_spatialdim: IntArgType):
        integrator_dimension = prior_spatialdim * (prior_ordint + 1)
        expected_ode_dimension = prior_spatialdim
        super().__init__(
            input_dim=integrator_dimension, output_dim=expected_ode_dimension
        )

        # Prepare caching the projection matrices
        self.projection_matrices = None
        self.prior_ordint = prior_ordint
        self.prior_spatialdim = prior_spatialdim

        self._residual = None
        self._residual_jacobian = None

    def incorporate_ode(self, ode: problems.InitialValueProblem):
        """Incorporate the ODE and cache the required projection matrices."""
        super().incorporate_ode(ode=ode)

        # Cache the projection matrices and match the implementation to the ODE
        dummy_integrator = statespace.Integrator(
            ordint=self.prior_ordint, spatialdim=self.prior_spatialdim
        )
        ode_order = 1  # currently everything we can do
        self.projection_matrices = [
            dummy_integrator.proj2coord(coord=deriv) for deriv in range(ode_order + 1)
        ]
        res, res_jac = self._match_residual_and_jacobian_to_ode_order(
            ode_order=ode_order
        )
        self._residual, self._residual_jacobian = res, res_jac

    def _match_residual_and_jacobian_to_ode_order(
        self, ode_order: IntArgType
    ) -> Tuple[Callable, Callable]:
        """Choose the correct residual (and Jacobian) implementation based on the order
        of the ODE."""
        choose_implementation = {
            1: (self._residual_first_order_ode, self._residual_first_order_ode_jacobian)
        }
        return choose_implementation[ode_order]

    def __call__(self, t: FloatArgType, x: np.ndarray) -> np.ndarray:
        return self._residual(t, x)

    def jacobian(self, t: FloatArgType, x: np.ndarray) -> np.ndarray:
        return self._residual_jacobian(t, x)

    # Implementation of different residuals

    def _residual_first_order_ode(self, t: FloatArgType, x: np.ndarray) -> np.ndarray:
        h0, h1 = self.projection_matrices
        return h1 @ x - self.ode.f(t, h0 @ x)

    def _residual_first_order_ode_jacobian(
        self, t: FloatArgType, x: np.ndarray
    ) -> np.ndarray:
        h0, h1 = self.projection_matrices
        return h1 - self.ode.df(t, h0 @ x) @ h0
