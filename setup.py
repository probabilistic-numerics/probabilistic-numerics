# -*- coding: utf-8 -*-
"""Setup file for probnum.

Use setup.cfg to configure the project.
"""
from setuptools import setup

# TODO (pypa/setuptools#3221): Migrate this to `[project.optional-dependencies]` in
# `pyproject.toml`, once optional dependencies defined there can reference one another
extras_require = dict()
extras_require["jax"] = [
    "jax[cpu]<0.4.27; platform_system!='Windows'",
]
extras_require["zoo"] = [
    "tqdm>=4.0",
    "requests>=2.0",
] + extras_require["jax"]
extras_require["keops"] = ["pykeops>=2.1.1,<3.0"]
extras_require["full"] = (
    extras_require["jax"] + extras_require["zoo"] + extras_require["keops"]
)


if __name__ == "__main__":
    setup(
        extras_require=extras_require,
    )
