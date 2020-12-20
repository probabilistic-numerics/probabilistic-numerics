"""Observation operators of probabilistic linear solvers."""

from typing import Callable

import numpy as np

from probnum.problems import LinearSystem


class ObservationOperator:
    """Observation operator of probabilistic linear solvers.

    Defines the way observations about the linear system are collected for a given
    action.

    Parameters
    ----------
    observation_op
        Callable defining the observation process.

    Examples
    --------
    """

    def __init__(
        self, observation_op: Callable[[LinearSystem, np.ndarray], np.ndarray]
    ):
        self._observation_op = observation_op

    def __call__(self, problem: LinearSystem, action: np.ndarray) -> np.ndarray:
        """Collect an observation about the linear system.

        Parameters
        ----------
        problem :
            Linear system to solve.
        action
            Action to probe linear system.
        """
        return self._observation_op(problem, action)


class MatrixMultObservation(ObservationOperator):
    r"""Matrix-vector product observations.

    Given an action :math:`s` collect an observation :math:`y` of the linear system by
    multiplying with the system matrix :math:`y = As`.
    """

    def __init__(self):
        super().__init__(observation_op=self.__call__)

    def __call__(self, problem: LinearSystem, action: np.ndarray) -> np.ndarray:
        return problem.A @ action
