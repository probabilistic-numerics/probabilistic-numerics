import numpy as np
import pytest

import probnum.random_variables as pnrv
from probnum.filtsmooth import statespace as pnfss
from probnum.problems.zoo.linalg import random_spd_matrix

from .test_sde import TestLTISDE


@pytest.fixture
def some_ordint(test_ndim):
    return test_ndim - 1


class TestIntegrator:
    """An integrator should be usable as is, but its tests are also useful for IBM,
    IOUP, etc."""

    # Replacement for an __init__ in the pytest language. See:
    # https://stackoverflow.com/questions/21430900/py-test-skips-test-class-if-constructor-is-defined
    @pytest.fixture(autouse=True)
    def _setup(self, some_ordint):
        self.some_ordint = some_ordint
        self.integrator = pnfss.Integrator(ordint=self.some_ordint, spatialdim=1)

    def test_proj2coord(self):
        base = np.zeros(self.some_ordint + 1)
        base[0] = 1
        e_0_expected = np.kron(np.eye(1), base)
        e_0 = self.integrator.proj2coord(coord=0)
        np.testing.assert_allclose(e_0, e_0_expected)

        base = np.zeros(self.some_ordint + 1)
        base[-1] = 1
        e_q_expected = np.kron(np.eye(1), base)
        e_q = self.integrator.proj2coord(coord=self.some_ordint)
        np.testing.assert_allclose(e_q, e_q_expected)

    def test_precon(self):

        assert isinstance(self.integrator.precon, pnfss.NordsieckLikeCoordinates)


class TestIBM(TestLTISDE, TestIntegrator):

    # Replacement for an __init__ in the pytest language. See:
    # https://stackoverflow.com/questions/21430900/py-test-skips-test-class-if-constructor-is-defined
    @pytest.fixture(autouse=True)
    def _setup(
        self,
        some_ordint,
        forw_impl_string_linear_gauss,
        backw_impl_string_linear_gauss,
    ):
        self.some_ordint = some_ordint
        spatialdim = 1  # make tests compatible with some_normal_rv1, etc.
        self.transition = pnfss.IBM(
            ordint=self.some_ordint,
            spatialdim=spatialdim,
            forward_implementation=forw_impl_string_linear_gauss,
            backward_implementation=backw_impl_string_linear_gauss,
        )

        self.G = lambda t: self.transition.driftmat
        self.v = lambda t: self.transition.forcevec
        self.L = lambda t: self.transition.dispmat

        self.g = lambda t, x: self.G(t) @ x + self.v(t)
        self.dg = lambda t, x: self.G(t)

    @property
    def integrator(self):
        return self.transition


class TestIOUP(TestLTISDE, TestIntegrator):

    # Replacement for an __init__ in the pytest language. See:
    # https://stackoverflow.com/questions/21430900/py-test-skips-test-class-if-constructor-is-defined
    @pytest.fixture(autouse=True)
    def _setup(
        self,
        some_ordint,
        forw_impl_string_linear_gauss,
        backw_impl_string_linear_gauss,
    ):
        self.some_ordint = some_ordint
        spatialdim = 1  # make tests compatible with some_normal_rv1, etc.
        self.transition = pnfss.IOUP(
            ordint=self.some_ordint,
            spatialdim=spatialdim,
            driftspeed=1.2345,
            forward_implementation=forw_impl_string_linear_gauss,
            backward_implementation=backw_impl_string_linear_gauss,
        )

        self.G = lambda t: self.transition.driftmat
        self.v = lambda t: self.transition.forcevec
        self.L = lambda t: self.transition.dispmat

        self.g = lambda t, x: self.G(t) @ x + self.v(t)
        self.dg = lambda t, x: self.G(t)

    @property
    def integrator(self):
        return self.transition


class TestMatern(TestLTISDE, TestIntegrator):

    # Replacement for an __init__ in the pytest language. See:
    # https://stackoverflow.com/questions/21430900/py-test-skips-test-class-if-constructor-is-defined
    @pytest.fixture(autouse=True)
    def _setup(
        self,
        some_ordint,
        forw_impl_string_linear_gauss,
        backw_impl_string_linear_gauss,
    ):
        self.some_ordint = some_ordint
        spatialdim = 1  # make tests compatible with some_normal_rv1, etc.
        self.transition = pnfss.Matern(
            ordint=self.some_ordint,
            spatialdim=spatialdim,
            lengthscale=1.2345,
            forward_implementation=forw_impl_string_linear_gauss,
            backward_implementation=backw_impl_string_linear_gauss,
        )

        self.G = lambda t: self.transition.driftmat
        self.v = lambda t: self.transition.forcevec
        self.L = lambda t: self.transition.dispmat

        self.g = lambda t, x: self.G(t) @ x + self.v(t)
        self.dg = lambda t, x: self.G(t)

    @property
    def integrator(self):
        return self.transition


def both_transitions_matern():
    matern = pnfss.Matern(ordint=2, spatialdim=2, lengthscale=2.041)
    matern2 = pnfss.Matern(ordint=2, spatialdim=2, lengthscale=2.041)
    matern_as_ltisde = pnfss.LTISDE(matern2.driftmat, matern2.forcevec, matern2.dispmat)
    return matern, matern_as_ltisde


def both_transitions_ioup():
    ioup = pnfss.IOUP(ordint=2, spatialdim=2, driftspeed=2.041)
    ioup2 = pnfss.IOUP(ordint=2, spatialdim=2, driftspeed=2.041)
    ioup_as_ltisde = pnfss.LTISDE(ioup2.driftmat, ioup2.forcevec, ioup2.dispmat)
    return ioup, ioup_as_ltisde


