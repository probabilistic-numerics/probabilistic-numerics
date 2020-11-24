import unittest

import numpy as np

from probnum.diffeq.ode import ivp
from probnum.diffeq.ode import ivp_examples
from probnum.random_variables import Constant
from tests.testing import NumpyAssertions

TEST_NDIM = 3


class TestExamples(unittest.TestCase, NumpyAssertions):
    """Test cases for example IVPs: Lotka-Volterra, etc."""

    def setUp(self):
        self.tspan = (0.0, 4.212)

    def test_logistic(self):
        """Test the logistic ODE convenience function."""
        rv = Constant(0.1)
        lg1 = ivp_examples.logistic(self.tspan, rv)
        self.assertEqual(issubclass(type(lg1), ivp.IVP), True)
        lg2 = ivp_examples.logistic(self.tspan, rv, params=(1.0, 1.0))
        self.assertEqual(issubclass(type(lg2), ivp.IVP), True)

    def test_logistic_jacobian(self):
        rv = Constant(0.1)
        lg1 = ivp_examples.logistic(self.tspan, rv)
        random_direction = 1 + 0.1 * np.random.rand(lg1.dimension)
        random_point = 1 + np.random.rand(lg1.dimension)
        fd_approx = (
            0.5
            * 1e11
            * (
                lg1(0.1, random_point + 1e-11 * random_direction)
                - lg1(0.1, random_point - 1e-11 * random_direction)
            )
        )
        self.assertAllClose(
            lg1.jacobian(0.1, random_point) @ random_direction, fd_approx, rtol=1e-2
        )

    def test_fitzhughnagumo(self):
        rv = Constant(np.ones(2))
        lg1 = ivp_examples.fitzhughnagumo(self.tspan, rv)
        self.assertEqual(issubclass(type(lg1), ivp.IVP), True)
        lg2 = ivp_examples.fitzhughnagumo(self.tspan, rv, params=(1.0, 1.0, 1.0, 1.0))
        self.assertEqual(issubclass(type(lg2), ivp.IVP), True)

    def test_fitzhughnagumo_jacobian(self):
        rv = Constant(np.ones(2))
        lg1 = ivp_examples.fitzhughnagumo(self.tspan, rv)
        random_direction = 1 + 0.1 * np.random.rand(lg1.dimension)
        random_point = 1 + np.random.rand(lg1.dimension)
        fd_approx = (
            0.5
            * 1e11
            * (
                lg1(0.1, random_point + 1e-11 * random_direction)
                - lg1(0.1, random_point - 1e-11 * random_direction)
            )
        )
        self.assertAllClose(
            lg1.jacobian(0.1, random_point) @ random_direction, fd_approx, rtol=1e-2
        )

    def test_lotkavolterra(self):
        rv = Constant(np.ones(2))
        lg1 = ivp_examples.lotkavolterra(self.tspan, rv)
        lg2 = ivp_examples.lotkavolterra(self.tspan, rv, params=(1.0, 1.0, 1.0, 1.0))
        self.assertEqual(issubclass(type(lg2), ivp.IVP), True)

    def test_lotkavolterra_jacobian(self):
        rv = Constant(np.ones(2))
        lg1 = ivp_examples.lotkavolterra(self.tspan, rv)
        random_direction = 1 + 0.1 * np.random.rand(lg1.dimension)
        random_point = 1 + np.random.rand(lg1.dimension)
        fd_approx = (
            0.5
            * 1e11
            * (
                lg1(0.1, random_point + 1e-11 * random_direction)
                - lg1(0.1, random_point - 1e-11 * random_direction)
            )
        )
        self.assertAllClose(
            lg1.jacobian(0.1, random_point) @ random_direction, fd_approx, rtol=1e-2
        )

    def test_seir(self):
        """
        Test the SEIR ODE convenience function.
        """
        rv = Constant(np.array([1.0, 0.0, 0.0, 0.0]))
        lg1 = ivp_examples.seir(self.tspan, rv)
        self.assertEqual(issubclass(type(lg1), ivp.IVP), True)
        lg2 = ivp_examples.seir(self.tspan, rv, params=(1.0, 1.0, 1.0, 1.0))
        self.assertEqual(issubclass(type(lg2), ivp.IVP), True)

    def test_rigidbody(self):
        """
        Test the rigidbody ODE convenience function.
        """
        rv = Constant(np.array([1.0, 1.0, 1.0]))
        lg1 = ivp_examples.rigidbody(self.tspan, rv)
        self.assertEqual(issubclass(type(lg1), ivp.IVP), True)

    def test_rigidbody_jacobian(self):
        rv = Constant(np.array([1.0, 1.0, 1.0]))
        lg1 = ivp_examples.rigidbody(self.tspan, rv)
        random_direction = 1 + 0.1 * np.random.rand(lg1.dimension)
        random_point = 1 + np.random.rand(lg1.dimension)
        fd_approx = (
            0.5
            * 1e11
            * (
                lg1(0.1, random_point + 1e-11 * random_direction)
                - lg1(0.1, random_point - 1e-11 * random_direction)
            )
        )
        self.assertAllClose(
            lg1.jacobian(0.1, random_point) @ random_direction, fd_approx, rtol=1e-2
        )

    def test_vanderpol(self):
        """
        Test the Van der Pol ODE convenience function.
        """
        rv = Constant(np.array([1.0, 1.0]))
        lg1 = ivp_examples.vanderpol(self.tspan, rv)
        self.assertEqual(issubclass(type(lg1), ivp.IVP), True)
        lg2 = ivp_examples.vanderpol(self.tspan, rv, params=(2.0,))
        self.assertEqual(issubclass(type(lg2), ivp.IVP), True)
        lg3 = ivp_examples.vanderpol(self.tspan, rv, params=2.0)
        self.assertEqual(issubclass(type(lg3), ivp.IVP), True)

    def test_vanderpol_jacobian(self):
        rv = Constant(np.array([1.0, 1.0]))
        lg1 = ivp_examples.vanderpol(self.tspan, rv)
        random_direction = 1 + 0.1 * np.random.rand(lg1.dimension)
        random_point = 1 + np.random.rand(lg1.dimension)
        fd_approx = (
            0.5
            * 1e11
            * (
                lg1(0.1, random_point + 1e-11 * random_direction)
                - lg1(0.1, random_point - 1e-11 * random_direction)
            )
        )
        self.assertAllClose(
            lg1.jacobian(0.1, random_point) @ random_direction, fd_approx, rtol=1e-2
        )


