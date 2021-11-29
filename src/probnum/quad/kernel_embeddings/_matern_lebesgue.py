"""Kernel embedding of Matern kernels with Lebesgue integration measure."""

# pylint: disable=invalid-name

from typing import Tuple, Union

import numpy as np

from probnum.quad._integration_measures import LebesgueMeasure
from probnum.randprocs.kernels import Matern, ProductMatern


def _kernel_mean_matern_lebesgue(
    x: np.ndarray, kernel: Union[Matern, ProductMatern], measure: LebesgueMeasure
) -> np.ndarray:
    """Kernel mean of a ProductMatern or 1D Matern kernel w.r.t. its first argument
    against a Lebesgue measure.

    Parameters
    ----------
    x :
        *shape (n_eval, input_dim)* -- n_eval locations where to evaluate the kernel mean.
    kernel :
        Instance of a ProductMatern or 1D Matern kernel.
    measure :
        Instance of a LebesgueMeasure.

    Returns
    -------
    k_mean :
        *shape=(n_eval,)* -- The kernel integrated w.r.t. its first argument,
                            evaluated at locations x.
    """
    kernel = _convert_to_product_matern(kernel)

    # Compute kernel mean via a product of one-dimensional kernel means
    kernel_mean = np.ones((x.shape[0],))
    for dim in range(kernel.input_dim):
        kernel_mean *= _kernel_mean_matern_1d_lebesgue(
            x=x[:, dim],
            kernel=kernel.one_d_materns[dim],
            domain=(measure.domain[0][dim], measure.domain[1][dim]),
        )

    return measure.normalization_constant * kernel_mean


def _kernel_variance_matern_lebesgue(
    kernel: Union[Matern, ProductMatern], measure: LebesgueMeasure
) -> float:
    """Kernel variance of a ProductMatern or 1D Matern kernel w.r.t. both arguments
    against a Lebesgue measure.

    Parameters
    ----------
    kernel :
        Instance of a ProductMatern or 1D Matern kernel.
    measure :
        Instance of a LebesgueMeasure.

    Returns
    -------
    k_var :
        The kernel integrated w.r.t. both arguments.
    """

    kernel = _convert_to_product_matern(kernel)

    # Compute kernel mean via a product of one-dimensional kernel variances
    kernel_variance = 1.0
    for dim in range(kernel.input_dim):
        kernel_variance *= _kernel_variance_matern_1d_lebesgue(
            kernel=kernel.one_d_materns[dim],
            domain=(measure.domain[0][dim], measure.domain[1][dim]),
        )

    return measure.normalization_constant ** 2 * kernel_variance


def _convert_to_product_matern(kernel):
    """Convert a 1D Matern kernel to a ProductMatern for unified treatment."""
    if isinstance(kernel, Matern):
        if kernel.input_dim > 1:
            raise NotImplementedError(
                "Kernel embeddings have been implemented only for "
                "Matérn kernels in dimension one and product Matern kernels."
            )
        kernel = ProductMatern(
            input_dim=kernel.input_dim,
            lengthscales=kernel.lengthscale,
            nus=kernel.nu,
        )
    return kernel


