"""Integrated processes such as the integrated Wiener process or the Matern process.

This is the sucessor of the former ODEPrior.
"""
try:
    # cached_property is only available in Python >=3.8
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

import numpy as np
import scipy.special

import probnum.random_variables as pnrv

from . import discrete_transition, sde
from .preconditioner import NordsieckLikeCoordinates


class Integrator:
    """An integrator is a special kind of SDE, where the :math:`i` th coordinate models
    the :math:`i` th derivative."""

    def __init__(self, ordint, spatialdim):
        self.ordint = ordint
        self.spatialdim = spatialdim
        self.precon = None  # to be set later

    def setup_precon(self):
        # This can not be done in the init, due to the order in which
        # IBM, IOUP, and Matern initialise their superclasses.
        # Integrator needs to be initialised before LTISDE,
        # in which case via LTISDE, self.precon is set to None
        # To make up for this, we call this function here explicitly
        # after the calls to the superclasses' init.
        self.precon = NordsieckLikeCoordinates.from_order(self.ordint, self.spatialdim)

    def proj2coord(self, coord: int) -> np.ndarray:
        """Projection matrix to :math:`i` th coordinates.

        Computes the matrix

        .. math:: H_i = \\left[ I_d \\otimes e_i \\right] P^{-1},

        where :math:`e_i` is the :math:`i` th unit vector,
        that projects to the :math:`i` th coordinate of a vector.
        If the ODE is multidimensional, it projects to **each** of the
        :math:`i` th coordinates of each ODE dimension.

        Parameters
        ----------
        coord : int
            Coordinate index :math:`i` which to project to.
            Expected to be in range :math:`0 \\leq i \\leq q + 1`.

        Returns
        -------
        np.ndarray, shape=(d, d*(q+1))
            Projection matrix :math:`H_i`.
        """
        projvec1d = np.eye(self.ordint + 1)[:, coord]
        projmat1d = projvec1d.reshape((1, self.ordint + 1))
        projmat = np.kron(np.eye(self.spatialdim), projmat1d)
        return projmat


class IBM(Integrator, sde.LTISDE):
    """Integrated Brownian motion in :math:`d` dimensions."""

    def __init__(self, ordint, spatialdim):
        # initialise BOTH superclasses' inits.
        # I don't like it either, but it does the job.
        Integrator.__init__(self, ordint=ordint, spatialdim=spatialdim)
        sde.LTISDE.__init__(
            self,
            driftmat=self._driftmat,
            forcevec=self._forcevec,
            dispmat=self._dispmat,
        )
        self.setup_precon()

    @property
    def _driftmat(self):
        driftmat_1d = np.diag(np.ones(self.ordint), 1)
        return np.kron(np.eye(self.spatialdim), driftmat_1d)

    @property
    def _forcevec(self):
        force_1d = np.zeros(self.ordint + 1)
        return np.kron(np.ones(self.spatialdim), force_1d)

    @property
    def _dispmat(self):
        dispmat_1d = np.zeros(self.ordint + 1)
        dispmat_1d[-1] = 1.0  # Unit diffusion
        return np.kron(np.eye(self.spatialdim), dispmat_1d).T

    @cached_property
    def equivalent_discretisation_preconditioned(self):
        """Discretised IN THE PRECONDITIONED SPACE."""
        empty_shift = np.zeros(self.spatialdim * (self.ordint + 1))
        return discrete_transition.DiscreteLTIGaussian(
            state_trans_mat=self._state_trans_mat,
            shift_vec=empty_shift,
            proc_noise_cov_mat=self._proc_noise_cov_mat,
        )

    @cached_property
    def _state_trans_mat(self):
        # Loop, but cached anyway
        driftmat_1d = np.array(
            [
                [
                    scipy.special.binom(self.ordint - i, self.ordint - j)
                    for j in range(0, self.ordint + 1)
                ]
                for i in range(0, self.ordint + 1)
            ]
        )
        return np.kron(np.eye(self.spatialdim), driftmat_1d)

    @cached_property
    def _proc_noise_cov_mat(self):
        # Optimised with broadcasting
        range = np.arange(0, self.ordint + 1)
        denominators = 2.0 * self.ordint + 1.0 - range[:, None] - range[None, :]
        proc_noise_cov_mat_1d = 1.0 / denominators
        return np.kron(np.eye(self.spatialdim), proc_noise_cov_mat_1d)

    def transition_rv(self, rv, start, stop, _diffusion=1.0, **kwargs):
        if not isinstance(rv, pnrv.Normal):
            errormsg = (
                "Closed form transitions in LTI SDE models is only "
                "available for Gaussian initial conditions."
            )
            raise TypeError(errormsg)
        step = stop - start
        rv = self.precon.inverse(step) @ rv
        rv, info = self.equivalent_discretisation_preconditioned.transition_rv(
            rv, start, _diffusion=_diffusion
        )
        info["crosscov"] = self.precon(step) @ info["crosscov"] @ self.precon(step).T
        return self.precon(step) @ rv, info

    def transition_realization(self, real, start, stop, _diffusion=1.0, **kwargs):
        if not isinstance(real, np.ndarray):
            raise TypeError(f"Numpy array expected, {type(real)} received.")
        step = stop - start
        real = self.precon.inverse(step) @ real
        out = self.equivalent_discretisation_preconditioned.transition_realization(
            real, start, _diffusion=_diffusion
        )
        real, info = out
        info["crosscov"] = self.precon(step) @ info["crosscov"] @ self.precon(step).T
        return self.precon(step) @ real, info

    def discretise(self, step):
        """Equivalent discretisation of the process.

        Overwrites matrix-fraction decomposition in the super-class.
        Only present for user's convenience and to maintain a clean
        interface. Not used for transition_rv, etc..
        """

        state_trans_mat = (
            self.precon(step)
            @ self.equivalent_discretisation_preconditioned.state_trans_mat
            @ self.precon.inverse(step)
        )
        proc_noise_cov_mat = (
            self.precon(step)
            @ self.equivalent_discretisation_preconditioned.proc_noise_cov_mat
            @ self.precon(step).T
        )
        zero_shift = np.zeros(len(state_trans_mat))
        return discrete_transition.DiscreteLTIGaussian(
            state_trans_mat=state_trans_mat,
            shift_vec=zero_shift,
            proc_noise_cov_mat=proc_noise_cov_mat,
        )


