"""White noise kernel."""

from typing import Optional

import numpy as np

import probnum.utils as _utils
from probnum.typing import IntArgType, ScalarArgType

from ._kernel import Kernel

_InputType = np.ndarray


class WhiteNoise(Kernel):
    """White noise kernel.

    Kernel representing independent and identically distributed white noise :math:`k(
    x_0, x_1) = \\sigma^2 \\delta(x_0, x_1)`.

    Parameters
    ----------
    input_dim :
        Input dimension of the kernel.
    sigma :
        Noise level.
    """

    def __init__(self, input_dim: IntArgType, sigma: ScalarArgType = 1.0):
        self.sigma = _utils.as_numpy_scalar(sigma)
        self._sigma_sq = self.sigma ** 2
        super().__init__(input_dim=input_dim, output_dim=None)

    def _evaluate(self, x0: _InputType, x1: Optional[_InputType] = None) -> np.ndarray:
        if x1 is None:
            return np.full_like(x0[..., 0], self._sigma_sq)

        return self._sigma_sq * np.all(x0 == x1, axis=-1)
