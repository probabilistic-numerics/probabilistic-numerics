"""Discrete transitions."""
import typing
from typing import Callable, Optional

import numpy as np

import probnum.random_variables as pnrv
from probnum.type import FloatArgType

from . import transition as trans
from .discrete_transition_utils import (
    cholesky_update,
    condition_state_on_rv,
    triu_to_positive_tril,
)

try:
    # functools.cached_property is only available in Python >=3.8
    from functools import cached_property, lru_cache
except ImportError:
    from functools import lru_cache

    from cached_property import cached_property

try:
    # functools.cached_property is only available in Python >=3.8
    from functools import cached_property, lru_cache
except ImportError:
    from functools import lru_cache

    from cached_property import cached_property


class DiscreteGaussian(trans.Transition):
    """Discrete transitions with additive Gaussian noise.

    .. math:: x_{i+1} \\sim \\mathcal{N}(g(t_i, x_i), S(t_i))

    for some (potentially non-linear) dynamics :math:`g` and process noise covariance matrix :math:`S`.

    Parameters
    ----------
    state_trans_fun :
        State transition function :math:`g=g(t, x)`. Signature: ``state_trans_fun(t, x)``.
    proc_noise_cov_mat_fun :
        Process noise covariance matrix function :math:`S=S(t)`. Signature: ``proc_noise_cov_mat_fun(t)``.
    jacob_state_trans_fun :
        Jacobian of the state transition function :math:`g`, :math:`Jg=Jg(t, x)`.
        Signature: ``jacob_state_trans_fun(t, x)``.

    See Also
    --------
    :class:`DiscreteModel`
    :class:`DiscreteGaussianLinearModel`
    """

    def __init__(
        self,
        input_dim,
        output_dim,
        state_trans_fun: Callable[[FloatArgType, np.ndarray], np.ndarray],
        proc_noise_cov_mat_fun: Callable[[FloatArgType], np.ndarray],
        jacob_state_trans_fun: Optional[
            Callable[[FloatArgType, np.ndarray], np.ndarray]
        ] = None,
    ):
        self.state_trans_fun = state_trans_fun
        self.proc_noise_cov_mat_fun = proc_noise_cov_mat_fun

        def dummy_if_no_jacobian(t, x):
            raise NotImplementedError

        self.jacob_state_trans_fun = (
            jacob_state_trans_fun
            if jacob_state_trans_fun is not None
            else dummy_if_no_jacobian
        )
        super().__init__(input_dim=input_dim, output_dim=output_dim)

    def forward_realization(
        self, real, t, compute_gain=False, _diffusion=1.0, **kwargs
    ):

        newmean = self.state_trans_fun(t, real)
        newcov = _diffusion * self.proc_noise_cov_mat_fun(t)

        return pnrv.Normal(newmean, newcov), {}

    def forward_rv(self, rv, t, compute_gain=False, _diffusion=1.0, **kwargs):
        raise NotImplementedError("Not available")

    def backward_realization(
        self,
        real_obtained,
        rv,
        rv_forwarded=None,
        gain=None,
        t=None,
        _diffusion=1.0,
        **kwargs,
    ):
        raise NotImplementedError("Not available")

    def backward_rv(
        self,
        rv_obtained,
        rv,
        rv_forwarded=None,
        gain=None,
        t=None,
        _diffusion=1.0,
        **kwargs,
    ):

        # Should we use the _backward_rv_classic here?
        # It is only intractable bc. forward_rv is intractable
        # and assuming its forward formula would yield a valid
        # gain, the backward formula would be valid.
        # This is the case for the UKF, for instance.
        raise NotImplementedError("Not available")

    # Implementations that are the same for all sorts of
    # discrete Gaussian transitions, in particular shared
    # by LinearDiscreteGaussian and e.g. DiscreteUKFComponent.

    def _backward_rv_classic(
        self,
        rv_obtained,
        rv,
        rv_forwarded=None,
        gain=None,
        t=None,
        _diffusion=None,
        _linearise_at=None,
    ):

        if rv_forwarded is None or gain is None:
            rv_forwarded, info = self.forward_rv(
                rv,
                t=t,
                compute_gain=True,
                _diffusion=_diffusion,
                _linearise_at=_linearise_at,
            )
            gain = info["gain"]
        return condition_state_on_rv(rv_obtained, rv_forwarded, rv, gain), {}

    @lru_cache(maxsize=None)
    def proc_noise_cov_cholesky_fun(self, t):
        R = self.proc_noise_cov_mat_fun(t)
        if np.linalg.norm(R) < 1e-15:
            return 0 * R
        return np.linalg.cholesky(R)


