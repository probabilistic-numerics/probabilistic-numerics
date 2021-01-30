# """Iterated Gaussian filtering and smoothing."""
# import numpy as np
#
# import probnum.random_variables as pnrv
#
# from .kalman import Kalman
# from .stoppingcriterion import StoppingCriterion
#
#
# class IteratedKalman(Kalman):
#     """Iterated Gaussian filter/smoother based on posterior linearisation."""
#
#     def __init__(self, kalman, stopcrit=None):
#         self.kalman = kalman
#         if stopcrit is None:
#             self.stopcrit = StoppingCriterion()
#         else:
#             self.stopcrit = stopcrit
#
#         super().__init__(kalman.dynamics_model, kalman.measurement_model, kalman.initrv)
#
#     def iterated_filtsmooth(self, dataset, times, _intermediate_step=None):
#         """Compute an iterated smoothing estimate with posterior linearisation.
#
#         If the extended Kalman filter is used, this yields the IEKS. In
#         any case, the result is an approximation to the maximum-a-
#         posteriori estimate.
#         """
#         old_posterior = self.filtsmooth(
#             dataset=dataset,
#             times=times,
#             _intermediate_step=_intermediate_step,
#             _previous_posterior=None,
#         )
#         new_posterior = old_posterior
#
#         normalised_error = np.inf
#
#         while normalised_error > 1:
#             old_posterior = new_posterior
#             new_posterior = self.filtsmooth(
#                 dataset=dataset,
#                 times=times,
#                 _intermediate_step=_intermediate_step,
#                 _previous_posterior=old_posterior,
#             )
#             difference = new_posterior.state_rvs.mean - old_posterior.state_rvs.mean
#             reference = old_posterior.state_rvs.mean
#             normalised_error = self.stopcrit.evaluate_error(difference, reference)
#         return new_posterior
