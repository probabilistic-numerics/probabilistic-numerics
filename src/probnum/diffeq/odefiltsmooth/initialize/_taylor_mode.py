"""Taylor-mode initialization."""
# pylint: disable=import-outside-toplevel


import numpy as np

from probnum import problems, randprocs, randvars, statespace

# In the initialisation-via-RK function below, this value is added to the marginal stds of the initial derivatives that are known.
# If we put in zero, there are linalg errors (because a zero-cov RV is conditioned on a dirac likelihood).
# This value is chosen such that its square-root is a really small damping factor).
SMALL_VALUE = 1e-28


from probnum.diffeq.odefiltsmooth.initialize import _initialize


class TaylorModeInitialization(_initialize.InitializationRoutine):
    """Initialize a probabilistic ODE solver with Taylor-mode automatic differentiation.

    This requires JAX. For an explanation of what happens ``under the hood``, see [1]_.

    References
    ----------
    .. [1] Krämer, N. and Hennig, P., Stable implementation of probabilistic ODE solvers,
       *arXiv:2012.10106*, 2020.


    The implementation is inspired by the implementation in
    https://github.com/jacobjinkelly/easy-neural-ode/blob/master/latent_ode.py



    Examples
    --------

    >>> import sys, pytest
    >>> if not sys.platform.startswith('linux'):
    ...     pytest.skip()

    >>> import numpy as np
    >>> from probnum.randvars import Normal
    >>> from probnum.problems.zoo.diffeq import threebody_jax, vanderpol_jax
    >>> from probnum.statespace import IBM
    >>> from probnum.randprocs import MarkovProcess

    Compute the initial values of the restricted three-body problem as follows

    >>> ivp = threebody_jax()
    >>> print(ivp.y0)
    [ 0.994       0.          0.         -2.00158511]

    Construct the prior process.

    >>> prior = IBM(ordint=3, spatialdim=4)
    >>> initrv = Normal(mean=np.zeros(prior.dimension), cov=np.eye(prior.dimension))
    >>> prior_process = MarkovProcess(transition=prior, initrv=initrv, initarg=ivp.t0)

    Initialize with Taylor-mode autodiff.

    >>> taylor_init = TaylorModeInitialization()
    >>> improved_initrv = taylor_init(ivp=ivp, prior_process=prior_process)

    Print the results.

    >>> print(prior_process.transition.proj2coord(0) @ improved_initrv.mean)
    [ 0.994       0.          0.         -2.00158511]
    >>> print(improved_initrv.mean)
    [ 9.94000000e-01  0.00000000e+00 -3.15543023e+02  0.00000000e+00
      0.00000000e+00 -2.00158511e+00  0.00000000e+00  9.99720945e+04
      0.00000000e+00 -3.15543023e+02  0.00000000e+00  6.39028111e+07
     -2.00158511e+00  0.00000000e+00  9.99720945e+04  0.00000000e+00]

    Compute the initial values of the van-der-Pol oscillator as follows.
    First, set up the IVP and prior process.

    >>> ivp = vanderpol_jax()
    >>> print(ivp.y0)
    [2. 0.]
    >>> prior = IBM(ordint=3, spatialdim=2)
    >>> initrv = Normal(mean=np.zeros(prior.dimension), cov=np.eye(prior.dimension))
    >>> prior_process = MarkovProcess(transition=prior, initrv=initrv, initarg=ivp.t0)

    >>> taylor_init = TaylorModeInitialization()
    >>> improved_initrv = taylor_init(ivp=ivp, prior_process=prior_process)

    Print the results.

    >>> print(prior_process.transition.proj2coord(0) @ improved_initrv.mean)
    [2. 0.]
    >>> print(improved_initrv.mean)
    [    2.     0.    -2.    60.     0.    -2.    60. -1798.]
    >>> print(improved_initrv.std)
    [0. 0. 0. 0. 0. 0. 0. 0.]
    """

    def __call__(
        self, ivp: problems.InitialValueProblem, prior_process: randprocs.MarkovProcess
    ) -> randvars.RandomVariable:

        f, y0, t0, tmax = ivp.f, ivp.y0, ivp.t0, ivp.tmax

        try:
            import jax.numpy as jnp
            from jax.config import config
            from jax.experimental.jet import jet

            config.update("jax_enable_x64", True)
        except ImportError as err:
            raise ImportError(
                "Cannot perform Taylor-mode initialisation without optional "
                "dependencies jax and jaxlib. Try installing them via `pip install jax jaxlib`."
            ) from err

        order = prior_process.transition.ordint

        def total_derivative(z_t):
            """Total derivative."""
            z, t = jnp.reshape(z_t[:-1], z_shape), z_t[-1]
            dz = jnp.ravel(f(t, z))
            dt = jnp.array([1.0])
            dz_t = jnp.concatenate((dz, dt))
            return dz_t

        z_shape = y0.shape
        z_t = jnp.concatenate((jnp.ravel(y0), jnp.array([t0])))

        derivs = []

        derivs.extend(y0)
        if order == 0:
            all_derivs = statespace.Integrator._convert_derivwise_to_coordwise(
                np.asarray(jnp.array(derivs)), ordint=0, spatialdim=len(y0)
            )

            return randvars.Normal(
                np.asarray(all_derivs),
                cov=np.asarray(jnp.diag(jnp.zeros(len(derivs)))),
                cov_cholesky=np.asarray(jnp.diag(jnp.zeros(len(derivs)))),
            )

        (dy0, [*yns]) = jet(total_derivative, (z_t,), ((jnp.ones_like(z_t),),))
        derivs.extend(dy0[:-1])
        if order == 1:
            all_derivs = statespace.Integrator._convert_derivwise_to_coordwise(
                np.asarray(jnp.array(derivs)), ordint=1, spatialdim=len(y0)
            )

            return randvars.Normal(
                np.asarray(all_derivs),
                cov=np.asarray(jnp.diag(jnp.zeros(len(derivs)))),
                cov_cholesky=np.asarray(jnp.diag(jnp.zeros(len(derivs)))),
            )

        for _ in range(1, order):
            (dy0, [*yns]) = jet(total_derivative, (z_t,), ((dy0, *yns),))
            derivs.extend(yns[-2][:-1])

        all_derivs = statespace.Integrator._convert_derivwise_to_coordwise(
            jnp.array(derivs), ordint=order, spatialdim=len(y0)
        )

        return randvars.Normal(
            np.asarray(all_derivs),
            cov=np.asarray(jnp.diag(jnp.zeros(len(derivs)))),
            cov_cholesky=np.asarray(jnp.diag(jnp.zeros(len(derivs)))),
        )


#
#
# def initialize_odefilter_with_taylormode(f, y0, t0, prior_process):
#     """
#     Parameters
#     ----------
#     f
#         ODE vector field.
#     y0
#         Initial value.
#     t0
#         Initial time point.
#     prior_process
#         Prior Gauss-Markov process used for the ODE solver. For instance an integrated Brownian motion prior (``IBM``).
#
#     Returns
#     -------
#     Normal
#         Estimated initial random variable. Compatible with the specified prior.
#     """
#     taylor_init = TaylorModeInitialization()
#     ivp = problems.InitialValueProblem(f=f, y0=y0, t0=t0, tmax=np.inf)
#     return taylor_init(ivp, prior_process=prior_process)
