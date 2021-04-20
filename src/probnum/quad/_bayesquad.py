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
from probnum.type import FloatArgType, IntArgType

from ._integration_measures import IntegrationMeasure, LebesgueMeasure
from .bq_methods import BayesianQuadrature


# pylint: disable=too-many-arguments
# TODO: Do we really need input_dim as a separate argument? Both kernel and measure have
# TODO: either input_dim or dim that we could straightforwardly extract.
def bayesquad(
    fun: Callable,
    input_dim: int,
    kernel: Optional[Kernel] = None,
    domain: Optional[
        Tuple[Union[np.ndarray, FloatArgType], Union[np.ndarray, FloatArgType]]
    ] = None,
    measure: Optional[IntegrationMeasure] = None,
    policy: str = "bmc",
    max_nevals: Optional[IntArgType] = None,
    var_tol: Optional[
        FloatArgType
    ] = None,  # TODO: shall we set a default variance tolerance?
    rel_tol: Optional[FloatArgType] = None,
    batch_size: Optional[IntArgType] = 1,
) -> Tuple[Normal, Dict]:
    r"""Infer the solution of the uni- or multivariate integral :math:`\int_\Omega f(x) d \mu(x)`
    on a hyper-rectangle :math:`\Omega = [a_1, b_1] \times \cdots \times [a_D, b_D]`.

    Bayesian quadrature (BQ) infers integrals of the form

    .. math:: F = \int_\Omega f(x) d \mu(x),

    of a function :math:`f:\mathbb{R}^D \mapsto \mathbb{R}` integrated on the domain
    :math:`\Omega \subset \mathbb{R}^D` against a measure :math:`\mu: \mathbb{R}^D
    \mapsto \mathbb{R}`.

    Bayesian quadrature methods return a probability distribution over the solution :math:`F` with
    uncertainty arising from finite computation (here a finite number of function evaluations).
    They start out with a random process encoding the prior belief about the function :math:`f`
    to be integrated. Conditioned on either existing or acquired function evaluations according to a
    policy, they update the belief on :math:`f`, which is translated into a posterior measure over
    the integral :math:`F`.
    See Briol et al. [1]_ for a review on Bayesian quadrature.

    Parameters
    ----------
    fun :
        Function to be integrated.
    input_dim :
        Input dimension of the integration problem
    kernel :
        the kernel used for the GP model
    domain :
        *shape=(dim,)* -- Domain of integration. Contains lower and upper bound as int or ndarray.
    measure:
        Integration measure, defaults to the Lebesgue measure.
    policy :
        Type of acquisition strategy to use. Options are

        =======================  =======
         Bayesian Monte Carlo    ``bmc``
         Uncertainty Sampling    ``us``
         Mutual Information      ``mi``
         Integral Variance       ``iv``
        =======================  =======

    max_nevals :
        Maximum number of function evaluations.
    var_tol :
        Tolerance on the variance of the integral.
    rel_tol :
        Tolerance on consecutive updates of the integral mean.

    Returns
    -------
    integral :
        The integral of ``func`` on the domain.
    info :
        Information on the performance of the method.

    Raises
    ------
    ValueError
        If neither a domain nor a measure are given.

    References
    ----------
    .. [1] Briol, F.-X., et al., Probabilistic integration: A role in statistical computation?,
       *Statistical Science 34.1*, 2019, 1-22, 2019

    Examples
    --------
    >>> import numpy as np
    >>> np.random.seed(0)
    >>> input_dim = 1
    >>> domain = (0, 1)
    >>> def f(x):
    ...     return x
    >>> F, info = bayesquad(fun=f, input_dim=input_dim, domain=domain)
    >>> print(F.mean)
    0.5000
    """
    if domain is None and measure is None:
        raise ValueError(
            "You need to either specify an integration domain or an integration "
            "measure. The Lebesgue measure can only operate on a finite domain."
        )

    if measure is None:
        measure = LebesgueMeasure(domain=domain, dim=input_dim)

    bq_method = BayesianQuadrature.from_interface(
        input_dim=input_dim,
        kernel=kernel,
        measure=measure,
        policy=policy,
        max_nevals=max_nevals,
        var_tol=var_tol,
        rel_tol=rel_tol,
        batch_size=batch_size,
    )

    # Integrate
    integral_belief, bq_state = bq_method.integrate(fun=fun)

    return integral_belief, bq_state.info
