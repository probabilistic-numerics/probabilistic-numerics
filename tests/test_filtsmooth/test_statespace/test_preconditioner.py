import abc
import unittest

import numpy as np
import pytest

from probnum.filtsmooth import statespace as pnfss

#         self.some_order = 3
#         self.some_dim = 1
#         self.precon = pnfs.statespace.NordsieckLikeCoordinates.from_order(
#             self.some_order, self.some_dim
#         )


@pytest.fixture
def precon():
    some_order = 3
    some_dim = 1
    return pnfss.NordsieckLikeCoordinates.from_order(some_order, some_dim)


def test_call(precon):
    P = precon(0.5)
    assert isinstance(P, np.ndarray)


def test_inverse(precon):
    P, Pinv = precon(0.5), precon.inverse(0.5)
    np.testing.assert_allclose(P @ Pinv, np.eye(*P.shape))
    np.testing.assert_allclose(Pinv @ P, np.eye(*P.shape))
