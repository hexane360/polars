from __future__ import annotations

import re

import pytest

import polars as pl
from polars.exceptions import InvalidOperationError
from polars.testing import assert_series_equal


def display_shape(shape: tuple[int, ...]) -> str:
    return "(" + ", ".join(tuple(str(d) if d >= 0 else "inferred" for d in shape)) + ")"


def test_reshape() -> None:
    s = pl.Series("a", [1, 2, 3, 4])
    out = s.reshape((-1, 2))
    expected = pl.Series("a", [[1, 2], [3, 4]], dtype=pl.Array(pl.Int64, 2))
    assert_series_equal(out, expected)
    out = s.reshape((2, 2))
    assert_series_equal(out, expected)
    out = s.reshape((2, -1))
    assert_series_equal(out, expected)

    out = s.reshape((-1, 1))
    expected = pl.Series("a", [[1], [2], [3], [4]], dtype=pl.Array(pl.Int64, 1))
    assert_series_equal(out, expected)
    out = s.reshape((4, -1))
    assert_series_equal(out, expected)
    out = s.reshape((4, 1))
    assert_series_equal(out, expected)

    # single dimension
    out = s.reshape((4,))
    assert_series_equal(out, s)
    out = s.reshape((-1,))
    assert_series_equal(out, s)

    # test lazy_dispatch
    out = pl.select(pl.lit(s).reshape((-1, 1))).to_series()
    assert_series_equal(out, expected)

    # invalid (empty) dimensions
    with pytest.raises(
        InvalidOperationError, match="at least one dimension must be specified"
    ):
        s.reshape(())


@pytest.mark.parametrize("shape", [(1, 3), (5, 1), (-1, 5), (3, -1)])
def test_reshape_invalid_dimension_size(shape: tuple[int, ...]) -> None:
    s = pl.Series("a", [1, 2, 3, 4])
    with pytest.raises(
        InvalidOperationError,
        match=re.escape(
            f"cannot reshape array of size 4 into shape {display_shape(shape)}"
        ),
    ):
        s.reshape(shape)


@pytest.mark.parametrize("shape", [(0, 5), (0, 1, -1)])
def test_reshape_invalid_into_empty(shape: tuple[int, ...]) -> None:
    s = pl.Series("a", [1, 2, 3, 4])
    with pytest.raises(
        InvalidOperationError,
        match=re.escape(
            f"cannot reshape non-empty array into shape containing a zero dimension: {display_shape(shape)}"
        ),
    ):
        s.reshape(shape)


@pytest.mark.parametrize("shape", [(0, 0), (-1, 0)])
def test_reshape_invalid_zero_dimension(shape: tuple[int, ...]) -> None:
    s = pl.Series("a", [1, 2, 3, 4])
    with pytest.raises(
        InvalidOperationError,
        match=re.escape(
            f"cannot reshape array into shape containing a zero dimension after the first: {display_shape(shape)}"
        ),
    ):
        s.reshape(shape)


@pytest.mark.parametrize("shape", [(-1, -1), (-1, -2), (-2, -2)])
def test_reshape_invalid_multiple_unknown_dims(shape: tuple[int, ...]) -> None:
    s = pl.Series("a", [1, 2, 3, 4])
    with pytest.raises(
        InvalidOperationError, match="can only specify one inferred dimension"
    ):
        s.reshape(shape)


@pytest.mark.parametrize("shape", [(0,), (-1,), (-2,)])
def test_reshape_empty_valid_1d(shape: tuple[int, ...]) -> None:
    s = pl.Series("a", [], dtype=pl.Int64)
    out = s.reshape(shape)
    assert_series_equal(out, s)


@pytest.mark.parametrize("shape", [(1, -1), (0, -2), (0, 3, -1)])
def test_reshape_empty_invalid_2d(shape: tuple[int, ...]) -> None:
    s = pl.Series("a", [], dtype=pl.Int64)
    with pytest.raises(
        InvalidOperationError,
        match=re.escape(
            f"cannot reshape empty array into shape {display_shape(shape)}"
        ),
    ):
        s.reshape(shape)


@pytest.mark.parametrize(
    ("shape", "out_dtype"),
    [
        ((0, 5), pl.Array(pl.Int64, 5)),
        ((-1, 3), pl.Array(pl.Int64, 3)),
        ((-1, 3, 2), pl.Array(pl.Int64, (3, 2))),
    ],
)
def test_reshape_empty_valid_2d(shape: tuple[int, ...], out_dtype: pl.DataType) -> None:
    s = pl.Series("a", [], dtype=pl.Int64)
    out = s.reshape(shape)
    assert out.dtype == out_dtype


@pytest.mark.parametrize("shape", [(1,), (2,)])
def test_reshape_empty_invalid_1d(shape: tuple[int, ...]) -> None:
    s = pl.Series("a", [], dtype=pl.Int64)
    with pytest.raises(
        InvalidOperationError,
        match=re.escape(f"cannot reshape empty array into shape ({shape[0]})"),
    ):
        s.reshape(shape)


def test_array_ndarray_reshape() -> None:
    shape = (8, 4, 2, 1)
    s = pl.Series(range(64)).reshape(shape)
    n = s.to_numpy()
    assert n.shape == shape
    assert (n[0] == s[0].to_numpy()).all()
    n = n[0]
    s = s[0]
    assert (n[0] == s[0].to_numpy()).all()
