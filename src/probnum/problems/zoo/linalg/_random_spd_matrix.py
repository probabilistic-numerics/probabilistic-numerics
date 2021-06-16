"""Random symmetric positive definite matrices."""

from typing import Sequence

import numpy as np
import scipy.stats

from probnum.type import IntArgType


def random_spd_matrix(
    rng: np.random.Generator,
    dim: IntArgType,
    spectrum: Sequence = None,
) -> np.ndarray:
    """Random symmetric positive definite matrix.

    Constructs a random symmetric positive definite matrix from a given spectrum. An
    orthogonal matrix :math:`Q` with :math:`\\operatorname{det}(Q)` (a rotation) is
    sampled with respect to the Haar measure and the diagonal matrix
    containing the eigenvalues is rotated accordingly resulting in :math:`A=Q
    \\operatorname{diag}(\\lambda_1, \\dots, \\lambda_n)Q^\\top`. If no spectrum is
    provided, one is randomly drawn from a Gamma distribution.

    Parameters
    ----------
    rng
        Random number generator.
    dim
        Matrix dimension.
    spectrum
        Eigenvalues of the matrix.

    See Also
    --------
    random_sparse_spd_matrix : Generate a random sparse symmetric positive definite matrix.

    Examples
    --------
    >>> from probnum.problems.zoo.linalg import random_spd_matrix
    >>> import numpy as np
    >>> rng = np.random.default_rng(1)
    >>> mat = random_spd_matrix(rng, dim=5)
    >>> mat
    array([[10.24394619,  0.05484236,  0.39575826, -0.70032495, -0.75482692],
           [ 0.05484236, 11.31516868,  0.6968935 , -0.13877394,  0.52783063],
           [ 0.39575826,  0.6968935 , 11.5728974 ,  0.21214568,  1.07692458],
           [-0.70032495, -0.13877394,  0.21214568,  9.88674751, -1.09750511],
           [-0.75482692,  0.52783063,  1.07692458, -1.09750511, 10.193655  ]])

    Check for symmetry and positive definiteness.

    >>> np.all(mat == mat.T)
    True
    >>> np.linalg.eigvals(mat)
    array([ 8.09147328, 12.7635956 , 10.84504988, 10.73086331, 10.78143272])
    """

    # Initialization
    if spectrum is None:
        # Create a custom ordered spectrum if none is given.
        spectrum_shape: float = 10.0
        spectrum_scale: float = 1.0
        spectrum_offset: float = 0.0

        spectrum = scipy.stats.gamma.rvs(
            spectrum_shape,
            loc=spectrum_offset,
            scale=spectrum_scale,
            size=dim,
            random_state=rng,
        )
        spectrum = np.sort(spectrum)[::-1]

    else:
        spectrum = np.asarray(spectrum)
        if not np.all(spectrum > 0):
            raise ValueError(f"Eigenvalues must be positive, but are {spectrum}.")

    # Early exit for d=1 -- special_ortho_group does not like this case.
    if dim == 1:
        return spectrum.reshape((1, 1))

    # Draw orthogonal matrix with respect to the Haar measure
    orth_mat = scipy.stats.special_ortho_group.rvs(dim, random_state=rng)
    spd_mat = orth_mat @ np.diag(spectrum) @ orth_mat.T

    # Symmetrize to avoid numerically not symmetric matrix
    # Since A commutes with itself (AA' = A'A = AA) the eigenvalues do not change.
    return 0.5 * (spd_mat + spd_mat.T)


def random_sparse_spd_matrix(
    rng: np.random.Generator,
    dim: IntArgType,
    density: float,
    chol_entry_min: float = 0.1,
    chol_entry_max: float = 1.0,
) -> np.ndarray:
    """Random sparse symmetric positive definite matrix.

    Constructs a random sparse symmetric positive definite matrix for a given degree
    of sparsity. The matrix is constructed from its Cholesky factor :math:`L`. Its
    diagonal is set to one and all other entries of the lower triangle are sampled
    from a uniform distribution with bounds :code:`[chol_entry_min, chol_entry_max]`.
    The resulting sparse matrix is then given by :math:`A=LL^\\top`.

    Parameters
    ----------
    rng
        Random number generator.
    dim
        Matrix dimension.
    density
        Degree of sparsity of the off-diagonal entries of the Cholesky factor.
        Between 0 and 1 where 1 represents a dense matrix.
    chol_entry_min
        Lower bound on the entries of the Cholesky factor.
    chol_entry_max
        Upper bound on the entries of the Cholesky factor.

    See Also
    --------
    random_spd_matrix : Generate a random symmetric positive definite matrix.

    Examples
    --------
    >>> from probnum.problems.zoo.linalg import random_sparse_spd_matrix
    >>> import numpy as np
    >>> rng = np.random.default_rng(42)
    >>> sparsemat = random_sparse_spd_matrix(rng, dim=5, density=0.1)
    >>> sparsemat
    array([[1.        , 0.4949906 , 0.        , 0.        , 0.        ],
           [0.4949906 , 1.24501569, 0.        , 0.        , 0.        ],
           [0.        , 0.        , 1.        , 0.        , 0.        ],
           [0.        , 0.        , 0.        , 1.        , 0.        ],
           [0.        , 0.        , 0.        , 0.        , 1.        ]])
    """

    # Initialization
    if not 0 <= density <= 1:
        raise ValueError(f"Density must be between 0 and 1, but is {density}.")
    chol = np.eye(dim)
    num_off_diag_cholesky = int(0.5 * dim * (dim - 1))
    num_nonzero_entries = int(num_off_diag_cholesky * density)

    if num_nonzero_entries > 0:
        # Draw entries of lower triangle (below diagonal) according to sparsity level
        entry_ids = np.mask_indices(n=dim, mask_func=np.tril, k=-1)
        idx_samples = rng.choice(
            a=num_off_diag_cholesky, size=num_nonzero_entries, replace=False
        )
        nonzero_entry_ids = (entry_ids[0][idx_samples], entry_ids[1][idx_samples])

        # Fill Cholesky factor
        chol[nonzero_entry_ids] = rng.uniform(
            low=chol_entry_min, high=chol_entry_max, size=num_nonzero_entries
        )

    return chol @ chol.T
