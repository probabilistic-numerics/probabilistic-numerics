"""Tests for SuiteSparse matrices and related functions."""
import pathlib

import scipy.sparse

from probnum.problems.zoo.linalg import SuiteSparseMatrix


def test_downloaded_matrix_is_sparse(suitesparse_mat: SuiteSparseMatrix):
    """Test whether a sparse scipy matrix is returned."""
    assert isinstance(suitesparse_mat.matrix, scipy.sparse.spmatrix)


def test_serialize_deserialize(
    suitesparse_mat: SuiteSparseMatrix, tmpdir: pathlib.Path
):
    """Test whether serializing and deserializing returns the same object."""
    pass


def test_attribute_parsing(suitesparse_mycielskian: SuiteSparseMatrix):
    """Test whether the attributes listed on the SuiteSparse Matrix Collection site are
    parsed correctly."""
    assert suitesparse_mycielskian.matid == "2759"
    assert suitesparse_mycielskian.group == "Mycielski"
    assert suitesparse_mycielskian.name == "mycielskian3"
    assert suitesparse_mycielskian.shape == (5, 5)
    assert suitesparse_mycielskian.nnz == 10
    assert not suitesparse_mycielskian.isspd
    assert suitesparse_mycielskian.psym == 1.0
    assert suitesparse_mycielskian.nsym == 1.0


def test_html_representation_returns_string(suitesparse_mat: SuiteSparseMatrix):
    """Test whether the HTML representation of a SuiteSparse Matrix returns a string."""
    assert isinstance(suitesparse_mat._repr_html_(), str)