def _kernel_mean_matern_1d_lebesgue(x: np.ndarray, kernel: Matern, domain: Tuple):
    """Kernel means for 1D Matern kernels.

    Note that these are for unnormalized Lebesgue measure.
    """
    # pylint: disable="invalid-name"
    (a, b) = domain
    ell = kernel.lengthscale
    if kernel.nu == 0.5:
        unnormalized_mean = ell * (2.0 - np.exp((a - x) / ell) - np.exp((x - b) / ell))
    elif kernel.nu == 1.5:
        unnormalized_mean = (
            4.0 * ell / np.sqrt(3.0)
            - np.exp(np.sqrt(3.0) * (x - b) / ell)
            / 3.0
            * (3.0 * b + 2.0 * np.sqrt(3.0) * ell - 3.0 * x)
            - np.exp(np.sqrt(3.0) * (a - x) / ell)
            / 3.0
            * (3.0 * x + 2.0 * np.sqrt(3.0) * ell - 3.0 * a)
        )
    elif kernel.nu == 2.5:
        unnormalized_mean = (
            16.0 * ell / (3.0 * np.sqrt(5.0))
            - np.exp(np.sqrt(5.0) * (x - b) / ell)
            / (15.0 * ell)
            * (
                8.0 * np.sqrt(5.0) * ell ** 2
                + 25.0 * ell * (b - x)
                + 5.0 * np.sqrt(5.0) * (b - x) ** 2
            )
            - np.exp(np.sqrt(5.0) * (a - x) / ell)
            / (15.0 * ell)
            * (
                8.0 * np.sqrt(5.0) * ell ** 2
                + 25.0 * ell * (x - a)
                + 5.0 * np.sqrt(5.0) * (a - x) ** 2
            )
        )
    elif kernel.nu == 3.5:
        unnormalized_mean = (
            1.0
            / (105.0 * ell ** 2)
            * (
                96.0 * np.sqrt(7.0) * ell ** 3
                - np.exp(np.sqrt(7.0) * (x - b) / ell)
                * (
                    48.0 * np.sqrt(7.0) * ell ** 3
                    - 231.0 * ell ** 2 * (x - b)
                    + 63.0 * np.sqrt(7.0) * ell * (x - b) ** 2
                    - 49.0 * (x - b) ** 3
                )
                - np.exp(np.sqrt(7.0) * (a - x) / ell)
                * (
                    48.0 * np.sqrt(7.0) * ell ** 3
                    + 231.0 * ell ** 2 * (x - a)
                    + 63.0 * np.sqrt(7.0) * ell * (x - a) ** 2
                    + 49.0 * (x - a) ** 3
                )
            )
        )
    else:
        raise NotImplementedError
    return unnormalized_mean


def _kernel_variance_matern_1d_lebesgue(kernel: Matern, domain: Tuple):
    """Kernel variances for 1D Matern kernels.

    Note that these are for unnormalized Lebesgue measure.
    """
    # pylint: disable="invalid-name"
    (a, b) = domain
    r = b - a
    ell = kernel.lengthscale
    if kernel.nu == 0.5:
        unnormalized_variance = 2.0 * ell * (r + ell * (np.exp(-r / ell) - 1.0))
    elif kernel.nu == 1.5:
        c = np.sqrt(3.0) * r
        unnormalized_variance = (
            2.0 * ell / 3.0 * (2.0 * c - 3.0 * ell + np.exp(-c / ell) * (c + 3.0 * ell))
        )
    elif kernel.nu == 2.5:
        c = np.sqrt(5.0) * r
        unnormalized_variance = (
            1.0
            / 15.0
            * (
                2.0 * ell * (8.0 * c - 15.0 * ell)
                + 2.0
                * np.exp(-c / ell)
                * (
                    5.0 * a ** 2
                    - 10.0 * a * b
                    + 5.0 * b ** 2
                    + 7.0 * c * ell
                    + 15.0 * ell ** 2
                )
            )
        )
    elif kernel.nu == 3.5:
        c = np.sqrt(7.0) * r
        unnormalized_variance = (
            1.0
            / (105.0 * ell)
            * (
                2.0
                * np.exp(-c / ell)
                * (
                    7.0 * np.sqrt(7.0) * (b ** 3 - a ** 3)
                    + 84.0 * b ** 2 * ell
                    + 57.0 * np.sqrt(7.0) * b * ell ** 2
                    + 105.0 * ell ** 3
                    + 21.0 * a ** 2 * (np.sqrt(7.0) * b + 4.0 * ell)
                    - 3.0
                    * a
                    * (
                        7.0 * np.sqrt(7.0) * b ** 2
                        + 56.0 * b * ell
                        + 19.0 * np.sqrt(7.0) * ell ** 2
                    )
                )
                - 6.0 * ell ** 2 * (35.0 * ell - 16.0 * c)
            )
        )
    else:
        raise NotImplementedError
    return unnormalized_variance