class DiscreteLinearGaussian(DiscreteGaussian):
    """Discrete, linear Gaussian transition models of the form.

    .. math:: x_{i+1} \\sim \\mathcal{N}(G(t_i) x_i + v(t_i), S(t_i))

    for some dynamics matrix :math:`G=G(t)`, force vector :math:`v=v(t)`,
    and diffusion matrix :math:`S=S(t)`.


    Parameters
    ----------
    state_trans_mat_fun : callable
        State transition matrix function :math:`G=G(t)`. Signature: ``state_trans_mat_fun(t)``.
    shift_vec_fun : callable
        Shift vector function :math:`v=v(t)`. Signature: ``shift_vec_fun(t)``.
    proc_noise_cov_mat_fun : callable
        Process noise covariance matrix function :math:`S=S(t)`. Signature: ``proc_noise_cov_mat_fun(t)``.

    See Also
    --------
    :class:`DiscreteModel`
    :class:`DiscreteGaussianLinearModel`
    """

    def __init__(
        self,
        input_dim,
        output_dim,
        state_trans_mat_fun: Callable[[FloatArgType], np.ndarray],
        shift_vec_fun: Callable[[FloatArgType], np.ndarray],
        proc_noise_cov_mat_fun: Callable[[FloatArgType], np.ndarray],
        forward_implementation="classic",
        backward_implementation="classic",
    ):

        # Choose implementation for forward and backward transitions
        choose_forward_implementation = {
            "classic": self._forward_rv_classic,
            "sqrt": self._forward_rv_sqrt,
        }
        choose_backward_implementation = {
            "classic": self._backward_rv_classic,
            "sqrt": self._backward_rv_sqrt,
            "joseph": self._backward_rv_joseph,
        }
        self._forward_implementation = choose_forward_implementation[
            forward_implementation
        ]
        self._backward_implementation = choose_backward_implementation[
            backward_implementation
        ]

        self.state_trans_mat_fun = state_trans_mat_fun
        self.shift_vec_fun = shift_vec_fun
        super().__init__(
            input_dim=input_dim,
            output_dim=output_dim,
            state_trans_fun=lambda t, x: (
                self.state_trans_mat_fun(t) @ x + self.shift_vec_fun(t)
            ),
            proc_noise_cov_mat_fun=proc_noise_cov_mat_fun,
            jacob_state_trans_fun=lambda t, x: state_trans_mat_fun(t),
        )

    def forward_rv(self, rv, t, compute_gain=False, _diffusion=1.0, **kwargs):

        return self._forward_implementation(
            rv=rv,
            t=t,
            compute_gain=compute_gain,
            _diffusion=_diffusion,
        )

    def forward_realization(self, real, t, _diffusion=1.0, **kwargs):

        return self._forward_realization_via_forward_rv(
            real, t=t, compute_gain=False, _diffusion=_diffusion
        )

    def backward_rv(
        self,
        rv_obtained,
        rv,
        rv_forwarded=None,
        gain=None,
        t=None,
        _diffusion=1.0,
        **kwargs,
    ):
        return self._backward_implementation(
            rv_obtained=rv_obtained,
            rv=rv,
            rv_forwarded=rv_forwarded,
            gain=gain,
            t=t,
            _diffusion=_diffusion,
        )

    def backward_realization(
        self,
        real_obtained,
        rv,
        rv_forwarded=None,
        gain=None,
        t=None,
        _diffusion=1.0,
        **kwargs,
    ):
        return self._backward_realization_via_backward_rv(
            real_obtained,
            rv,
            rv_forwarded=rv_forwarded,
            gain=gain,
            t=t,
            _diffusion=_diffusion,
        )

    # Forward and backward implementations
    # _backward_rv_classic is inherited from DiscreteGaussian

    def _forward_rv_classic(
        self, rv, t, compute_gain=False, _diffusion=1.0
    ) -> (pnrv.RandomVariable, typing.Dict):
        H = self.state_trans_mat_fun(t)
        R = self.proc_noise_cov_mat_fun(t)
        shift = self.shift_vec_fun(t)

        new_mean = H @ rv.mean + shift
        crosscov = rv.cov @ H.T
        new_cov = H @ crosscov + _diffusion * R
        info = {"crosscov": crosscov}
        if compute_gain:
            gain = crosscov @ np.linalg.inv(new_cov)
            info["gain"] = gain
        return pnrv.Normal(new_mean, cov=new_cov), info

    def _forward_rv_sqrt(
        self, rv, t, compute_gain=False, _diffusion=1.0
    ) -> (pnrv.RandomVariable, typing.Dict):

        H = self.state_trans_mat_fun(t)
        SR = self.proc_noise_cov_cholesky_fun(t)
        shift = self.shift_vec_fun(t)

        new_mean = H @ rv.mean + shift
        new_cov_cholesky = cholesky_update(
            H @ rv.cov_cholesky, np.sqrt(_diffusion) * SR
        )
        new_cov = new_cov_cholesky @ new_cov_cholesky.T
        crosscov = rv.cov @ H.T
        info = {"crosscov": crosscov}
        if compute_gain:
            gain = crosscov @ np.linalg.inv(new_cov)
            info["gain"] = gain
        return pnrv.Normal(new_mean, cov=new_cov, cov_cholesky=new_cov_cholesky), info

    def _backward_rv_sqrt(
        self,
        rv_obtained,
        rv,
        rv_forwarded=None,
        gain=None,
        t=None,
        _diffusion=1.0,
    ):
        # forwarded_rv is ignored in square-root smoothing.

        # Smoothing updates need the gain, but
        # filtering updates "compute their own".
        # Thus, if we are doing smoothing (|cov_obtained|>0) an the gain is not provided,
        # make an extra prediction to compute the gain.
        if gain is None:
            if np.linalg.norm(rv_obtained.cov) > 0:
                _, info = self.forward_rv(
                    rv, t=t, compute_gain=True, _diffusion=_diffusion
                )
                gain = info["gain"]
            else:
                gain = np.zeros((len(rv.mean), len(rv_obtained.mean)))

        H = self.state_trans_mat_fun(t)
        SR = np.sqrt(_diffusion) * self.proc_noise_cov_cholesky_fun(t)
        shift = self.shift_vec_fun(t)

        SC_past = rv.cov_cholesky
        SC_attained = rv_obtained.cov_cholesky

        dim = len(H)  # 2
        dim2 = len(H.T)  # 8
        zeros = np.zeros((dim, dim))
        zeros2 = np.zeros((dim, dim2))

        blockmat = np.block(
            [
                [SC_past.T @ H.T, SC_past.T],
                [SR.T, zeros2],
                [zeros, SC_attained.T @ gain.T],
            ]
        )
        big_triu = np.linalg.qr(blockmat, mode="r")
        SC = big_triu[dim : (dim + dim2), dim : (dim + dim2)]

        if gain is None:
            gain = big_triu[:dim, dim:].T @ np.linalg.inv(big_triu[:dim, :dim].T)

        new_mean = rv.mean + gain @ (rv_obtained.mean - H @ rv.mean - shift)
        new_cov_cholesky = triu_to_positive_tril(SC)
        new_cov = new_cov_cholesky @ new_cov_cholesky.T
        return pnrv.Normal(new_mean, new_cov, cov_cholesky=new_cov_cholesky), {}

    def _backward_rv_joseph(
        self,
        rv_obtained,
        rv,
        rv_forwarded=None,
        gain=None,
        t=None,
        _diffusion=None,
    ):
        # forwarded_rv is ignored in Joseph updates.

        if gain is None:
            _, info = self.forward_rv(rv, t=t, compute_gain=True, _diffusion=_diffusion)
            gain = info["gain"]

        H = self.state_trans_mat_fun(t)
        R = _diffusion * self.proc_noise_cov_mat_fun(t)
        shift = self.shift_vec_fun(t)

        new_mean = rv.mean + gain @ (rv_obtained.mean - H @ rv.mean - shift)
        joseph_factor = np.eye(len(rv.mean)) - gain @ H
        new_cov = (
            joseph_factor @ rv.cov @ joseph_factor.T
            + gain @ R @ gain.T
            + gain @ rv_obtained.cov @ gain.T
        )
        return pnrv.Normal(new_mean, new_cov), {}


