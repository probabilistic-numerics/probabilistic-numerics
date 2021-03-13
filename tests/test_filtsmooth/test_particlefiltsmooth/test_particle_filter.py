import numpy as np
import pytest

from probnum import filtsmooth, random_variables, statespace

from ..filtsmooth_testcases import pendulum


def test_effective_number_of_events():
    weights = np.random.rand(10)
    categ = random_variables.Categorical(
        support=np.random.rand(10, 2), probabilities=weights / np.sum(weights)
    )
    ess = filtsmooth.effective_number_of_events(categ)
    assert 0 < ess < 10


def test_resample_categorical():
    weights = np.random.rand(10)
    categ = random_variables.Categorical(
        support=np.random.rand(10, 2), probabilities=weights / np.sum(weights)
    )
    new_categ = filtsmooth.resample_categorical(categ)
    assert isinstance(new_categ, random_variables.Categorical)
    assert new_categ.shape == categ.shape
    np.testing.assert_allclose(np.diff(new_categ.probabilities), 0.0)


# Test the RMSE on a pendulum example


@pytest.fixture
def num_particles():
    return 4


@pytest.fixture
def problem():
    return pendulum()


@pytest.fixture
def data(problem):
    """Downsample pendulum data because PF is EXPENSIVE."""
    dynamod, measmod, initrv, info = problem
    delta_t = 16 * info["dt"]
    tmax = info["tmax"]
    times = np.arange(0, tmax, delta_t)
    states, obs = statespace.generate_samples(dynamod, measmod, initrv, times)

    return states, obs, times


@pytest.fixture
def linearized_measmod(problem, measmod_style):
    """UKF-importance density and bootstrap PF."""
    if measmod_style == "uk":
        dynmod, measmod, initrv, info = problem
        linearized_measmod = filtsmooth.DiscreteUKFComponent(measmod)
        return linearized_measmod

    # Now measmod_style is "none"
    return None


@pytest.fixture
def particle(problem, num_particles, linearized_measmod):
    """Create a particle filter."""
    dynmod, measmod, initrv, info = problem

    particle = filtsmooth.ParticleFilter(
        dynmod,
        measmod,
        initrv,
        num_particles=num_particles,
        linearized_measurement_model=linearized_measmod,
    )
    return particle


@pytest.fixture
def pf_output(particle, data, num_particles):
    true_states, obs, locations = data
    return particle.filter(obs, locations)


@pytest.mark.parametrize("measmod_style", ["uk", "none"])
def test_shape_pf_output(pf_output, data, num_particles):
    true_states, obs, locations = data

    states = pf_output.states.support
    weights = pf_output.states.probabilities
    num_gridpoints = len(locations)
    assert states.shape == (num_gridpoints, num_particles, 2)
    assert weights.shape == (num_gridpoints, num_particles)


@pytest.mark.parametrize("measmod_style", ["uk", "none"])
def test_rmse_particlefilter(pf_output, data):
    """Assert that the RMSE of the mode of the posterior of the PF is a lot smaller than
    the RMSE of the data."""
    true_states, obs, locations = data

    mode = pf_output.states.mode
    rmse_mode = np.linalg.norm(np.sin(mode) - np.sin(true_states)) / np.sqrt(
        true_states.size
    )
    rmse_data = np.linalg.norm(obs - np.sin(true_states)) / np.sqrt(true_states.size)

    # RMSE of PF.mode strictly better than RMSE of data
    assert rmse_mode < 0.9 * rmse_data
