import numpy as np
import pytest
from scipy.integrate._ivp import base, rk
from scipy.integrate._ivp.common import OdeSolution

from probnum import diffeq, randvars
from probnum.diffeq import odesolution, wrapperscipyodesolution, wrapperscipysolver


@pytest.fixture
def y():
    return np.array([0.1])


@pytest.fixture
def times():
    return [0.0, 1.0]


@pytest.fixture
def logistic():
    return diffeq.logistic(times, y0)


@pytest.fixture
def lorenz():
    return diffeq.lorenz(times, [0.0, 1.0, 1.05])


@pytest.fixture
def scipysolverlog(logistic, initrv):
    return rk.RK45(logistic.rhs, logistic.t0, y0, logistic.tmax)


@pytest.fixture
def scipysolverlorenz(lorenz):
    return rk.RK45(lorenz.rhs, lorenz.t0, [0.0, 1.0, 1.05], lorenz.tmax)


@pytest.fixture
def testsolverlog(logistic, initrv):
    testsolver = rk.RK45(logistic.rhs, logistic.t0, y0, logistic.tmax)
    return wrapperscipysolver.WrapperScipyRungeKutta(testsolver, order=4)


@pytest.fixture
def testsolverlorenz(lorenz):
    testsolver = rk.RK45(lorenz.rhs, lorenz.t0, [0.0, 1.0, 1.05], lorenz.tmax)
    return wrapperscipysolver.WrapperScipyRungeKutta(testsolver, order=4)


@pytest.fixture
def start_point():
    return 0.5


@pytest.fixture
def stop_point():
    return 0.6


@pytest.fixture
def dense_output():
    return [base.DenseOutput(0, 1)]


@pytest.fixture
def lst():
    return list([randvars.Constant(1)])


@pytest.mark.parametrize(
    "testsolver45,scipysolver45",
    [(testsolverlog, scipysolverlog), (testsolverlorenz, scipysolverlorenz)],
)
def test_initialise(testsolver45, scipysolver45):
    time, state = testsolver45.initialise()
    time_scipy = scipysolver45.t
    state_scipy = scipysolver45.y
    np.testing.assert_allclose(time, time_scipy, atol=1e-14, rtol=1e-14)
    np.testing.assert_allclose(state.mean[0], state_scipy[0], atol=1e-14, rtol=1e-14)


"""
def test_step_execution(scipysolver45, testsolver45, start_point, stop_point, y):
    scipy_y_new, f_new = rk.rk_step(
        scipysolver45.fun,
        start_point,
        y,
        scipysolver45.f,
        stop_point - start_point,
        scipysolver45.A,
        scipysolver45.B,
        scipysolver45.C,
        scipysolver45.K,
    )
    scipy_error_estimation = scipysolver45._estimate_error(
        scipysolver45.K, stop_point - start_point
    )
    solver_y_new, solver_error_estimation = testsolver45.step(
        start_point, stop_point, randvars.Constant(0.1)
    )
    np.testing.assert_allclose(solver_y_new.mean, scipy_y_new, atol=1e-14, rtol=1e-14)
    np.testing.assert_allclose(
        solver_error_estimation, scipy_error_estimation, atol=1e-14, rtol=1e-14
    )


def test_step_variables(scipysolver45, testsolver45, y, start_point, stop_point):
    solver_y_new, solver_error_estimation = testsolver45.step(
        start_point, stop_point, randvars.Constant(y)
    )
    y_new, f_new = rk.rk_step(
        scipysolver45.fun,
        start_point,
        y,
        scipysolver45.f,
        stop_point - start_point,
        scipysolver45.A,
        scipysolver45.B,
        scipysolver45.C,
        scipysolver45.K,
    )
    # locations are correct
    np.testing.assert_allclose(
        testsolver45.solver.t_old, start_point, atol=1e-14, rtol=1e-14
    )
    np.testing.assert_allclose(
        testsolver45.solver.t, stop_point, atol=1e-14, rtol=1e-14
    )
    np.testing.assert_allclose(
        testsolver45.solver.h_previous, stop_point - start_point, atol=1e-14, rtol=1e-14
    )
    # evaluations are correct
    np.testing.assert_allclose(
        testsolver45.solver.y_old.mean, y, atol=1e-14, rtol=1e-14
    )
    np.testing.assert_allclose(testsolver45.solver.y, y_new, atol=1e-14, rtol=1e-14)
    np.testing.assert_allclose(
        testsolver45.solver.h_abs, stop_point - start_point, atol=1e-14, rtol=1e-14
    )
    np.testing.assert_allclose(testsolver45.solver.f, f_new, atol=1e-14, rtol=1e-14)


def test_dense_output(scipysolver45, testsolver45, y, start_point, stop_point):
    # step has to be performed before dense-output can be computed
    scipysolver45.step()
    # perform step of the same size
    testsolver45.step(
        scipysolver45.t_old, scipysolver45.t, randvars.Constant(scipysolver45.y_old),
    )
    testsolver_dense = testsolver45.dense_output()
    scipy_dense = scipysolver45._dense_output_impl()
    np.testing.assert_allclose(
        testsolver_dense(scipysolver45.t_old),
        scipy_dense(scipysolver45.t_old),
        atol=1e-14,
        rtol=1e-14,
    )
    np.testing.assert_allclose(
        testsolver_dense(scipysolver45.t),
        scipy_dense(scipysolver45.t),
        atol=1e-14,
        rtol=1e-14,
    )
    np.testing.assert_allclose(
        testsolver_dense((scipysolver45.t_old + scipysolver45.t) / 2),
        scipy_dense((scipysolver45.t_old + scipysolver45.t) / 2),
        atol=1e-14,
        rtol=1e-14,
    )


def test_rvlist_to_odesol(times, dense_output, lst):
    scipy_sol = OdeSolution(times, dense_output)
    probnum_solution = wrapperscipyodesolution.WrapperScipyODESolution(
        scipy_sol, times, lst
    )
    assert issubclass(
        wrapperscipyodesolution.WrapperScipyODESolution, odesolution.ODESolution
    )
    assert isinstance(probnum_solution, wrapperscipyodesolution.WrapperScipyODESolution)
"""
