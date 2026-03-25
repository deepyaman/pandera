"""Behavioral parity tests: narwhals backend against Polars and Ibis.

Tests verify that the narwhals backend produces identical validation
behavior when wrapping Polars frames and Ibis Tables. Covers TEST-04.

Coerce-dependent tests are marked xfail(strict=True) — coerce is a v2
feature; strict=True ensures CI breaks when coerce lands so marks are
cleaned up rather than silently accumulating.
"""
import pytest
import polars as pl
import narwhals.stable.v1 as nw
from pandera.api.polars.container import DataFrameSchema
from pandera.api.polars.components import Column
from pandera.api.checks import Check
from pandera.errors import SchemaError, SchemaErrors


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_polars_df(data: dict) -> pl.DataFrame:
    return pl.DataFrame(data)


def _make_ibis_table(data: dict):
    import pandas as pd
    import ibis
    return ibis.memtable(pd.DataFrame(data))


# ---------------------------------------------------------------------------
# TEST-04: Container validation parity (Polars vs Ibis)
# ---------------------------------------------------------------------------

def test_validate_ibis_valid():
    """schema.validate(ibis_table) succeeds for a valid ibis Table."""
    from pandera.api.ibis.container import DataFrameSchema as IbisSchema
    from pandera.api.ibis.components import Column as IbisColumn
    import ibis.expr.datatypes as dt

    schema = IbisSchema(columns={"a": IbisColumn(dt.int64)})
    t = _make_ibis_table({"a": [1, 2, 3]})
    result = schema.validate(t)
    assert result is not None


def test_validate_ibis_invalid_raises():
    """schema.validate(ibis_table) raises SchemaError for an invalid ibis Table."""
    from pandera.api.ibis.container import DataFrameSchema as IbisSchema
    from pandera.api.ibis.components import Column as IbisColumn
    import ibis.expr.datatypes as dt

    schema = IbisSchema(columns={"a": IbisColumn(dt.int64, checks=[Check.greater_than(10)])})
    t = _make_ibis_table({"a": [1, 2, 3]})
    with pytest.raises((SchemaError, SchemaErrors)):
        schema.validate(t)


def test_lazy_mode_ibis_collects_all_errors():
    """schema.validate(ibis_table, lazy=True) collects multiple errors."""
    from pandera.api.ibis.container import DataFrameSchema as IbisSchema
    from pandera.api.ibis.components import Column as IbisColumn
    import ibis.expr.datatypes as dt

    schema = IbisSchema(columns={
        "a": IbisColumn(dt.int64, checks=[Check.greater_than(10)]),
        "b": IbisColumn(dt.int64, checks=[Check.greater_than(10)]),
    })
    t = _make_ibis_table({"a": [1, 2], "b": [3, 4]})
    with pytest.raises(SchemaErrors) as exc_info:
        schema.validate(t, lazy=True)
    assert len(exc_info.value.schema_errors) > 1


def test_strict_true_ibis_rejects_extra_columns():
    """schema.validate(ibis_table, strict=True) raises for extra columns."""
    from pandera.api.ibis.container import DataFrameSchema as IbisSchema
    from pandera.api.ibis.components import Column as IbisColumn
    import ibis.expr.datatypes as dt

    schema = IbisSchema(columns={"a": IbisColumn(dt.int64)}, strict=True)
    t = _make_ibis_table({"a": [1], "b": [2]})
    with pytest.raises((SchemaError, SchemaErrors)):
        schema.validate(t)


def test_strict_filter_ibis_drops_extra_columns():
    """schema.validate(ibis_table, strict='filter') drops extra columns."""
    from pandera.api.ibis.container import DataFrameSchema as IbisSchema
    from pandera.api.ibis.components import Column as IbisColumn
    import ibis.expr.datatypes as dt

    schema = IbisSchema(columns={"a": IbisColumn(dt.int64)}, strict="filter")
    t = _make_ibis_table({"a": [1], "b": [2]})
    result = schema.validate(t)
    assert result is not None
    result_df = result.execute()
    assert "b" not in result_df.columns
    assert "a" in result_df.columns


