"""Tests for linear solver information operators."""

import pathlib

import numpy as np

from probnum.linalg.solvers import LinearSolverState, information_ops

from pytest_cases import parametrize_with_cases

case_modules = (pathlib.Path(__file__).parent / "cases").stem
cases_information_ops = case_modules + ".information_ops"
cases_states = case_modules + ".states"


@parametrize_with_cases("info_op", cases=cases_information_ops)
@parametrize_with_cases("state", cases=cases_states, has_tag=["has_action"])
def test_returns_ndarray_or_scalar(
    info_op: information_ops.LinearSolverInformationOp, state: LinearSolverState
):
    observation = info_op(state)
    assert isinstance(observation, np.ndarray) or np.isscalar(observation)
