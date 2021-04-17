""""""
import numpy as np

import probnum._randomvariablelist as pnrv_list
import probnum.diffeq as pnd
import probnum.randvars as pnrv


class ScipyODESolution(pnd.ODESolution):
    def __init__(self, scipy_solution, times, rvs):
        """Evaluate the time-continuous solution at time t.
        Parameters
        ----------
        t : float
            Location / time at which to evaluate the continuous ODE solution.
        Returns
        -------
        :obj:`RandomVariable`
            Probabilistic estimate of the continuous-time solution at time ``t``.
        """
        self.scipy_solution = scipy_solution
        self.times = times
        # self.y = pnrv_list._RandomVariableList(rvs)
        self.states = pnrv_list._RandomVariableList(rvs)

    @property
    def t(self):
        """Time points of the discrete-time solution."""
        return self.times

    @property
    def y(self):
        """Discrete-time solution."""
        return np.array(self.y)

    def __call__(self, t):
        """"solution as _RandomVariableList."""
        states = np.array(self.scipy_solution(t)).T
        solution_as_rv = pnrv_list._RandomVariableList(
            list(map(lambda x: (pnrv.Constant(x)), states))
        )
        return solution_as_rv

    def __len__(self):
        """Number of points in the discrete-time solution."""
        return len(self.scipy_solution.ts)

    def __getitem__(self, idx):
        """Access the discrete-time solution through indexing and slicing."""
        return self.scipy_solution.interpolants[idx](self.scipy_solution.ts[idx])

    def sample(self, t=None, size=()):
        return "Not possible"