class TestIVP(unittest.TestCase):
    def setUp(self):
        def rhs_(t, x):
            return -x

        def jac_(t, x):
            return -np.eye(len(x))

        def sol_(t):
            return np.exp(-t) * np.ones(TEST_NDIM)

        some_center = np.random.rand(TEST_NDIM)
        rv = Constant(some_center)
        self.mockivp = ivp.IVP(
            (0.0, np.random.rand()), rv, rhs=rhs_, jac=jac_, sol=sol_
        )

    def test_rhs(self):
        some_x = np.random.rand(TEST_NDIM)
        some_t = np.random.rand()
        out = self.mockivp.rhs(some_t, some_x)
        self.assertEqual(len(out), TEST_NDIM)

    def test_jacobian(self):
        some_x = np.random.rand(TEST_NDIM)
        some_t = np.random.rand()
        out = self.mockivp.jacobian(some_t, some_x)
        self.assertEqual(out.shape[0], TEST_NDIM)
        self.assertEqual(out.shape[1], TEST_NDIM)

    def test_solution(self):
        some_t = np.random.rand()
        out = self.mockivp.solution(some_t)
        self.assertEqual(out.ndim, 1)
        self.assertEqual(out.shape[0], TEST_NDIM)

    def test_initialdistribution(self):
        __ = self.mockivp.initialdistribution

    def test_timespan(self):
        __, __ = self.mockivp.timespan