class DiscreteLTIGaussian(DiscreteLinearGaussian):
    """Discrete, linear, time-invariant Gaussian transition models of the form.

    .. math:: x_{i+1} \\sim \\mathcal{N}(G x_i + v, S)

    for some dynamics matrix :math:`G`, force vector :math:`v`,
    and diffusion matrix :math:`S`.

    Parameters
    ----------
    state_trans_mat :
        State transition matrix :math:`G`.
    shift_vec :
        Shift vector :math:`v`.
    proc_noise_cov_mat :
        Process noise covariance matrix :math:`S`.

    Raises
    ------
    TypeError
        If state_trans_mat, shift_vec and proc_noise_cov_mat have incompatible shapes.

    See Also
    --------
    :class:`DiscreteModel`
    :class:`DiscreteGaussianLinearModel`
    """

    def __init__(
        self,
        state_trans_mat: np.ndarray,
        shift_vec: np.ndarray,
        proc_noise_cov_mat: np.ndarray,
        forward_implementation="classic",
        backward_implementation="classic",
    ):
        _check_dimensions(state_trans_mat, shift_vec, proc_noise_cov_mat)
        output_dim, input_dim = state_trans_mat.shape

        super().__init__(
            input_dim,
            output_dim,
            lambda t: state_trans_mat,
            lambda t: shift_vec,
            lambda t: proc_noise_cov_mat,
            forward_implementation=forward_implementation,
            backward_implementation=backward_implementation,
        )

        self.state_trans_mat = state_trans_mat
        self.shift_vec = shift_vec
        self.proc_noise_cov_mat = proc_noise_cov_mat

    def proc_noise_cov_cholesky_fun(self, t):
        return self.proc_noise_cov_cholesky

    @cached_property
    def proc_noise_cov_cholesky(self):

        # Catch for zero matrix
        if np.linalg.norm(self.proc_noise_cov_mat) < 1e-15:
            return 0.0 * self.proc_noise_cov_mat
        return np.linalg.cholesky(self.proc_noise_cov_mat)


