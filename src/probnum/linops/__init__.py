"""Finite-dimensional Linear Operators."""

from ._diagonal import Diagonal, Identity, ScalarMult
from ._kronecker import Kronecker, SymmetricKronecker, Symmetrize
from ._linear_operator import LinearOperator, MatrixMult
from ._utils import aslinop

# Public classes and functions. Order is reflected in documentation.
__all__ = [
    "aslinop",
    "LinearOperator",
    "MatrixMult",
    "Diagonal",
    "ScalarMult",
    "Identity",
    "Kronecker",
    "SymmetricKronecker",
    "Symmetrize",
]

# Set correct module paths. Corrects links and module paths in documentation.
LinearOperator.__module__ = "probnum.linops"

MatrixMult.__module__ = "probnum.linops"

Diagonal.__module__ = "probnum.linops"
ScalarMult.__module__ = "probnum.linops"
Identity.__module__ = "probnum.linops"

Kronecker.__module__ = "probnum.linops"
SymmetricKronecker.__module__ = "probnum.linops"
Symmetrize.__module__ = "probnum.linops"

aslinop.__module__ = "probnum.linops"
