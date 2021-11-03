"""Belief update in a matrix-based inference view where the information is given by
matrix-vector multiplication."""
import numpy as np

import probnum  # pylint: disable="unused-import"
from probnum import linops, randvars
from probnum.linalg.solvers.beliefs import LinearSystemBelief

from ._linear_solver_belief_update import LinearSolverBeliefUpdate


class MatrixBasedLinearBeliefUpdate(LinearSolverBeliefUpdate):
    r"""Gaussian belief update in a matrix-based inference framework assuming linear information.

    Updates the belief over the quantities of interest of a linear system :math:`Ax=b` given matrix-variate Gaussian beliefs with Kronecker covariance structure and linear observations. The belief update computes :math:`p(M \mid y) = \mathcal{N}(M; M_{i+1}, V \otimes W_{i+1})`, [1]_ [2]_ such that

    .. math ::
        \begin{align}
            M_{i+1} &= M_i + (y - M_i s) (s^\top W_i s)^\dagger s^\top W_i,\\
            W_{i+1} &= W_i - W_i s (s^\top W s)^\dagger s^\top W_i.
        \end{align}


    References
    ----------
    .. [1] Hennig, P., Probabilistic Interpretation of Linear Solvers, *SIAM Journal on
       Optimization*, 2015, 25, 234-260
    .. [2] Wenger, J. and Hennig, P., Probabilistic Linear Solvers for Machine Learning,
       *Advances in Neural Information Processing Systems (NeurIPS)*, 2020
    """

    def __call__(
        self, solver_state: "probnum.linalg.solvers.LinearSolverState"
    ) -> LinearSystemBelief:

        # Inference for A
        A = self._matrix_based_update(
            matrix=solver_state.belief.A,
            action=solver_state.action,
            observ=solver_state.observation,
        )

        # Inference for Ainv (interpret action and observation as swapped)
        Ainv = self._matrix_based_update(
            matrix=solver_state.belief.Ainv,
            action=solver_state.observation,
            observ=solver_state.action,
        )
        return LinearSystemBelief(A=A, Ainv=Ainv, x=None, b=solver_state.belief.b)

    def _matrix_based_update(
        self, matrix: randvars.Normal, action: np.ndarray, observ: np.ndarray
    ) -> randvars.Normal:
        """Matrix-based inference update for linear information."""
        if not isinstance(matrix.cov, linops.Kronecker):
            raise ValueError(
                f"Covariance must have Kronecker structure, but is '{type(matrix.cov).__name__}'."
            )

        pred = matrix.mean @ action
        resid = observ - pred
        covfactor_Ms = matrix.cov.B @ action
        gram = action.T @ covfactor_Ms
        gram_pinv = 1.0 / gram if gram > 0.0 else 0.0
        gain = covfactor_Ms * gram_pinv
        covfactor_update = linops.aslinop(gain[:, None]) @ linops.aslinop(
            covfactor_Ms[None, :]
        )
        resid_gain = linops.aslinop(resid[:, None]) @ linops.aslinop(
            gain[None, :]
        )  # residual and gain are flipped due to matrix vectorization

        return randvars.Normal(
            mean=matrix.mean + resid_gain,
            cov=linops.Kronecker(A=matrix.cov.A, B=matrix.cov.B - covfactor_update),
        )
