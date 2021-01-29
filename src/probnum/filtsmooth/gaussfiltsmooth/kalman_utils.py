"""Prediction, update, and smoothing implementations for the Kalman filter/smoother."""


# Prediction choices


def predict_via_transition(
    dynamics_model, start, stop, randvar, _intermediate_step=None, _diffusion=1.0
):
    pass


def predict_sqrt(
    dynamics_model, start, stop, randvar, _intermediate_step=None, _diffusion=1.0
):
    pass


# Measure choices


def measure_via_transition():
    pass


def measure_sqrt():
    pass


# Update choices


def update_classic(measurement_model, rv, time, data):
    pass


def update_joseph(measurement_model, rv, time, data):
    pass


def update_sqrt(measurement_model, rv, time, data):
    pass


def iterated_update_classic(measurement_model, rv, time, data):
    pass


def iterated_update_joseph(measurement_model, rv, time, data):
    pass


def iterated_update_sqrt(measurement_model, rv, time, data):
    pass


# Smoothing choices


def smooth_step_classic_with_precon():
    pass


def smooth_step_joseph_with_precon():
    pass


def smooth_step_sqrt_with_precon():
    pass


def smooth_step_classic():
    pass


def smooth_step_joseph():
    pass


def smooth_step_sqrt():
    pass
