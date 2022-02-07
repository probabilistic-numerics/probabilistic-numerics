"""Test for ODE residual information operator."""

import numpy as np
import pytest

from probnum import diffeq, randprocs, randvars
from tests.test_diffeq.test_odefilter.test_information_operators import (
    _information_operator_test_inferface,
)


class TestODEResidual(_information_operator_test_inferface.ODEInformationOperatorTest):
    @pytest.fixture(autouse=True)
    def _setup(self):
        num_prior_derivatives = 3
        ode_dimension = 2

        self.info_op = diffeq.odefilter.information_operators.ODEResidual(
            num_prior_derivatives=num_prior_derivatives, ode_dimension=ode_dimension
        )
        self.initial_rv = randvars.Normal(
            mean=np.arange(self.info_op.input_dim), cov=np.eye(self.info_op.input_dim)
        )

    def test_call(self, fitzhughnagumo):
        self.info_op.incorporate_ode(ode=fitzhughnagumo)
        called = self.info_op(fitzhughnagumo.t0, self.initial_rv.mean)
        assert isinstance(called, np.ndarray)
        assert called.shape == (self.info_op.output_dim,)

    def test_jacobian(self, fitzhughnagumo):
        self.info_op.incorporate_ode(ode=fitzhughnagumo)
        called = self.info_op.jacobian(fitzhughnagumo.t0, self.initial_rv.mean)
        assert isinstance(called, np.ndarray)
        assert called.shape == (self.info_op.output_dim, self.info_op.input_dim)

    def test_as_transition(self, fitzhughnagumo):
        # Nothin happens unless an ODE has been incorporated
        with pytest.raises(ValueError):
            self.info_op.as_transition()

        # Basic functionality works: default arguments
        self.info_op.incorporate_ode(ode=fitzhughnagumo)
        transition = self.info_op.as_transition()
        assert isinstance(transition, randprocs.markov.discrete.NonlinearGaussian)

        noise_fun = lambda t: randvars.Normal(
            mean=np.zeros(self.info_op.output_dim), cov=np.eye(self.info_op.output_dim)
        )
        transition = self.info_op.as_transition(
            noise_fun=noise_fun,
        )
        noise = transition.noise_fun(0.0)
        assert isinstance(transition, randprocs.markov.discrete.NonlinearGaussian)
        assert np.linalg.norm(noise.cov) > 0.0
        assert np.linalg.norm(noise.cov_cholesky) > 0.0

    def test_incorporate_ode(self, fitzhughnagumo):
        self.info_op.incorporate_ode(ode=fitzhughnagumo)
        assert self.info_op.ode == fitzhughnagumo

        # Incorporating an ODE when another one has been
        # incorporated raises a ValueError
        with pytest.raises(ValueError):
            self.info_op.incorporate_ode(ode=fitzhughnagumo)

    def test_ode_has_been_incorporated(self, fitzhughnagumo):
        assert self.info_op.ode_has_been_incorporated is False
        self.info_op.incorporate_ode(ode=fitzhughnagumo)
        assert self.info_op.ode_has_been_incorporated is True