def both_transitions_ibm():
    ibm = pnfss.IBM(ordint=2, spatialdim=1)
    ibm2 = pnfss.IBM(ordint=2, spatialdim=1)
    ibm_as_ltisde = pnfss.LTISDE(ibm2.driftmat, ibm2.forcevec, ibm2.dispmat)
    return ibm, ibm_as_ltisde


@pytest.mark.parametrize(
    "both_transitions",
    [both_transitions_ibm(), both_transitions_ioup(), both_transitions_matern()],
)
def test_same_forward_outputs(both_transitions, diffusion):
    trans1, trans2 = both_transitions
    real = 1 + 0.1 * np.random.rand(trans1.dimension)
    out_1, info1 = trans1.forward_realization(
        real, t=0.0, dt=0.5, compute_gain=True, _diffusion=diffusion
    )
    out_2, info2 = trans2.forward_realization(
        real, t=0.0, dt=0.5, compute_gain=True, _diffusion=diffusion
    )
    np.testing.assert_allclose(out_1.mean, out_2.mean)
    np.testing.assert_allclose(out_1.cov, out_2.cov)
    np.testing.assert_allclose(info1["crosscov"], info2["crosscov"])
    np.testing.assert_allclose(info1["gain"], info2["gain"])


@pytest.mark.parametrize(
    "both_transitions",
    [both_transitions_ibm(), both_transitions_ioup(), both_transitions_matern()],
)
def test_same_backward_outputs(both_transitions, diffusion):
    trans1, trans2 = both_transitions
    real = 1 + 0.1 * np.random.rand(trans1.dimension)
    real2 = 1 + 0.1 * np.random.rand(trans1.dimension)
    cov = random_spd_matrix(trans1.dimension)
    rv = pnrv.Normal(real2, cov)
    out_1, info1 = trans1.backward_realization(
        real, rv, t=0.0, dt=0.5, compute_gain=True, _diffusion=diffusion
    )
    out_2, info2 = trans2.backward_realization(
        real, rv, t=0.0, dt=0.5, compute_gain=True, _diffusion=diffusion
    )
    np.testing.assert_allclose(out_1.mean, out_2.mean)
    np.testing.assert_allclose(out_1.cov, out_2.cov)

    # Both dicts are empty?
    assert not info1
    assert not info2


@pytest.fixture
def dt():
    return 0.1


@pytest.fixture
def ah_22_ibm(dt):
    return np.array(
        [
            [1.0, dt, dt ** 2 / 2.0],
            [0.0, 1.0, dt],
            [0.0, 0.0, 1.0],
        ]
    )


@pytest.fixture
def qh_22_ibm(dt):
    return np.array(
        [
            [dt ** 5 / 20.0, dt ** 4 / 8.0, dt ** 3 / 6.0],
            [dt ** 4 / 8.0, dt ** 3 / 3.0, dt ** 2 / 2.0],
            [dt ** 3 / 6.0, dt ** 2 / 2.0, dt],
        ]
    )


@pytest.fixture
def spdmat3x3():
    return random_spd_matrix(3)


@pytest.fixture
def normal_rv3x3(spdmat3x3):

    return pnrv.Normal(
        mean=np.random.rand(3),
        cov=spdmat3x3,
        cov_cholesky=np.linalg.cholesky(spdmat3x3),
    )


class TestIBMValues:

    # Replacement for an __init__ in the pytest language. See:
    # https://stackoverflow.com/questions/21430900/py-test-skips-test-class-if-constructor-is-defined
    @pytest.fixture(autouse=True)
    def _setup(
        self,
        forw_impl_string_linear_gauss,
        backw_impl_string_linear_gauss,
    ):
        spatialdim = 1  # make tests compatible with some_normal_rv1, etc.
        self.transition = pnfss.IBM(
            ordint=2,
            spatialdim=spatialdim,
            forward_implementation=forw_impl_string_linear_gauss,
            backward_implementation=backw_impl_string_linear_gauss,
        )

    def test_discretise_values(self, ah_22_ibm, qh_22_ibm, dt):
        discrete_model = self.transition.discretise(dt=dt)
        np.testing.assert_allclose(discrete_model.state_trans_mat, ah_22_ibm)
        np.testing.assert_allclose(discrete_model.proc_noise_cov_mat, qh_22_ibm)

    def test_forward_rv_values(self, normal_rv3x3, diffusion, ah_22_ibm, qh_22_ibm, dt):
        rv, _ = self.transition.forward_rv(
            normal_rv3x3, t=0.0, dt=dt, _diffusion=diffusion
        )
        np.testing.assert_allclose(ah_22_ibm @ normal_rv3x3.mean, rv[:3].mean)
        np.testing.assert_allclose(
            ah_22_ibm @ normal_rv3x3.cov @ ah_22_ibm.T + diffusion * qh_22_ibm,
            rv.cov,
        )

    def test_forward_realization_values(
        self, normal_rv3x3, diffusion, ah_22_ibm, qh_22_ibm, dt
    ):
        real = normal_rv3x3.sample()
        rv, _ = self.transition.forward_realization(
            real, t=0.0, dt=dt, _diffusion=diffusion
        )
        np.testing.assert_allclose(ah_22_ibm @ real, rv.mean)
        np.testing.assert_allclose(diffusion * qh_22_ibm, rv.cov)
