"""Test cases for `Kernel.__call__`."""

from typing import Callable, Optional, Tuple

import pytest

from probnum import backend, compat
from probnum.backend.typing import ShapeType
from probnum.randprocs import kernels
import tests.utils


@pytest.fixture(
    params=[
        pytest.param(
            (x0_shape, x1_shape),
            id=(f"x0{x0_shape}-x1{x1_shape}"),
        )
        for x0_shape, x1_shape in [
            [(), None],
            [(), ()],
            [(), (1,)],
            [(), (3,)],
            [(1,), None],
            [(1,), ()],
            [(1,), (1,)],
            [(1,), (2,)],
            [(10,), None],
            [(10,), (1,)],
            [(10,), (10,)],
            [(30, 1), (9,)],
            [(1, 1), (1, 1)],
            [(10, 1), (10,)],
            [(10, 1), (1, 2)],
            [(100, 1), (10,)],
            [(100, 1), (1, 10)],
            [(2, 4, 1, 1, 3), (1, 4, 5, 1, 1)],
        ]
    ],
    name="input_shapes",
    scope="module",
)
def fixture_input_shapes(
    request, input_shape: ShapeType
) -> Tuple[ShapeType, Optional[ShapeType]]:
    """Shapes for the first and second argument of the covariance function.

    The second shape is ``None`` if the second argument to the covariance function is
    ``None``.
    """

    x0_shape, x1_shape = request.param

    return (
        x0_shape + input_shape,
        x1_shape + input_shape if x1_shape is not None else None,
    )


@pytest.fixture(name="x0", scope="module")
def fixture_x0(input_shapes: Tuple[ShapeType, Optional[ShapeType]]) -> backend.Array:
    """The first argument to the covariance function drawn from a standard normal
    distribution."""

    x0_shape, _ = input_shapes

    return backend.random.standard_normal(
        seed=tests.utils.random.seed_from_sampling_args(
            base_seed=899803, shape=x0_shape
        ),
        shape=x0_shape,
    )


@pytest.fixture(name="x1", scope="module")
def fixture_x1(
    input_shapes: Tuple[ShapeType, Optional[ShapeType]]
) -> Optional[backend.Array]:
    """The second argument to the covariance function drawn from a standard normal
    distribution."""

    _, x1_shape = input_shapes

    if x1_shape is None:
        return None

    return backend.random.standard_normal(
        seed=tests.utils.random.seed_from_sampling_args(base_seed=4569, shape=x1_shape),
        shape=x1_shape,
    )


@pytest.fixture(name="call_result", scope="module")
def fixture_call_result(
    kernel: kernels.Kernel, x0: backend.Array, x1: Optional[backend.Array]
) -> backend.Array:
    """Result of ``Kernel.__call__`` when given ``x0`` and ``x1``."""

    return kernel(x0, x1)


@pytest.fixture(name="call_result_naive", scope="module")
def fixture_call_result_naive(
    kernel_call_naive: Callable[
        [backend.Array, Optional[backend.Array]], backend.Array
    ],
    x0: backend.Array,
    x1: Optional[backend.Array],
) -> backend.Array:
    """Result of ``Kernel.__call__`` when applied to the entries of ``x0`` and ``x1`` in
    a loop."""

    return kernel_call_naive(x0, x1)


def test_type(call_result: backend.Array):
    """Test whether the type of the output of ``Kernel.__call__`` is an object of
    ``backend.Array``."""

    assert backend.isarray(call_result)


def test_shape(
    call_result: backend.Array,
    call_result_naive: backend.Array,
):
    """Test whether the shape of the output of ``Kernel.__call__`` matches the shape of
    the naive reference implementation."""

    assert call_result.shape == call_result_naive.shape


def test_values(
    call_result: backend.Array,
    call_result_naive: backend.Array,
):
    """Test whether the entries of the output of ``Kernel.__call__`` match the entries
    generated by the naive reference implementation."""

    compat.testing.assert_allclose(
        call_result,
        call_result_naive,
        rtol=10**-12,
        atol=10**-12,
    )


@pytest.mark.parametrize(
    "shape",
    [
        (),
        (1,),
        (10,),
        (1, 10),
        (4, 25),
    ],
)
def test_wrong_input_dimension(kernel: kernels.Kernel, shape: ShapeType):
    """Test whether passing an input with the wrong input dimension raises an error."""

    if kernel.input_ndim > 0:
        input_shape = shape + tuple(dim + 1 for dim in kernel.input_shape)

        with pytest.raises(ValueError):
            kernel(backend.zeros(input_shape), None)

        with pytest.raises(ValueError):
            kernel(backend.ones(input_shape), backend.zeros(shape + kernel.input_shape))

        with pytest.raises(ValueError):
            kernel(backend.ones(shape + kernel.input_shape), backend.zeros(input_shape))


@pytest.mark.parametrize(
    "x0_shape,x1_shape",
    [
        ((2,), (8,)),
        ((2, 5), (3, 5)),
        ((4, 4), (4, 2)),
    ],
)
def test_broadcasting_error(
    kernel: kernels.Kernel,
    x0_shape: backend.Array,
    x1_shape: backend.Array,
):
    """Test whether an error is raised if the inputs can not be broadcast to a common
    shape."""

    with pytest.raises(ValueError):
        kernel(
            backend.zeros(x0_shape + kernel.input_shape),
            backend.ones(x1_shape + kernel.input_shape),
        )
