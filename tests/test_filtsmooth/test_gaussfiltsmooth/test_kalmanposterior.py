import numpy as np
import pytest

import probnum.problems.zoo.filtsmooth as filtsmooth_zoo
from probnum import filtsmooth, problems, randprocs, randvars, statespace, utils
from probnum._randomvariablelist import _RandomVariableList


@pytest.fixture
def problem():
    """Car-tracking problem."""
    return filtsmooth_zoo.car_tracking()


@pytest.fixture
def setup(problem):
    """Filter and regression problem."""
    regression_problem, statespace_components = problem
    kalman = filtsmooth.Kalman(
        statespace_components["prior_process"],
    )

    return (
        kalman,
        regression_problem,
        statespace_components["measurement_model"],
    )


@pytest.fixture
def posterior(setup):
    """Kalman smoothing posterior."""
    kalman, regression_problem, measurement_model = setup
    posterior, _ = kalman.filtsmooth(regression_problem, measurement_model)
    return posterior


def test_len(posterior):
    """__len__ performs as expected."""
    assert len(posterior) > 0
    assert len(posterior.locations) == len(posterior)
    assert len(posterior.states) == len(posterior)


def test_locations(posterior, setup):
    """Locations are stored correctly."""
    _, regression_problem, _ = setup
    times = regression_problem.locations
    np.testing.assert_allclose(posterior.locations, np.sort(posterior.locations))
    np.testing.assert_allclose(posterior.locations, times)


def test_getitem(posterior):
    """Getitem performs as expected."""

    np.testing.assert_allclose(posterior[0].mean, posterior.states[0].mean)
    np.testing.assert_allclose(posterior[0].cov, posterior.states[0].cov)

    np.testing.assert_allclose(posterior[-1].mean, posterior.states[-1].mean)
    np.testing.assert_allclose(posterior[-1].cov, posterior.states[-1].cov)

    np.testing.assert_allclose(posterior[:].mean, posterior.states[:].mean)
    np.testing.assert_allclose(posterior[:].cov, posterior.states[:].cov)


def test_states(posterior):
    """RVs are stored correctly."""

    assert isinstance(posterior.states, _RandomVariableList)
    assert len(posterior.states[0].shape) == 1


def test_call_error_if_small(posterior):
    """Evaluating in the past of the data raises an error."""
    assert -0.5 < posterior.locations[0]
    with pytest.raises(NotImplementedError):
        posterior(-0.5)


def test_call_vectorisation(posterior):
    """Evaluation allows vector inputs."""
    locs = np.arange(0, 1, 20)
    evals = posterior(locs)
    assert len(evals) == len(locs)


def test_call_interpolation(posterior):
    """Interpolation is possible and returns a Normal RV."""
    assert posterior.locations[0] < 9.88 < posterior.locations[-1]
    assert 9.88 not in posterior.locations
    out_rv = posterior(9.88)
    assert isinstance(out_rv, randvars.Normal)


def test_call_to_discrete(posterior):
    """Called at a grid point, the respective disrete solution is returned."""

    first_point = posterior.locations[0]
    np.testing.assert_allclose(posterior(first_point).mean, posterior[0].mean)
    np.testing.assert_allclose(posterior(first_point).cov, posterior[0].cov)

    final_point = posterior.locations[-1]
    np.testing.assert_allclose(posterior(final_point).mean, posterior[-1].mean)
    np.testing.assert_allclose(posterior(final_point).cov, posterior[-1].cov)

    mid_point = posterior.locations[4]
    np.testing.assert_allclose(posterior(mid_point).mean, posterior[4].mean)
    np.testing.assert_allclose(posterior(mid_point).cov, posterior[4].cov)


def test_call_extrapolation(posterior):
    """Extrapolation is possible and returns a Normal RV."""
    assert posterior.locations[-1] < 30.0
    out_rv = posterior(30.0)
    assert isinstance(out_rv, randvars.Normal)


@pytest.fixture
def seed():
    return 42


# Sampling shape checks include extrapolation phases
IN_DOMAIN_DENSE_LOCS = np.arange(0.0, 0.5, 0.025)
OUT_OF_DOMAIN_DENSE_LOCS = np.arange(0.0, 500.0, 25.0)


@pytest.mark.parametrize("locs", [None, IN_DOMAIN_DENSE_LOCS, OUT_OF_DOMAIN_DENSE_LOCS])
@pytest.mark.parametrize("size", [(), 2, (2,), (2, 2)])
def test_sampling_shapes(posterior, locs, size):
    """Shape of the returned samples matches expectation."""
    samples = posterior.sample(t=locs, size=size)

    if isinstance(size, int):
        size = (size,)
    if locs is None:
        expected_size = (
            size + posterior.states.shape
        )  # (*size, *posterior.states.shape)
    else:
        expected_size = (
            size + locs.shape + posterior.states[0].shape
        )  # (*size, *posterior(locs).mean.shape)

    assert samples.shape == expected_size


@pytest.mark.parametrize("locs", [np.arange(0.0, 0.5, 0.025)])
@pytest.mark.parametrize("size", [(), 2, (2,), (2, 2)])
def test_sampling_shapes_1d(locs, size):
    """Make the sampling tests for a 1d posterior."""
    locations = np.linspace(0, 2 * np.pi, 100)
    data = 0.5 * np.random.randn(100) + np.sin(locations)

    prior = statespace.IBM(0, 1)
    measmod = statespace.DiscreteLTIGaussian(
        state_trans_mat=np.eye(1), shift_vec=np.zeros(1), proc_noise_cov_mat=np.eye(1)
    )
    initrv = randvars.Normal(np.zeros(1), np.eye(1))

    prior_process = randprocs.MarkovProcess(
        transition=measmod, initrv=initrv, initarg=locations[0]
    )
    kalman = filtsmooth.Kalman(prior_process)
    regression_problem = problems.RegressionProblem(
        observations=data, locations=locations
    )
    posterior, _ = kalman.filtsmooth(regression_problem, measmod)

    size = utils.as_shape(size)
    if locs is None:
        base_measure_reals = np.random.randn(*(size + posterior.locations.shape + (1,)))
        samples = posterior.transform_base_measure_realizations(
            base_measure_reals, t=posterior.locations
        )
    else:
        locs = np.union1d(locs, posterior.locations)
        base_measure_reals = np.random.randn(*(size + (len(locs),)) + (1,))
        samples = posterior.transform_base_measure_realizations(
            base_measure_reals, t=locs
        )

    assert samples.shape == base_measure_reals.shape
