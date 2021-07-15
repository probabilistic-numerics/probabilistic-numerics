"""Interface for information operators."""

import abc

from probnum import filtsmooth, problems, statespace


class InformationOperator(abc.ABC):
    r"""ODE information operators used in probabilistic ODE solvers.

    ODE information operators gather information about whether a state or function solves an ODE.
    More specifically, an information operator maps a sample from the prior distribution
    **that is also an ODE solution** to the zero function.

    Consider the following example. For an ODE

    .. math:: \dot y(t) - f(t, y(t)) = 0,

    and a :math:`\nu` times integrated Wiener process prior,
    the information operator maps

    .. math:: \mathcal{Z}: [t, (Y_0, Y_1, ..., Y_\nu)] \mapsto Y_1(t) - f(t, Y_0(t)).

    (Recall that :math:`Y_j` models the `j` th derivative of `Y_0` for given prior.)
    If :math:`Y_0` solves the ODE, :math:`\mathcal{Z}(Y)(t)` is zero for all :math:`t`.

    Information operators are used to condition prior distributions on solving a numerical problem.
    This happens by conditioning the prior distribution :math:`Y` on :math:`\mathcal{Z}(Y)(t_n)=0`
    on time-points :math:`t_1, ..., t_n, ..., t_N` (:math:`N` is usually large).
    Therefore, they are one important component in a probabilistic ODE solver.
    """

    def __init__(self, input_dim, output_dim):

        self.input_dim = input_dim
        self.output_dim = output_dim

        # Initialized once the IVP can be seen
        self.ivp = None

    def set_ivp(self, ivp):
        if self.ivp_has_been_set:
            raise ValueError
        else:
            self.ivp = ivp

    @property
    def ivp_has_been_set(self):
        return self.ivp is not None

    @abc.abstractmethod
    def __call__(self, t, x):
        raise NotImplementedError

    def jacobian(self, t, x):
        raise NotImplementedError

    def as_transition(self):
        return statespace.DiscreteGaussian.from_callable(
            state_trans_fun=self.__call__,
            jacob_state_trans_fun=self.jacobian,
            input_dim=self.input_dim,
            output_dim=self.output_dim,
        )

    def as_ekf_component(
        self, forward_implementation="sqrt", backward_implementation="sqrt"
    ):
        return filtsmooth.DiscreteEKFComponent(
            non_linear_model=self.as_transition(),
            forward_implementation=forward_implementation,
            backward_implementation=backward_implementation,
        )


class ODEResidualOperator(InformationOperator):
    def __init__(self, prior_ordint, prior_spatialdim):
        integrator_dimension = prior_spatialdim * (prior_ordint + 1)
        expected_ode_dimension = prior_spatialdim
        super().__init__(
            input_dim=integrator_dimension, output_dim=expected_ode_dimension
        )

        # Cache the projection matrices
        dummy_integrator = statespace.Integrator(
            ordint=prior_ordint, spatialdim=prior_spatialdim
        )
        self.h0 = dummy_integrator.proj2coord(coord=0)
        self.h1 = dummy_integrator.proj2coord(coord=1)
        self.prior_ordint = prior_ordint
        self.prior_spatialdim = prior_spatialdim

    def __call__(self, t, x):
        return self.h1 @ x - self.ivp.f(t, self.h0 @ x)

    def jacobian(self, t, x):
        return self.h1 - self.ivp.df(t, self.h0 @ x) @ self.h0
