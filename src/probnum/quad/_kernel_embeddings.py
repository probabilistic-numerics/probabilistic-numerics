"""Contains the kernel embeddings, i.e., integrals over kernels."""

import abc

import numpy as np
import scipy.linalg as slinalg
import scipy.special

from ..kernels import ExpQuad, Kernel
from ._integration_measures import GaussianMeasure, IntegrationMeasure, LebesgueMeasure


class _KernelEmbedding(abc.ABC):
    """Abstract class for integrals over kernels.

    Child classes implement integrals for a given combination of kernel and measure.
    The naming scheme for child classes is 'K + kernel + M + measure'

    Parameters
    ----------
    kernel:
        Instance of a kernel
    measure:
        Instance of an integration measure
    """

    def __init__(self, kernel: Kernel, measure: IntegrationMeasure) -> None:
        self.kernel = kernel
        self.measure = measure

        if self.kernel.input_dim != self.measure.dim:
            raise ValueError(
                "Input dimensions of kernel and measure need to be the same."
            )

        self.dim = self.kernel.input_dim

    def kernel_mean(self, x: np.ndarray) -> np.ndarray:
        """Kernel mean w.r.t. its first argument against the integration measure.

        Parameters
        ----------
        x:
            n_eval locations where to evaluate the kernel mean, shape (n_eval, dim)

        Returns
        -------
        k_mean:
            The kernel integrated w.r.t. its first argument, evaluated at locations x, shape (n_eval,)
        """
        raise NotImplementedError

    def kernel_variance(self) -> float:
        """Kernel integrated in both arguments against the integration measure.

        Returns
        -------
        k_var:
            The kernel integrated w.r.t. both arguments
        """
        raise NotImplementedError


class _KExpQuadMGauss(_KernelEmbedding):
    """Kernel embedding of exponentiated quadratic kernel with Gaussian integration
    measure.

    TODO: adopt the convention that arrays have shape (n_eval, dim)

    Parameters
    ----------
    kernel:
        Instance of an exponentiated quadratic kernel
    measure:
        Instance of a Gaussian integration measure
    """

    def __init__(self, kernel: ExpQuad, measure: GaussianMeasure) -> None:
        super().__init__(kernel, measure)

    def kernel_mean(self, x: np.ndarray) -> np.ndarray:

        if self.measure.diagonal_covariance:
            cov_diag = np.diag(np.atleast_2d(self.measure.cov))
            chol_inv_x = (x - self.measure.mean) / np.sqrt(
                self.kernel.lengthscale ** 2 + cov_diag
            )
            det_factor = self.kernel.lengthscale ** self.dim / np.sqrt(
                (self.kernel.lengthscale ** 2 + cov_diag).prod()
            )
        else:
            chol = slinalg.cho_factor(
                self.kernel.lengthscale ** 2 * np.eye(self.dim) + self.measure.cov,
                lower=True,
            )
            chol_inv_x = slinalg.cho_solve(chol, (x - self.measure.mean).T).T
            det_factor = self.kernel.lengthscale ** self.dim / np.diag(chol[0]).prod()

        exp_factor = np.exp(-0.5 * (np.atleast_2d(chol_inv_x) ** 2).sum(axis=1))
        return det_factor * exp_factor

    def kernel_variance(self) -> float:

        if self.measure.diagonal_covariance:
            denom = np.sqrt(
                (
                    self.kernel.lengthscale ** 2
                    + 2.0 * np.diag(np.atleast_2d(self.measure.cov))
                ).prod()
            )
        else:
            chol, _ = slinalg.cho_factor(
                self.kernel.lengthscale * np.eye(self.dim) + 2 * self.measure.cov,
                lower=True,
            )
            denom = np.diag(chol).prod()

        return self.kernel.lengthscale ** self.dim / denom


class _KExpQuadMLebesgue(_KernelEmbedding):
    """Kernel embedding of exponentiated quadratic kernel with Lebesgue integration
    measure.

    Parameters
    ----------
    kernel:
        Instance of an exponentiated quadratic kernel
    measure:
        Instance of a Lebesgue integration measure
    """

    def __init__(self, kernel: ExpQuad, measure: LebesgueMeasure) -> None:
        super().__init__(kernel, measure)

    def kernel_mean(self, x: np.ndarray) -> np.ndarray:
        a = self.measure.domain[0]
        b = self.measure.domain[1]
        ell = self.kernel.lengthscale
        return (
            self.measure.normalization_constant
            * (np.pi * ell ** 2 / 2) ** (self.dim / 2)
            * np.atleast_2d(
                scipy.special.erf((b - x) / (ell * np.sqrt(2)))
                - scipy.special.erf((a - x) / (ell * np.sqrt(2)))
            ).prod(axis=1)
        )

    def kernel_variance(self) -> float:
        r = self.measure.domain[1] - self.measure.domain[0]
        ell = self.kernel.lengthscale
        return (
            self.measure.normalization_constant ** 2
            * (2 * np.pi * ell ** 2) ** (self.dim / 2)
            * np.atleast_2d(
                ell * np.sqrt(2 / np.pi) * (np.exp(-(r ** 2) / (2 * ell ** 2)) - 1)
                + r * scipy.special.erf(r / (ell * np.sqrt(2)))
            ).prod()
        )


def get_kernel_embedding(
    kernel: Kernel, measure: IntegrationMeasure
) -> _KernelEmbedding:
    """Select the right kernel embedding given the kernel and integration measure.

    Parameters
    ----------
    kernel:
        Instance of a kernel
    measure:
        Instance of an integration measure

    Returns
    -------
    an instance of _KernelEmbedding
    """

    # Exponentiated quadratic kernel
    if isinstance(kernel, ExpQuad):
        if isinstance(measure, GaussianMeasure):
            return _KExpQuadMGauss(kernel, measure)
        elif isinstance(measure, LebesgueMeasure):
            return _KExpQuadMLebesgue(kernel, measure)
        raise NotImplementedError

    # other kernels
    raise NotImplementedError
