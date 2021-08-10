"""Test problems involving ordinary differential equations."""


from ._ivp_examples import (
    fitzhughnagumo,
    logistic,
    lorenz63,
    lotkavolterra,
    rigidbody,
    seir,
    threebody,
    vanderpol,
)
from ._ivp_examples_jax import threebody_jax, vanderpol_jax

# Public classes and functions. Order is reflected in documentation.
__all__ = [
    "logistic",
    "lotkavolterra",
    "fitzhughnagumo",
    "seir",
    "threebody",
    "vanderpol",
    "lorenz63",
    "rigidbody",
    "threebody_jax",
    "vanderpol_jax",
]
