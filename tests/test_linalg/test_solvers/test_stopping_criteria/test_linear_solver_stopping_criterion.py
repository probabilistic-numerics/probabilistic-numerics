"""Tests for stopping criteria of linear solvers."""

import pathlib

from probnum.linalg.solvers import LinearSolverState, stopping_criteria

from pytest_cases import parametrize_with_cases

case_modules = (pathlib.Path(__file__).parent / "cases").stem
cases_stopping_criteria = case_modules + ".stopping_criteria"
cases_states = case_modules + ".states"


@parametrize_with_cases("stop_crit", cases=cases_stopping_criteria)
@parametrize_with_cases("state", cases=cases_states)
def test_returns_bool(
    stop_crit: stopping_criteria.LinearSolverStoppingCriterion,
    state: LinearSolverState,
):
    assert stop_crit(solver_state=state) in [True, False]
