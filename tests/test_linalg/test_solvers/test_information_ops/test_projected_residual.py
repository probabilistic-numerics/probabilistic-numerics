"""Tests for the projected right hand side information operator."""

import pathlib

import numpy as np
from pytest_cases import parametrize_with_cases

from probnum.linalg.solvers import LinearSolverState, information_ops

case_modules = (pathlib.Path(__file__).parent / "cases").stem
cases_information_ops = case_modules + ".information_ops"
cases_states = case_modules + ".states"


@parametrize_with_cases(
    "info_op", cases=cases_information_ops, glob="*projected_residual"
)
@parametrize_with_cases("state", cases=cases_states, has_tag=["has_action"])
def test_is_projected_residual(
    info_op: information_ops.LinearSolverInformationOp, state: LinearSolverState
):
    observation = info_op(state)
    np.testing.assert_equal(observation, state.action.T @ state.residual)