def _check_dimensions(state_trans_mat, shift_vec, proc_noise_cov_mat):
    """LTI SDE model needs matrices which are compatible with each other in size."""
    if state_trans_mat.ndim != 2:
        raise TypeError(
            f"dynamat.ndim=2 expected. dynamat.ndim={state_trans_mat.ndim} received."
        )
    if shift_vec.ndim != 1:
        raise TypeError(
            f"shift_vec.ndim=1 expected. shift_vec.ndim={shift_vec.ndim} received."
        )
    if proc_noise_cov_mat.ndim != 2:
        raise TypeError(
            f"proc_noise_cov_mat.ndim=2 expected. proc_noise_cov_mat.ndim={proc_noise_cov_mat.ndim} received."
        )
    if (
        state_trans_mat.shape[0] != shift_vec.shape[0]
        or shift_vec.shape[0] != proc_noise_cov_mat.shape[0]
        or proc_noise_cov_mat.shape[0] != proc_noise_cov_mat.shape[1]
    ):
        raise TypeError(
            f"Dimension of dynamat, forcevec and diffmat do not align. "
            f"Expected: dynamat.shape=(N,*), forcevec.shape=(N,), diffmat.shape=(N, N).     "
            f"Received: dynamat.shape={state_trans_mat.shape}, forcevec.shape={shift_vec.shape}, "
            f"proc_noise_cov_mat.shape={proc_noise_cov_mat.shape}."
        )
