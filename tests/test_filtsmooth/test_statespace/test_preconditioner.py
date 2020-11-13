import abc
import unittest

import numpy as np

import probnum.filtsmooth as pnfs
from tests.testing import NumpyAssertions


class TestPreconditioner(abc.ABC):

    precon = NotImplemented

    @abc.abstractmethod
    def test_call(self):
        raise NotImplementedError

    def test_inverse(self):
        raise NotImplementedError

    def test_call(self):
        P = self.precon(step=0.5)
        self.assertEqual(P.ndim, 2)
        self.assertEqual(P.shape[0], (self.some_order + 1) * self.some_dim)
        self.assertEqual(P.shape[1], (self.some_order + 1) * self.some_dim)

    def test_inverse(self):
        P = self.precon(step=0.5)
        Pinv = self.precon.inverse(step=0.5)
        self.assertAllClose(P @ Pinv, np.eye(*P.shape), rtol=1e-15, atol=0.0)
        self.assertAllClose(Pinv @ P, np.eye(*P.shape), rtol=1e-15, atol=0.0)


class TestNordsieckCoordinates(abc.ABC, unittest.TestCase, NumpyAssertions):
    def setUp(self):
        self.some_order = 3
        self.some_dim = 1
        self.precon = pnfs.statespace.NordsieckCoordinates.from_order(
            self.some_order, self.some_dim
        )


class TestTaylorCoordinates(abc.ABC, unittest.TestCase, NumpyAssertions):
    def setUp(self):
        self.some_order = 3
        self.some_dim = 1
        self.precon = pnfs.statespace.TaylorCoordinates.from_order(
            self.some_order, self.some_dim
        )


if __name__ == "__main__":
    unittest.main()