def test_failure_cases_native_ibis():
    """SchemaError.failure_cases on ibis validation is native ibis.Table.

    Phase 6 contract: failure_cases is native ibis.Table for ibis inputs — not nw.DataFrame.
    RED until Plan 03 materializes failure_cases to native in the error pipeline.
    """
    import ibis
    from pandera.api.ibis.container import DataFrameSchema as IbisSchema
    from pandera.api.ibis.components import Column as IbisColumn
    import ibis.expr.datatypes as dt

    schema = IbisSchema(columns={"a": IbisColumn(dt.int64, checks=[Check.greater_than(10)])})
    t = _make_ibis_table({"a": [1, 2, 3]})
    try:
        schema.validate(t)
        pytest.fail("Expected SchemaError was not raised")
    except SchemaError as err:
        fc = err.failure_cases
        # Phase 6 contract: failure_cases is native ibis.Table (unwrapped).
        assert isinstance(fc, ibis.Table), (
            f"failure_cases should be native ibis.Table (Phase 6 contract), got {type(fc)}"
        )


# ---------------------------------------------------------------------------
# TEST-04: Decorator parity (Polars vs Ibis)
# ---------------------------------------------------------------------------

def test_check_decorator_ibis():
    """@pa.check_input / @pa.check_output works with ibis Table."""
    import pandera.ibis as pa_ibis
    import ibis.expr.datatypes as dt

    schema = pa_ibis.DataFrameSchema(columns={"a": pa_ibis.Column(dt.int64)})

    @pa_ibis.check_input(schema)
    def my_func(t):
        return t

    t = _make_ibis_table({"a": [1, 2, 3]})
    result = my_func(t)
    assert result is not None


# ---------------------------------------------------------------------------
# TEST-04: DataFrameModel parity (Polars vs Ibis)
# ---------------------------------------------------------------------------

def test_dataframe_model_ibis():
    """Ibis DataFrameModel schema validates an ibis Table correctly."""
    import pandera.ibis as pa_ibis
    import ibis.expr.datatypes as dt

    class MyModel(pa_ibis.DataFrameModel):
        a: dt.int64

    t = _make_ibis_table({"a": [1, 2, 3]})
    result = MyModel.validate(t)
    assert result is not None


# ---------------------------------------------------------------------------
# TEST-04: Coerce parity (strict=True — must fail until coerce lands in v2)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="TEST-04: coerce not yet implemented in narwhals backend (v2 feature)", strict=True)
def test_coerce_ibis():
    """coerce=True on ibis Column coerces dtype — xfail strict=True until v2."""
    from pandera.api.ibis.container import DataFrameSchema as IbisSchema
    from pandera.api.ibis.components import Column as IbisColumn
    import ibis.expr.datatypes as dt

    schema = IbisSchema(columns={"a": IbisColumn(dt.int64, coerce=True)})
    # ibis.memtable with string column — should coerce to int64
    import pandas as pd
    import ibis
    t = ibis.memtable(pd.DataFrame({"a": ["1", "2", "3"]}))
    result = schema.validate(t)
    assert result is not None


# ---------------------------------------------------------------------------
# TEST-04: Polars parity (verify narwhals backend works for polars too)
# ---------------------------------------------------------------------------

def test_validate_polars_parity():
    """narwhals backend validates Polars frames correctly (polars parity baseline)."""
    schema = DataFrameSchema(columns={"a": Column(pl.Int64)})
    result = schema.validate(pl.DataFrame({"a": [1, 2, 3]}))
    assert isinstance(result, pl.DataFrame)


def test_lazy_mode_polars_parity():
    """narwhals backend lazy=True collects multiple Polars errors (parity baseline)."""
    schema = DataFrameSchema(
        columns={
            "a": Column(pl.Int64, checks=[Check.greater_than(10)]),
            "b": Column(pl.Int64, checks=[Check.greater_than(10)]),
        }
    )
    with pytest.raises(SchemaErrors) as exc_info:
        schema.validate(pl.DataFrame({"a": [1, 2], "b": [3, 4]}), lazy=True)
    assert len(exc_info.value.schema_errors) > 1


# ---------------------------------------------------------------------------
# TEST-02: element_wise=True check on ibis Table raises (not supported)
# ---------------------------------------------------------------------------

