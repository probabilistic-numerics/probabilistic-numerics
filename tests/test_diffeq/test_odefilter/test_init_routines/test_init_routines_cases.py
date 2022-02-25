"""Test cases for initialization."""

import pytest_cases

from probnum.diffeq.odefilter import init_routines
from probnum.problems.zoo import diffeq as diffeq_zoo

from . import known_initial_derivatives

try:
    from jax.config import config  # speed...

    config.update("jax_disable_jit", True)
except ImportError:
    pass


@pytest_cases.case(tags=("jax",))
def problem_threebody():
    ivp = diffeq_zoo.threebody_jax()
    threebody_inits_matrix_full = known_initial_derivatives.THREEBODY_INITS
    return ivp, threebody_inits_matrix_full


@pytest_cases.case(tags=("numpy",))
def problem_lotka_volterra():
    ivp = diffeq_zoo.lotkavolterra()
    inits_matrix_full = known_initial_derivatives.LV_INITS
    return ivp, inits_matrix_full


@pytest_cases.case(tags=["is_exact", "requires_jax"])
def solver_taylor_mode():
    return init_routines.TaylorMode()


@pytest_cases.case(tags=["is_exact", "requires_jax"])
def solver_auto_diff_forward_jvp():
    return init_routines.ForwardModeJVP()


@pytest_cases.case(tags=["is_exact", "requires_jax"])
def solver_auto_diff_forward():
    return init_routines.ForwardMode()


@pytest_cases.case(tags=["is_exact", "requires_jax"])
def solver_auto_diff_reverse():
    return init_routines.ReverseMode()


@pytest_cases.case(tags=["is_not_exact", "requires_numpy"])
def solver_non_probabilistic_fit():
    return init_routines.NonProbabilisticFit()


@pytest_cases.case(tags=["is_not_exact", "requires_numpy"])
def solver_non_probabilistic_fit_with_jacobian():
    return init_routines.NonProbabilisticFitWithJacobian()


@pytest_cases.case(tags=["is_not_exact", "requires_numpy"])
def solver_stack():
    return init_routines.Stack()


@pytest_cases.case(tags=["is_not_exact", "requires_numpy"])
def solver_stack_with_jacobian():
    return init_routines.StackWithJacobian()
