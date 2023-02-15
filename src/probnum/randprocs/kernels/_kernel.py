"""Kernel / covariance function."""

from __future__ import annotations

import abc
import functools
import operator
from typing import Optional, Union

import numpy as np

from probnum import linops, utils as _pn_utils
from probnum.typing import ArrayLike, ScalarLike, ShapeLike, ShapeType

BinaryOperandType = Union["Kernel", ScalarLike]


class Kernel(abc.ABC):
    r"""(Cross-)covariance function(s)

    Abstract base class representing one or multiple (cross-)covariance function(s),
    also known as kernels.
    A cross-covariance function

    .. math::
        :nowrap:

        \begin{equation}
            k_{fg} \colon
            \mathcal{X}^{d_\text{in}} \times \mathcal{X}^{d_\text{in}}
            \to \mathbb{R}
        \end{equation}

    is a function of two arguments :math:`x_0` and :math:`x_1`, which represents the
    covariance between two evaluations :math:`f(x_0)` and :math:`g(x_1)` of two
    scalar-valued random processes :math:`f` and :math:`g` on a common probability space
    (or, equivalently, two outputs :math:`h_i(x_0)` and :math:`h_j(x_1)` of a
    vector-valued random process :math:`h`).
    If :math:`f = g`, then the cross-covariance function is also referred to as a
    covariance function, in which case it must be symmetric and positive
    (semi-)definite.

    An instance of a :class:`Kernel` can compute multiple different (cross-)covariance
    functions on the same pair of inputs simultaneously. For instance, it can be used to
    compute the full covariance matrix

    .. math::
        :nowrap:

        \begin{equation}
            C^f \colon
            \mathcal{X}^{d_\text{in}} \times \mathcal{X}^{d_\text{in}}
            \to \mathbb{R}^{d_\text{out} \times d_\text{out}},
            C^f_{i j}(x_0, x_1) := k_{f_i f_j}(x_0, x_1)
        \end{equation}

    of the vector-valued random process :math:`f`. To this end, we understand any
    :class:`Kernel` as a tensor whose shape is given by :attr:`output_shape`, which
    contains different (cross-)covariance functions as its entries.

    Parameters
    ----------
    input_shape
        Shape of the :class:`Kernel`'s input.
    output_shape
        Shape of the :class:`Kernel`'s output.

        If ``output_shape`` is set to ``()``, the :class:`Kernel` instance represents a
        single (cross-)covariance function. Otherwise, i.e. if ``output_shape`` is a
        non-empty tuple, the :class:`Kernel` instance represents a tensor of
        (cross-)covariance functions whose shape is given by ``output_shape``.

    Examples
    --------

    >>> from probnum.randprocs.kernels import Linear
    >>> D = 3
    >>> k = Linear(input_shape=D)
    >>> k.input_shape
    (3,)
    >>> k.output_shape
    ()

    Generate some input data.

    >>> N = 4
    >>> xs = np.linspace(0, 1, N * D).reshape(N, D)
    >>> xs.shape
    (4, 3)
    >>> xs
    array([[0.        , 0.09090909, 0.18181818],
           [0.27272727, 0.36363636, 0.45454545],
           [0.54545455, 0.63636364, 0.72727273],
           [0.81818182, 0.90909091, 1.        ]])

    We can compute kernel matrices like so.

    >>> k.matrix(xs)
    array([[0.04132231, 0.11570248, 0.19008264, 0.26446281],
           [0.11570248, 0.41322314, 0.7107438 , 1.00826446],
           [0.19008264, 0.7107438 , 1.23140496, 1.75206612],
           [0.26446281, 1.00826446, 1.75206612, 2.49586777]])

    The :meth:`Kernel.__call__` evaluations are vectorized over the "batch shapes" of
    the inputs, applying standard NumPy broadcasting.

    >>> k(xs[:, None], xs[None, :])  # same as `.matrix`
    array([[0.04132231, 0.11570248, 0.19008264, 0.26446281],
           [0.11570248, 0.41322314, 0.7107438 , 1.00826446],
           [0.19008264, 0.7107438 , 1.23140496, 1.75206612],
           [0.26446281, 1.00826446, 1.75206612, 2.49586777]])

    No broadcasting is applied if both inputs have the same shape. For instance, one can
    efficiently compute just the diagonal of the kernel matrix via

    >>> k(xs, xs)
    array([0.04132231, 0.41322314, 1.23140496, 2.49586777])
    >>> k(xs, None)  # x1 = None is an efficient way to set x1 == x0
    array([0.04132231, 0.41322314, 1.23140496, 2.49586777])

    and the diagonal above the main diagonal of the kernel matrix is retrieved through

    >>> k(xs[:-1, :], xs[1:, :])
    array([0.11570248, 0.7107438 , 1.75206612])

    Kernels support basic arithmetic operations. For example we can add noise to the
    kernel in the following fashion.

    >>> from probnum.randprocs.kernels import WhiteNoise
    >>> k_noise = k + 0.1 * WhiteNoise(input_shape=D)
    >>> k_noise.matrix(xs)
    array([[0.14132231, 0.11570248, 0.19008264, 0.26446281],
           [0.11570248, 0.51322314, 0.7107438 , 1.00826446],
           [0.19008264, 0.7107438 , 1.33140496, 1.75206612],
           [0.26446281, 1.00826446, 1.75206612, 2.59586777]])
    """

    def __init__(
        self,
        input_shape: ShapeLike,
        output0_shape: ShapeLike = (),
        output1_shape: ShapeLike = (),
    ):
        self._input_shape = _pn_utils.as_shape(input_shape)

        if self.input_ndim > 1:
            raise ValueError(
                "Currently, we only support kernels with at most 1 input dimension."
            )

        self._output0_shape = _pn_utils.as_shape(output0_shape)
        self._output1_shape = _pn_utils.as_shape(output1_shape)

    @property
    def input_shape(self) -> ShapeType:
        """Shape of single, i.e. non-batched, arguments of the covariance function."""
        return self._input_shape

    @property
    def input_ndim(self) -> int:
        """Syntactic sugar for ``len(input_shape)``."""
        return len(self._input_shape)

    @functools.cached_property
    def input_size(self) -> int:
        """Syntactic sugar for the product over the input size."""
        return functools.reduce(operator.mul, self.input_shape, 1)

    @property
    def output0_shape(self) -> ShapeType:
        """Shape of single, i.e. non-batched, return values of the covariance function.

        If :attr:`output_shape` is ``()``, the :class:`Kernel` instance represents a
        single (cross-)covariance function. Otherwise, i.e. if :attr:`output_shape` is
        non-empty, the :class:`Kernel` instance represents a tensor of
        (cross-)covariance functions whose shape is given by ``output_shape``.
        """
        return self._output0_shape

    @property
    def output0_ndim(self) -> int:
        """Syntactic sugar for ``len(output0_shape)``."""
        return len(self.output0_shape)

    @functools.cached_property
    def output0_size(self) -> int:
        """Syntactic sugar for the product over :attr:`output0_shape`."""
        return functools.reduce(operator.mul, self.output0_shape, 1)

    @property
    def output1_shape(self) -> ShapeType:
        return self._output1_shape

    @property
    def output1_ndim(self) -> int:
        """Syntactic sugar for ``len(output1_shape)``."""
        return len(self.output1_shape)

    @functools.cached_property
    def output1_size(self) -> int:
        """Syntactic sugar for the product over :attr:`output1_shape`."""
        return functools.reduce(operator.mul, self.output1_shape, 1)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} with"
            f" input_shape={self.input_shape},"
            f" output0_shape={self.output0_shape}, and"
            f" output1_shape={self.output1_shape}>"
        )

    def __call__(
        self,
        x0: ArrayLike,
        x1: Optional[ArrayLike],
    ) -> np.ndarray:
        """Evaluate the (cross-)covariance function(s).

        The evaluation of the (cross-covariance) function(s) is vectorized over the
        batch shapes of the arguments, applying standard NumPy broadcasting.

        Parameters
        ----------
        x0
            *shape=* ``batch_shape_0 +`` :attr:`input_shape` -- (Batch of) input(s)
            for the first argument of the :class:`Kernel`.
        x1
            *shape=* ``batch_shape_1 +`` :attr:`input_shape` -- (Batch of) input(s)
            for the second argument of the :class:`Kernel`.
            Can also be set to ``None``, in which case the function will behave as if
            ``x1 = x0`` (but it is implemented more efficiently).

        Returns
        -------
        k_x0_x1 :
            *shape=* ``bcast_batch_shape +`` :attr:`output_shape` -- The
            (cross-)covariance function(s) evaluated at ``(x0, x1)``.
            Since the function is vectorized over the batch shapes of the inputs, the
            output array contains the following entries:

            .. code-block:: python

                k_x0_x1[batch_idx + output_idx] = k[output_idx](
                    x0[batch_idx, ...],
                    x1[batch_idx, ...],
                )

            where we assume that ``x0`` and ``x1`` have been broadcast to a common
            shape ``bcast_batch_shape +`` :attr:`input_shape`, and where ``output_idx``
            and ``batch_idx`` are indices compatible with :attr:`output_shape` and
            ``bcast_batch_shape``, respectively.
            By ``k[output_idx]`` we refer to the covariance function at index
            ``output_idx`` in the tensor of covariance functions represented by the
            :class:`Kernel` instance.

        Raises
        ------
        ValueError
            If one of the input shapes is not of the form ``batch_shape_{0,1} +``
            :attr:`input_shape`.
        ValueError
            If the inputs can not be broadcast to a common shape.

        See Also
        --------
        matrix: Convenience function to compute a kernel matrix, i.e. a matrix of
            pairwise evaluations of the kernel on two sets of points.

        Examples
        --------
        See documentation of class :class:`Kernel`.
        """

        x0 = np.asarray(x0)

        if x1 is not None:
            x1 = np.asarray(x1)

        # Shape checking
        broadcast_batch_shape = self._check_shapes(
            x0.shape, x1.shape if x1 is not None else None
        )

        # Evaluate the kernel
        k_x0_x1 = self._evaluate(x0, x1)

        assert (
            k_x0_x1.shape
            == broadcast_batch_shape + self._output0_shape + self._output1_shape
        )

        return k_x0_x1

    def matrix(
        self,
        x0: ArrayLike,
        x1: Optional[ArrayLike] = None,
    ) -> np.ndarray:
        """Kernel matrix corresponding to the given input points.

        Parameters
        ----------
        x0
            *shape=* ``batch_shape_0 +`` :attr:`input_shape` -- (Batch of) input(s) for
            the first argument of the :class:`Kernel`.
        x1
            *shape=* ``batch_shape_1 +`` :attr:`input_shape` -- (Batch of) input(s) for
            the second argument of the :class:`Kernel`.
            Can also be set to :data:`None`, in which case the function will behave as
            if ``x1 == x0`` (potentially using a more efficient implementation for this
            particular case).

        Returns
        -------
        k_x0_x1
            *shape=* ``(``:attr:`output0_size` ``* N0,`` :attr:`output1_size` ``* N1)``
            *with* ``N0 = prod(batch_shape_0)`` and ``N1 = prod(batch_shape_1)`` --
            The kernel matrix corresponding to the given batches of input points.
            The order of the rows and columns of the kernel matrix corresponds to the
            order of entries obtained by flattening :class:`~numpy.ndarray`\\ s with
            shapes :attr:`output0_shape` ``+ batch_shape_0`` and :attr:`output0_shape`
            ``+ batch_shape_1`` in "C-order".

        Raises
        ------
        ValueError
            If the shape of either input is not of the form ``batch_shape_0 +``
            :attr:`input_shape`.
        """
        x0 = self._preprocess_linop_input(x0, argname="x0")

        if x1 is not None:
            x1 = self._preprocess_linop_input(x1, argname="x1")

        k_matrix_x0_x1 = self._evaluate_matrix(x0, x1)

        assert isinstance(k_matrix_x0_x1, np.ndarray)
        assert k_matrix_x0_x1.shape == (
            self.output0_size * x0.shape[0],
            self.output1_size * (x1.shape[0] if x1 is not None else x0.shape[0]),
        )

        return k_matrix_x0_x1

    def linop(
        self,
        x0: ArrayLike,
        x1: Optional[ArrayLike] = None,
    ) -> linops.LinearOperator:
        """:class:`LinearOperator` representing the kernel matrix corresponding to the
        given input points.

        Representing a kernel matrix as a matrix-free :class:`LinearOperator` is often
        more efficient than computing a dense kernel matrix, both in terms of memory and
        computation time, particularly when using iterative methods to solve the
        associated linear systems.

        For instance, kernel matrices for separable kernels (e.g. tensor product
        kernels or separable multi-output kernels) can often be represented as
        :class:`linops.KroneckerProduct`\\ s of smaller kernel matrices and frameworks
        like :mod:`pykeops<pykeops.numpy>` can be used to implement efficient
        matrix-vector products with kernel matrices without needing to construct the
        entire kernel matrix in memory.

        Parameters
        ----------
        x0
            *shape=* ``batch_shape_0 +`` :attr:`input_shape` -- (Batch of) input(s) for
            the first argument of the :class:`Kernel`.
        x1
            *shape=* ``batch_shape_1 +`` :attr:`input_shape` -- (Batch of) input(s) for
            the second argument of the :class:`Kernel`.
            Can also be set to :data:`None`, in which case the function will behave as
            if ``x1 == x0`` (potentially using a more efficient implementation for this
            particular case).

        Returns
        -------
        k_x0_x1
            *shape=* ``(``:attr:`output0_size` ``* N0,`` :attr:`output1_size` ``* N1)``
            *with* ``N0 = prod(batch_shape_0)`` and ``N1 = prod(batch_shape_1)`` --
            :class:`LinearOperator` representing the kernel matrix corresponding to the
            given batches of input points.
            The order of the rows and columns of the kernel matrix corresponds to the
            order of entries obtained by flattening :class:`~numpy.ndarray`\\ s with
            shapes :attr:`output0_shape` ``+ batch_shape_0`` and :attr:`output0_shape`
            ``+ batch_shape_1`` in "C-order".

        Raises
        ------
        ValueError
            If the shape of either input is not of the form ``batch_shape_0 +``
            :attr:`input_shape`.
        """
        x0 = self._preprocess_linop_input(x0, argname="x0")

        if x1 is not None:
            x1 = self._preprocess_linop_input(x1, argname="x1")

        k_linop_x0_x1 = self._evaluate_linop(x0, x1)

        assert isinstance(k_linop_x0_x1, linops.LinearOperator)
        assert k_linop_x0_x1.shape == (
            self.output0_size * x0.shape[0],
            self.output1_size * (x1.shape[0] if x1 is not None else x0.shape[1]),
        )

        return k_linop_x0_x1

    @abc.abstractmethod
    def _evaluate(
        self,
        x0: np.ndarray,
        x1: Optional[np.ndarray],
    ) -> np.ndarray:
        """Implementation of the kernel evaluation which is called after input checking.

        When implementing a particular kernel, the subclass should implement the kernel
        computation by overwriting this method. It is called by the :meth:`__call__`
        method after applying input checking. The implementation must return the array
        described in the "Returns" section of the :meth:`__call__` method.
        Note that the inputs are not automatically broadcast to a common shape, but it
        is guaranteed that this is possible.

        Parameters
        ----------
        x0
            See argument ``x0`` in the docstring of :meth:`__call__`.
        x1
            See argument ``x1`` in the docstring of :meth:`__call__`.

        Returns
        -------
        k_x0_x1 :
            See "Returns" section in the docstring of :meth:`__call__`.
        """
        raise NotImplementedError

    def _evaluate_matrix(
        self,
        x0: np.ndarray,
        x1: Optional[np.ndarray],
    ) -> linops.LinearOperator:
        assert x0.ndim == 1 + self.input_shape
        assert x1 is None or x1.ndim == 1 + self.input_shape

        k_x0_x1 = self(x0[:, None, ...], (x1 if x1 is not None else x0)[None, :, ...])

        assert k_x0_x1.ndim == 2 + self.output0_ndim + self.output1_ndim

        batch_shape = k_x0_x1.shape[:2]

        assert k_x0_x1.shape == batch_shape + self.output0_shape + self.output1_shape

        cov_x0_x1 = np.moveaxis(k_x0_x1, 1, -1)
        cov_x0_x1 = np.moveaxis(cov_x0_x1, 0, 1 + self.output1_shape)

        assert cov_x0_x1.shape == self.output0_shape + (
            batch_shape[0],
        ) + self.output1_shape + (batch_shape[1],)

        return cov_x0_x1.reshape(
            (
                self.output0_size * batch_shape[0],
                self.output1_size * batch_shape[1],
            ),
            order="C",
        )

    def _evaluate_linop(
        self,
        x0: np.ndarray,
        x1: Optional[np.ndarray],
    ) -> linops.LinearOperator:
        return linops.Matrix(self._evaluate_matrix(x0, x1))

    def _check_shapes(
        self,
        x0_shape: ShapeType,
        x1_shape: Optional[ShapeType] = None,
    ) -> ShapeType:
        """Checks input argument shapes and computes the broadcast batch shape of both
        inputs.

        This function checks the shapes of the inputs to the :meth:`__call__` method and
        it computes the `bcast_batch_shape` mentioned in the docstring.

        Parameters
        ----------
        x0_shape :
            Shape of the first input to the covariance function.
        x1_shape :
            Shape of the (optional) second input to the covariance function.

        Returns
        -------
        broadcast_batch_shape :
            The `batch_shape` after broadcasting the inputs to a common shape.

        Raises
        -------
        ValueError
            If one of the input shapes is not of the form ``batch_shape_{0,1} +``
            :attr:`input_shape`.
        ValueError
            If the inputs can not be broadcast to a common shape.
        """

        err_msg = (
            "The shape of the input array `{argname}` must match the `input_shape` "
            f"`{self.input_shape}` of the kernel along its last dimension, but an "
            "array with shape `{shape}` was given."
        )

        if x0_shape[len(x0_shape) - self.input_ndim :] != self.input_shape:
            raise ValueError(err_msg.format(argname="x0", shape=x0_shape))

        broadcast_batch_shape = x0_shape[: len(x0_shape) - self.input_ndim]

        if x1_shape is not None:
            if x1_shape[len(x1_shape) - self.input_ndim :] != self.input_shape:
                raise ValueError(err_msg.format(argname="x1", shape=x1_shape))

            try:
                broadcast_batch_shape = np.broadcast_shapes(
                    broadcast_batch_shape,
                    x1_shape[: len(x1_shape) - self.input_ndim],
                )
            except ValueError as ve:
                err_msg = (
                    f"The input arrays `x0` and `x1` with shapes {x0_shape} and "
                    f"{x1_shape} can not be broadcast to a common shape."
                )
                raise ValueError(err_msg) from ve

        return broadcast_batch_shape

    def _preprocess_linop_input(self, x: ArrayLike, argname: str) -> np.ndarray:
        x = np.asarray(x)

        if not (
            x.ndim >= self.input_ndim
            and x.shape[(x.ndim - self.input_ndim) :] == self.input_shape
        ):
            raise ValueError(
                f"The shape of `{argname}` must must match the input shape "
                f"`{self.input_shape}` of the kernel along its trailing dimensions, "
                f"but an array with shape `{x.shape}` was given."
            )

        return x.reshape((-1,) + self.input_shape, order="C")

    def _euclidean_inner_products(
        self, x0: np.ndarray, x1: Optional[np.ndarray]
    ) -> np.ndarray:
        """Implementation of the Euclidean inner product, which supports scalar inputs
        and an optional second argument."""
        prods = x0**2 if x1 is None else x0 * x1

        if self.input_ndim == 0:
            return prods

        assert self.input_ndim == 1

        return np.sum(prods, axis=-1)

    ####################################################################################
    # Binary Arithmetic
    ####################################################################################

    __array_ufunc__ = None
    """
    This prevents numpy from calling elementwise arithmetic operations instead of
    the arithmetic operations defined by `Kernel`.
    """

    def __add__(self, other: BinaryOperandType) -> Kernel:
        from ._arithmetic import add  # pylint: disable=import-outside-toplevel

        return add(self, other)

    def __radd__(self, other: BinaryOperandType) -> Kernel:
        from ._arithmetic import add  # pylint: disable=import-outside-toplevel

        return add(other, self)

    def __mul__(self, other: BinaryOperandType) -> Kernel:
        from ._arithmetic import mul  # pylint: disable=import-outside-toplevel

        return mul(self, other)

    def __rmul__(self, other: BinaryOperandType) -> Kernel:
        from ._arithmetic import mul  # pylint: disable=import-outside-toplevel

        return mul(other, self)