def test_element_wise_check_raises_not_implemented_ibis():
    """element_wise=True on ibis Table raises SchemaError wrapping NotImplementedError.

    SQL-lazy backends (Ibis, DuckDB, PySpark) cannot apply row-level Python
    functions to lazy query plans. element_wise checks are rejected at check
    application time. The NotImplementedError is captured by run_checks and
    surfaced as a SchemaError with CHECK_ERROR reason_code. TEST-02.
    """
    from pandera.api.ibis.container import DataFrameSchema as IbisSchema
    from pandera.api.ibis.components import Column as IbisColumn
    import ibis.expr.datatypes as dt

    schema = IbisSchema(
        columns={"a": IbisColumn(dt.int64, checks=[Check(lambda x: x > 0, element_wise=True)])}
    )
    t = _make_ibis_table({"a": [1, 2, 3]})
    with pytest.raises(SchemaError) as exc_info:
        schema.validate(t)
    # The SchemaError wraps the NotImplementedError from element_wise check rejection
    assert "NotImplementedError" in str(exc_info.value) or "element_wise" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Gap closure: lazy=True custom ibis check must not crash (UAT test 8)
# ---------------------------------------------------------------------------

def test_custom_check_ibis_lazy():
    """schema.validate(ibis_table, lazy=True) with a custom check completes without crashing.

    Regression test for _count_failure_cases calling len() on ibis.Table.
    ibis raises ExpressionError('Use .count() instead') — not TypeError — so
    the original except clause missed it. Fix: detect ibis.Table and use
    .count().execute() instead.

    The check must use IbisData wrapping to produce an ibis.Table as
    failure_cases, which is what triggers the _count_failure_cases bug.
    """
    from pandera.api.ibis.container import DataFrameSchema as IbisSchema
    from pandera.api.ibis.components import Column as IbisColumn
    from pandera.api.ibis.types import IbisData
    import ibis.expr.datatypes as dt
    import ibis.selectors as s
    from ibis import _ as ibis_deferred

    # Custom check using IbisData — returns a column-selection ibis expression.
    # Values [1, 2, 3] are not all == 0, so the check will fail.
    # The failure produces an ibis.Table as failure_cases, which triggered the
    # _count_failure_cases len() crash (ExpressionError, not TypeError).
    def _check_all_zero(data: IbisData):
        return data.table.select(s.across(s.all(), ibis_deferred == 0))

    schema = IbisSchema(
        columns={"a": IbisColumn(dt.int64, checks=[Check(_check_all_zero)])},
    )
    t = _make_ibis_table({"a": [1, 2, 3]})
    with pytest.raises((SchemaError, SchemaErrors)):
        schema.validate(t, lazy=True)


# ---------------------------------------------------------------------------
# TEST-09: drop_invalid_rows expr accumulation (RED baseline for Phase 09)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    reason=(
        "Phase 09 RED baseline: check_output is currently nw.LazyFrame wide table, not nw.Expr. "
        "Will be GREEN after 09-02 changes apply() to return nw.Expr directly."
    ),
    strict=True,
)
def test_drop_invalid_rows_expr_accumulation():
    """check_output stored on SchemaError is nw.Expr after Phase 09 fix.

    RED now: apply() returns a nw.LazyFrame wide table (with CHECK_OUTPUT_KEY column),
    so check_output is a nw.LazyFrame — drop_invalid_rows crashes with
    TypeError: Slicing is not supported on LazyFrame.

    GREEN after 09-02: apply() returns nw.Expr directly; postprocess accumulates
    expressions into a single wide table via with_columns(); drop_invalid_rows
    filters without materialising.
    """
    schema = DataFrameSchema(
        columns={"a": Column(pl.Int64, checks=[Check.greater_than(0)])},
        drop_invalid_rows=True,
    )
    lf = pl.LazyFrame({"a": [-1, 1, 2]})
    try:
        schema.validate(lf, lazy=True)
        pytest.fail("Expected SchemaErrors was not raised")
    except SchemaErrors as err:
        check_output = err.schema_errors[0].check_output
        assert isinstance(check_output, nw.Expr), (
            f"check_output should be nw.Expr after Phase 09 fix, got {type(check_output)}"
        )
