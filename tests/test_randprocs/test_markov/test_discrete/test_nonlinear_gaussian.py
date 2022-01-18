import numpy as np
import pytest

from probnum import randprocs, randvars
from tests.test_randprocs.test_markov import test_transition


class TestNonlinearGaussian(test_transition.InterfaceTestTransition):
    """Tests for the discrete Gaussian class.

    Most of the tests are reused/overwritten in subclasses, therefore the class-
    structure. Unfortunately, testing the product space of all combinations (different
    subclasses, different implementations, etc.) generates a lot of tests that are
    executed.
    """

    # Replacement for an __init__ in the pytest language. See:
    # https://stackoverflow.com/questions/21430900/py-test-skips-test-class-if-constructor-is-defined
    @pytest.fixture(autouse=True)
    def _setup(self, test_ndim, spdmat1):

        self.g = lambda t, x: np.sin(x)
        self.process_noise_fun = lambda t: randvars.Normal(
            mean=np.zeros(test_ndim), cov=spdmat1
        )
        self.dg = lambda t, x: np.cos(x)
        self.transition = randprocs.markov.discrete.NonlinearGaussian(
            input_dim=test_ndim,
            output_dim=test_ndim,
            state_trans_fun=self.g,
            process_noise_fun=self.process_noise_fun,
            jacob_state_trans_fun=self.dg,
        )

    # Test access to system matrices

    def test_state_transition(self, some_normal_rv1):
        received = self.transition.state_trans_fun(0.0, some_normal_rv1.mean)
        expected = self.g(0.0, some_normal_rv1.mean)
        np.testing.assert_allclose(received, expected)

    def test_process_noise_fun(self):
        received = self.transition.process_noise_fun(0.0)
        expected = self.process_noise_fun(0.0)
        np.testing.assert_allclose(received.mean, expected.mean)
        np.testing.assert_allclose(received.cov, expected.cov)

    def test_jacobian(self, some_normal_rv1):
        received = self.transition.jacob_state_trans_fun(0.0, some_normal_rv1.mean)
        expected = self.dg(0.0, some_normal_rv1.mean)
        np.testing.assert_allclose(received, expected)

    # Test forward and backward implementations

    def test_forward_rv(self, some_normal_rv1):
        with pytest.raises(NotImplementedError):
            self.transition.forward_rv(some_normal_rv1, 0.0)

    def test_forward_realization(self, some_normal_rv1):
        out, _ = self.transition.forward_realization(some_normal_rv1.mean, 0.0)
        assert isinstance(out, randvars.Normal)

    def test_backward_rv(self, some_normal_rv1, some_normal_rv2):
        with pytest.raises(NotImplementedError):
            self.transition.backward_rv(some_normal_rv1, some_normal_rv2)

    def test_backward_realization(self, some_normal_rv1, some_normal_rv2):
        with pytest.raises(NotImplementedError):
            self.transition.backward_realization(some_normal_rv1.mean, some_normal_rv2)

    def test_input_dim(self, test_ndim):
        assert self.transition.input_dim == test_ndim

    def test_output_dim(self, test_ndim):
        assert self.transition.output_dim == test_ndim
