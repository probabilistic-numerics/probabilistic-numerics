"""Tests for IntegratedOrnsteinUhlenbeckProcessTransitions."""


import numpy as np
import pytest

from probnum import randprocs, randvars
from tests.test_randprocs.test_markov.test_continuous import test_lti_sde
from tests.test_randprocs.test_markov.test_integrator import integrator_test_mixin


@pytest.mark.parametrize("driftspeed", [-2.0, 0.0, 2.0])
@pytest.mark.parametrize("initarg", [0.0, 2.0])
@pytest.mark.parametrize("num_derivatives", [0, 1, 4])
@pytest.mark.parametrize("wiener_process_dimension", [1, 2, 3])
@pytest.mark.parametrize("use_initrv", [True, False])
@pytest.mark.parametrize("diffuse", [True, False])
def test_ioup_construction(
    driftspeed, initarg, num_derivatives, wiener_process_dimension, use_initrv, diffuse
):
    if use_initrv:
        d = (num_derivatives + 1) * wiener_process_dimension
        initrv = randvars.Normal(np.arange(d), np.diag(np.arange(1, d + 1)))
    else:
        initrv = None
    if use_initrv and diffuse:
        with pytest.warns(Warning):
            randprocs.markov.integrator.IntegratedOrnsteinUhlenbeckProcess(
                driftspeed=driftspeed,
                initarg=initarg,
                num_derivatives=num_derivatives,
                wiener_process_dimension=wiener_process_dimension,
                initrv=initrv,
                diffuse=diffuse,
            )

    else:
        ioup = randprocs.markov.integrator.IntegratedOrnsteinUhlenbeckProcess(
            driftspeed=driftspeed,
            initarg=initarg,
            num_derivatives=num_derivatives,
            wiener_process_dimension=wiener_process_dimension,
            initrv=initrv,
            diffuse=diffuse,
        )

        isinstance(
            ioup,
            randprocs.markov.integrator.IntegratedOrnsteinUhlenbeckProcess,
        )
        isinstance(ioup, randprocs.markov.MarkovProcess)
        isinstance(
            ioup.transition,
            randprocs.markov.integrator.IntegratedOrnsteinUhlenbeckTransition,
        )


class TestIntegratedOrnsteinUhlenbeckProcessTransition(
    test_lti_sde.TestLTISDE, integrator_test_mixin.IntegratorMixInTestMixIn
):

    # Replacement for an __init__ in the pytest language. See:
    # https://stackoverflow.com/questions/21430900/py-test-skips-test-class-if-constructor-is-defined
    @pytest.fixture(autouse=True)
    def _setup(
        self,
        some_num_derivatives,
        forw_impl_string_linear_gauss,
        backw_impl_string_linear_gauss,
    ):
        self.some_num_derivatives = some_num_derivatives
        wiener_process_dimension = 1  # make tests compatible with some_normal_rv1, etc.
        self.transition = (
            randprocs.markov.integrator.IntegratedOrnsteinUhlenbeckTransition(
                num_derivatives=self.some_num_derivatives,
                wiener_process_dimension=wiener_process_dimension,
                driftspeed=1.2345,
                forward_implementation=forw_impl_string_linear_gauss,
                backward_implementation=backw_impl_string_linear_gauss,
            )
        )

        self.G = lambda t: self.transition.drift_matrix
        self.v = lambda t: self.transition.force_vector
        self.L = lambda t: self.transition.dispersion_matrix

        self.G_const = self.transition.drift_matrix
        self.v_const = self.transition.force_vector
        self.L_const = self.transition.dispersion_matrix

        self.g = lambda t, x: self.G(t) @ x + self.v(t)
        self.dg = lambda t, x: self.G(t)
        self.l = lambda t, x: self.L(t)

    @property
    def integrator(self):
        return self.transition

    def test_wiener_process_dimension(self, test_ndim):
        assert self.transition.wiener_process_dimension == 1

    def test_state_ordering_default(self):
        assert self.transition.state_ordering == "coordinate"


def test_ioup_transition_drift_matrix_values():
    F = randprocs.markov.integrator.IntegratedOrnsteinUhlenbeckTransition._ioup_drift_matrix(
        driftspeed=0.1,
        num_derivatives=2,
        wiener_process_dimension=1,
    )
    expected = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, -0.1]])
    np.testing.assert_allclose(F, expected)

    I = np.eye(3)
    F = randprocs.markov.integrator.IntegratedOrnsteinUhlenbeckTransition._ioup_drift_matrix(
        driftspeed=0.1,
        num_derivatives=2,
        wiener_process_dimension=3,
    )
    expected = np.kron(I, expected)
    np.testing.assert_allclose(F, expected)


def test_ioup_transition_force_vector_values():
    u = randprocs.markov.integrator.IntegratedOrnsteinUhlenbeckTransition._ioup_force_vector(
        num_derivatives=2,
        wiener_process_dimension=1,
    )
    expected = np.array([0.0, 0.0, 0.0])
    np.testing.assert_allclose(u, expected)

    I = np.ones(3)
    u = randprocs.markov.integrator.IntegratedOrnsteinUhlenbeckTransition._ioup_force_vector(
        num_derivatives=2,
        wiener_process_dimension=3,
    )
    expected = np.kron(I, expected)
    np.testing.assert_allclose(u, expected)


def test_ioup_transition_dispersion_matrix_values():
    L = randprocs.markov.integrator.IntegratedOrnsteinUhlenbeckTransition._ioup_dispersion_matrix(
        num_derivatives=2,
        wiener_process_dimension=1,
    )
    expected = np.array(
        [
            [0.0],
            [0.0],
            [1.0],
        ]
    )
    np.testing.assert_allclose(L, expected)

    I = np.eye(3)
    L = randprocs.markov.integrator.IntegratedOrnsteinUhlenbeckTransition._ioup_dispersion_matrix(
        num_derivatives=2,
        wiener_process_dimension=3,
    )
    expected = np.kron(I, expected)
    np.testing.assert_allclose(L, expected)
