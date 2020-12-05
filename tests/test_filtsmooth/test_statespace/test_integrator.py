import unittest

import numpy as np

import probnum.filtsmooth as pnfs
import probnum.random_variables as pnrv
from tests.testing import NumpyAssertions


class TestIntegrator(unittest.TestCase, NumpyAssertions):
    def setUp(self) -> None:
        self.q = 3
        self.d = 2
        self.integrator = pnfs.statespace.Integrator(ordint=self.q, spatialdim=self.d)

    def test_proj2coord(self):
        with self.subTest():
            base = np.zeros(self.q + 1)
            base[0] = 1
            e_0_expected = np.kron(np.eye(self.d), base)
            e_0 = self.integrator.proj2coord(coord=0)
            self.assertAllClose(e_0, e_0_expected, rtol=1e-15, atol=0)

        with self.subTest():
            base = np.zeros(self.q + 1)
            base[-1] = 1
            e_q_expected = np.kron(np.eye(self.d), base)
            e_q = self.integrator.proj2coord(coord=self.q)
            self.assertAllClose(e_q, e_q_expected, rtol=1e-15, atol=0)


STEP = np.random.rand()
DIFFCONST = np.random.rand()

AH_22_IBM = np.array(
    [
        [1.0, STEP, STEP ** 2 / 2.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, STEP, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0, STEP, STEP ** 2 / 2.0],
        [0.0, 0.0, 0.0, 0.0, 1.0, STEP],
        [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
    ]
)

QH_22_IBM = DIFFCONST ** 2 * np.array(
    [
        [STEP ** 5 / 20.0, STEP ** 4 / 8.0, STEP ** 3 / 6.0, 0.0, 0.0, 0.0],
        [STEP ** 4 / 8.0, STEP ** 3 / 3.0, STEP ** 2 / 2.0, 0.0, 0.0, 0.0],
        [STEP ** 3 / 6.0, STEP ** 2 / 2.0, STEP, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, STEP ** 5 / 20.0, STEP ** 4 / 8.0, STEP ** 3 / 6.0],
        [0.0, 0.0, 0.0, STEP ** 4 / 8.0, STEP ** 3 / 3.0, STEP ** 2 / 2.0],
        [0.0, 0.0, 0.0, STEP ** 3 / 6.0, STEP ** 2 / 2.0, STEP],
    ]
)


class TestIBM(unittest.TestCase, NumpyAssertions):
    def setUp(self):
        self.sde = pnfs.statespace.IBM(ordint=2, spatialdim=2, diffconst=DIFFCONST)

    def test_discretise(self):
        discrete_model = self.sde.discretise(step=STEP)
        self.assertAllClose(discrete_model.dynamicsmat, AH_22_IBM, 1e-14)

    def test_transition_rv(self):
        mean, cov = np.ones(self.sde.dimension), np.eye(self.sde.dimension)
        initrv = pnrv.Normal(mean, cov)
        rv, _ = self.sde.transition_rv(rv=initrv, start=0.0, stop=STEP)
        self.assertAllClose(AH_22_IBM @ initrv.mean, rv.mean, 1e-14)
        self.assertAllClose(
            AH_22_IBM @ initrv.cov @ AH_22_IBM.T + QH_22_IBM, rv.cov, 1e-14
        )

    def test_transition_rv_preconditioned(self):
        """Check that if the flag is set, the result is different!"""
        mean, cov = np.ones(self.sde.dimension), np.eye(self.sde.dimension)
        initrv = pnrv.Normal(mean, cov)
        rv1, _ = self.sde.transition_rv(rv=initrv, start=0.0, stop=STEP)
        rv2, _ = self.sde.transition_rv_preconditioned(rv=initrv, start=0.0)
        diff1 = np.abs(rv1.mean - rv2.mean)
        diff2 = np.abs(rv1.cov - rv2.cov)

        # Choose some 'sufficiently positive' constant
        # that worked in the present example
        self.assertGreater(np.linalg.norm(diff1), 1e-2)
        self.assertGreater(np.linalg.norm(diff2), 1e-2)

    def test_transition_realization(self):
        mean, cov = np.ones(self.sde.dimension), np.eye(self.sde.dimension)
        state = pnrv.Normal(mean, cov).sample()
        rv, _ = self.sde.transition_realization(real=state, start=0.0, stop=STEP)
        self.assertAllClose(AH_22_IBM @ state, rv.mean, 1e-14)
        self.assertAllClose(QH_22_IBM, rv.cov, 1e-14)

    def test_transition_realization_preconditioned(self):
        mean, cov = np.ones(self.sde.dimension), np.eye(self.sde.dimension)
        state = pnrv.Normal(mean, cov).sample()
        rv1, _ = self.sde.transition_realization(real=state, start=0.0, stop=STEP)
        rv2, _ = self.sde.transition_realization_preconditioned(real=state, start=0.0)
        diff1 = np.abs(rv1.mean - rv2.mean)
        diff2 = np.abs(rv1.cov - rv2.cov)

        # Choose some 'sufficiently positive' constant
        # that worked in the present example
        self.assertGreater(np.linalg.norm(diff1), 1e-2)
        self.assertGreater(np.linalg.norm(diff2), 1e-2)


class TestIOUP(unittest.TestCase, NumpyAssertions):
    def setUp(self):
        driftspeed = 0.151231
        self.ioup = pnfs.statespace.IOUP(2, 2, driftspeed, DIFFCONST)

    def test_transition_rv(self):
        mean, cov = np.ones(self.ioup.dimension), np.eye(self.ioup.dimension)
        initrv = pnrv.Normal(mean, cov)
        self.ioup.transition_rv(initrv, start=0.0, stop=STEP)

    def test_transition_realization(self):
        mean, cov = np.ones(self.ioup.dimension), np.eye(self.ioup.dimension)
        real = pnrv.Normal(mean, cov).sample()
        self.ioup.transition_realization(real, start=0.0, stop=STEP)

    def test_asymptotically_ibm(self):
        """For driftspeed==0, it coincides with the IBM prior."""
        ioup_speed0 = pnfs.statespace.IOUP(2, 3, driftspeed=0.0, diffconst=1.2345)

        ibm = pnfs.statespace.IBM(2, 3, diffconst=1.2345)
        self.assertAllClose(ioup_speed0.driftmat, ibm.driftmat)
        self.assertAllClose(ioup_speed0.forcevec, ibm.forcevec)
        self.assertAllClose(ioup_speed0.dispmat, ibm.dispmat)

        mean, cov = np.ones(ibm.dimension), np.eye(ibm.dimension)
        rv = pnrv.Normal(mean, cov)
        ibm_out, _ = ibm.transition_rv(rv, start=0.0, stop=STEP)
        ioup_out, _ = ioup_speed0.transition_rv(rv, start=0.0, stop=STEP)
        self.assertAllClose(ibm_out.mean, ioup_out.mean)
        self.assertAllClose(ibm_out.cov, ioup_out.cov)

        real = rv.sample()
        ibm_out, _ = ibm.transition_realization(real, start=0.0, stop=STEP)
        ioup_out, _ = ioup_speed0.transition_realization(real, start=0.0, stop=STEP)
        self.assertAllClose(ibm_out.mean, ioup_out.mean)
        self.assertAllClose(ibm_out.cov, ioup_out.cov)


class TestMatern(unittest.TestCase, NumpyAssertions):
    """Test whether coefficients for q=1, 2 match closed form.

    ... and whether coefficients for q=0 are Ornstein Uhlenbeck.
    """

    def setUp(self):
        lenscale, diffconst = np.random.rand(), np.random.rand()
        self.mat0 = pnfs.statespace.Matern(0, 1, lenscale, diffconst)
        self.mat1 = pnfs.statespace.Matern(1, 1, lenscale, diffconst)
        self.mat2 = pnfs.statespace.Matern(2, 1, lenscale, diffconst)

    def test_n0(self):
        """Closed form solution for ordint=0.

        This is the OUP.
        """
        xi = np.sqrt(2 * (self.mat0.dimension - 0.5)) / self.mat0.lengthscale
        self.assertAlmostEqual(self.mat0.driftmat[0, 0], -xi)

    def test_n1(self):
        """Closed form solution for ordint=1."""
        xi = np.sqrt(2 * (self.mat1.dimension - 0.5)) / self.mat1.lengthscale
        expected = np.array([-(xi ** 2), -2 * xi])
        self.assertAllClose(self.mat1.driftmat[-1, :], expected)

    def test_n2(self):
        """Closed form solution for n=2."""
        xi = np.sqrt(2 * (self.mat2.dimension - 0.5)) / self.mat2.lengthscale
        expected = np.array([-(xi ** 3), -3 * xi ** 2, -3 * xi])
        self.assertAllClose(self.mat2.driftmat[-1, :], expected)

    def test_larger_shape(self):
        mat2d = pnfs.statespace.Matern(2, 2, 1.0, 1.0)
        self.assertEqual(mat2d.dimension, 2 * (2 + 1))

    def test_transition_rv(self):
        mean, cov = np.ones(self.mat1.dimension), np.eye(self.mat1.dimension)
        initrv = pnrv.Normal(mean, cov)
        self.mat1.transition_rv(initrv, start=0.0, stop=STEP)

    def test_transition_real(self):
        mean, cov = np.ones(self.mat1.dimension), np.eye(self.mat1.dimension)
        real = pnrv.Normal(mean, cov).sample()
        self.mat1.transition_realization(real, start=0.0, stop=STEP)


if __name__ == "__main__":
    unittest.main()
