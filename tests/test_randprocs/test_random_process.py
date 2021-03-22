"""Tests for random processes."""

import numpy as np

from probnum import randprocs, randvars

# pylint: disable=invalid-name


def test_output_shape(random_process: randprocs.RandomProcess, x0: np.ndarray):
    """Test whether evaluations of the random process have the correct shape."""
    if random_process.output_dim == 1:
        assert random_process(x0).ndim == 1
    else:
        assert random_process(x0).shape[1] == random_process.output_dim


def test_mean_shape(random_process: randprocs.RandomProcess, x0: np.ndarray):
    """Test whether the mean of the random process has the correct shape."""
    if random_process.output_dim == 1:
        assert random_process.mean(x0).ndim == 1
    else:
        assert random_process.mean(x0).shape[1] == random_process.output_dim


def test_var_shape(random_process: randprocs.RandomProcess, x0: np.ndarray):
    """Test whether the variance of the random process has the correct shape."""
    if random_process.output_dim == 1:
        assert random_process.var(x0).ndim == 1
    else:
        assert random_process.var(x0).shape[1] == random_process.output_dim


def test_std_shape(random_process: randprocs.RandomProcess, x0: np.ndarray):
    """Test whether the standard deviation of the random process has the correct
    shape."""
    if random_process.output_dim == 1:
        assert random_process.std(x0).ndim == 1
    else:
        assert random_process.std(x0).shape[1] == random_process.output_dim


def test_cov_shape(random_process: randprocs.RandomProcess, x0: np.ndarray):
    """Test whether the covariance of the random process has the correct shape."""
    n = x0.shape[0]
    if random_process.output_dim == 1:
        assert random_process.cov(x0).shape == (n, n) or random_process.cov(x0).ndim < 2
    else:
        assert random_process.cov(x0).shape == (
            n,
            n,
            random_process.output_dim,
            random_process.output_dim,
        )


def test_evaluated_random_process_is_random_variable(
    random_process: randprocs.RandomProcess, random_state: np.random.RandomState
):
    """Test whether evaluating a random process returns a random variable."""
    n_inputs_x0 = 10
    x0 = random_state.normal(size=(n_inputs_x0, random_process.input_dim))
    y0 = random_process(x0)

    assert isinstance(y0, randvars.RandomVariable), (
        f"Output of {repr(random_process)} is not a " f"random variable."
    )


def test_samples_are_callables(
    random_process: randprocs.RandomProcess, random_state: np.random.RandomState
):
    """When not specifying inputs to the sample method it should return ``size`` number
    of callables."""
    assert callable(random_process.sample(random_state=random_state))


def test_rp_mean_cov_evaluated_matches_rv_mean_cov(
    random_process: randprocs.RandomProcess, random_state: np.random.RandomState
):
    """Check whether the evaluated mean and covariance function of a random process is
    equivalent to the mean and covariance of the evaluated random process as a random
    variable."""
    x = random_state.normal(size=(10, random_process.input_dim))

    np.testing.assert_allclose(
        random_process(x).mean,
        random_process.mean(x),
        err_msg=f"Mean of evaluated {repr(random_process)} does not match the "
        f"random process mean function evaluated.",
    )

    np.testing.assert_allclose(
        random_process(x).cov,
        random_process.cov(x),
        err_msg=f"Covariance of evaluated {repr(random_process)} does not match the "
        f"random process mean function evaluated.",
    )
