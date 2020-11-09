import unittest

import probnum.filtsmooth as pnfs

from . import filtsmooth_testcases as cases


class TestContinuousEKFComponent(unittest.TestCase):
    """Implementation incomplete, hence check that an error is raised."""

    def test_notimplementederror(self):
        sde = pnfs.statespace.SDE(None, None, None)  # content is irrelevant.
        with self.assertRaises(NotImplementedError):
            pnfs.ContinuousEKFComponent(sde, num_steps=1)


class TestDiscreteEKFComponent(cases.LinearisedDiscreteTransitionTestCase):
    def setUp(self):
        self.linearising_component_pendulum = pnfs.DiscreteEKFComponent
        self.linearising_component_car = pnfs.DiscreteEKFComponent
        self.visualise = False
