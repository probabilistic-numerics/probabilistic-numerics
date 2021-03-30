"""Bayesian Quadrature.

This module provides routines to integrate functions through Bayesian
quadrature, meaning a model over the integrand is constructed in order
to actively select evaluation points of the integrand to estimate the
value of the integral. Bayesian quadrature methods return a random
variable, specifying the belief about the true value of the integral.
"""

from typing import Callable, Dict, Optional, Tuple, Union

import numpy as np

from probnum.kernels import Kernel
from probnum.randvars import Normal
from probnum.type import FloatArgType

from ._integration_measures import IntegrationMeasure, LebesgueMeasure
from .bq_methods import BayesianQuadrature


def bayesquad(
    fun: Callable,
    input_dim: int,
    kernel: Optional[Kernel] = None,
    domain: Optional[
        Tuple[Union[np.ndarray, FloatArgType], Union[np.ndarray, FloatArgType]]
    ] = None,
    nevals: int = None,
    measure: Optional[IntegrationMeasure] = None,
    method: str = "vanilla",
    policy: str = "bmc",
) -> Tuple[Normal, Dict]:
    r"""Infer the solution of the uni- or multivariate integral :math:`\int_a^b f(x) d \mu(x)`.

    Bayesian quadrature (BQ) infers integrals of the form

    .. math:: F = \int_a^b f(x) d \mu(x),

    of a function :math:`f:\mathbb{R}^D \mapsto \mathbb{R}` integrated between bounds
    :math:`a` and :math:`b` against a measure :math:`\mu: \mathbb{R}^D \mapsto \mathbb{R}`.

    Bayesian quadrature methods return a probability distribution over the solution :math:`F` with
    uncertainty arising from finite computation (here a finite number of function evaluations).
    They start out with a random process encoding the prior belief about the function :math:`f`
    to be integrated. Conditioned on either existing or acquired function evaluations according to a
    policy, they update the belief on :math:`f`, which is translated into a posterior measure over
    the integral :math:`F`.

    Parameters
    ----------
    fun :
        Function to be integrated.
    input_dim:
        Input dimension of the integration problem
    kernel:
        the kernel used for the GP model
    domain :
        Domain of integration. Contains lower and upper bound as int or ndarray, shape=(dim,)
    measure:
        Integration measure, defaults to the Lebesgue measure.
    nevals :
        Number of function evaluations.
    method :
        Type of Bayesian quadrature to use. The available options are

        ====================  ===========
         vanilla              ``vanilla``
         WSABI                ``wsabi``
        ====================  ===========

    policy :
        Type of acquisition strategy to use. Options are

        =======================  =======
         Bayesian Monte Carlo    ``bmc``
         Uncertainty Sampling    ``us``
         Mutual Information      ``mi``
         Integral Variance       ``iv``
        =======================  =======

    Returns
    -------
    integral :
        The integral of ``func`` on the domain.
    info :
        Information on the performance of the method.

    References
    ----------
    """
    if domain is None and measure is None:
        raise ValueError(
            "You need to either specify an integration domain or an integration measure. "
            "The Lebesgue measure can only operate on a finite domain."
        )

    # Integration measure
    if measure is None:
        measure = LebesgueMeasure(domain=domain, dim=input_dim)

    # Choose Method
    bq_method = BayesianQuadrature.from_interface(
        input_dim=input_dim, kernel=kernel, method=method, policy=policy
    )

    if nevals is None:
        nevals = input_dim * 25

    # Integrate
    integral, info = bq_method.integrate(fun=fun, measure=measure, nevals=nevals)

    return integral, info