class IOUP(Integrator, sde.LTISDE):
    """Integrated Ornstein-Uhlenbeck process in :math:`d` dimensions."""

    def __init__(
        self,
        ordint: int,
        spatialdim: int,
        driftspeed: float,
    ):
        # Other than previously in ProbNum, we do not use preconditioning for IOUP by default.
        self.driftspeed = driftspeed

        Integrator.__init__(self, ordint=ordint, spatialdim=spatialdim)
        sde.LTISDE.__init__(
            self,
            driftmat=self._driftmat,
            forcevec=self._forcevec,
            dispmat=self._dispmat,
        )
        self.setup_precon()

    @property
    def _driftmat(self):
        driftmat_1d = np.diag(np.ones(self.ordint), 1)
        driftmat_1d[-1, -1] = -self.driftspeed
        return np.kron(np.eye(self.spatialdim), driftmat_1d)

    @property
    def _forcevec(self):
        force_1d = np.zeros(self.ordint + 1)
        return np.kron(np.ones(self.spatialdim), force_1d)

    @property
    def _dispmat(self):
        dispmat_1d = np.zeros(self.ordint + 1)
        dispmat_1d[-1] = 1.0  # Unit Diffusion
        return np.kron(np.eye(self.spatialdim), dispmat_1d).T


class Matern(Integrator, sde.LTISDE):
    """Matern process in :math:`d` dimensions."""

    def __init__(
        self,
        ordint: int,
        spatialdim: int,
        lengthscale: float,
    ):

        self.lengthscale = lengthscale

        Integrator.__init__(self, ordint=ordint, spatialdim=spatialdim)
        sde.LTISDE.__init__(
            self,
            driftmat=self._driftmat,
            forcevec=self._forcevec,
            dispmat=self._dispmat,
        )
        self.setup_precon()

    @property
    def _driftmat(self):
        driftmat = np.diag(np.ones(self.ordint), 1)
        nu = self.ordint + 0.5
        D, lam = self.ordint + 1, np.sqrt(2 * nu) / self.lengthscale
        driftmat[-1, :] = np.array(
            [-scipy.special.binom(D, i) * lam ** (D - i) for i in range(D)]
        )
        return np.kron(np.eye(self.spatialdim), driftmat)

    @property
    def _forcevec(self):
        force_1d = np.zeros(self.ordint + 1)
        return np.kron(np.ones(self.spatialdim), force_1d)

    @property
    def _dispmat(self):
        dispmat_1d = np.zeros(self.ordint + 1)
        dispmat_1d[-1] = 1.0  # Unit diffusion
        return np.kron(np.eye(self.spatialdim), dispmat_1d).T