class IsotropicMixin(abc.ABC):  # pylint: disable=too-few-public-methods
    r"""Mixin for isotropic kernels.

    An isotropic kernel is a kernel which only depends on the norm of the difference of
    the arguments, i.e.

    .. math ::

        k(x_0, x_1) = k(\lVert x_0 - x_1 \rVert).

    Hence, all isotropic kernels are stationary.
    """

    def _squared_euclidean_distances(
        self,
        x0: np.ndarray,
        x1: Optional[np.ndarray],
        *,
        scale_factors: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Implementation of the squared (modified) Euclidean distance, which supports
        scalar inputs, an optional second argument, and separate scale factors for each
        input dimension."""

        if x1 is None:
            return np.zeros_like(  # pylint: disable=unexpected-keyword-arg
                x0,
                shape=x0.shape[: x0.ndim - self.input_ndim],
            )

        sqdiffs = x0 - x1

        if scale_factors is not None:
            sqdiffs *= scale_factors

        sqdiffs *= sqdiffs

        return np.sum(sqdiffs, axis=tuple(range(-self.input_ndim, 0)))

    def _euclidean_distances(
        self,
        x0: np.ndarray,
        x1: Optional[np.ndarray],
        *,
        scale_factors: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Implementation of the (modified) Euclidean distance, which supports scalar
        inputs, an optional second argument, and separate scale factors for each input
        dimension."""

        if x1 is None:
            return np.zeros_like(  # pylint: disable=unexpected-keyword-arg
                x0,
                shape=x0.shape[: x0.ndim - self.input_ndim],
            )

        return np.sqrt(
            self._squared_euclidean_distances(x0, x1, scale_factors=scale_factors)
        )
