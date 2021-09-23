"""Polynomial kernel."""

from typing import Optional

import numpy as np

import probnum.utils as _utils
from probnum.typing import IntArgType, ScalarArgType

from ._kernel import Kernel

_InputType = np.ndarray


class Polynomial(Kernel[_InputType]):
    """Polynomial kernel.

    Covariance function defined by :math:`k(x_0, x_1) = (x_0^\\top x_1 + c)^q`.

    Parameters
    ----------
    input_dim :
        Input dimension of the kernel.
    constant
        Constant offset :math:`c`.
    exponent
        Exponent :math:`q` of the polynomial.

    See Also
    --------
    Linear : Linear covariance function.

    Examples
    --------
    >>> import numpy as np
    >>> from probnum.kernels import Polynomial
    >>> K = Polynomial(input_dim=2, constant=1.0, exponent=3)
    >>> K(np.array([[1, -1], [-1, 0]]))
    array([[27.,  0.],
           [ 0.,  8.]])
    """

    def __init__(
        self,
        input_dim: IntArgType,
        constant: ScalarArgType = 0.0,
        exponent: IntArgType = 1.0,
    ):
        self.constant = _utils.as_numpy_scalar(constant)
        self.exponent = _utils.as_numpy_scalar(exponent)
        super().__init__(input_dim=input_dim, output_dim=1)

    def _evaluate(self, x0: _InputType, x1: Optional[_InputType] = None) -> np.ndarray:
        if x1 is None:
            x1 = x0

        kernmat = (np.sum(x0 * x1, axis=-1) + self.constant) ** self.exponent

        return kernmat[..., None, None]
