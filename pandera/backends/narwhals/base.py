"""Base schema backend for Narwhals."""

import warnings
from collections import defaultdict

import narwhals.stable.v1 as nw
import polars as pl

from pandera.api.narwhals.error_handler import ErrorHandler
from pandera.api.narwhals.utils import _materialize
from pandera.backends.base import BaseSchemaBackend, CoreCheckResult
from pandera.backends.narwhals.checks import NarwhalsCheckBackend
from pandera.constants import CHECK_OUTPUT_KEY
from pandera.errors import (
    FailureCaseMetadata,
    SchemaError,
    SchemaErrorReason,
    SchemaWarning,
)


def _is_lazy_or_sql(fc) -> bool:
    """True for polars-lazy (nw.LazyFrame) or SQL-lazy (nw.DataFrame wrapping ibis.Table)."""
    if isinstance(fc, nw.LazyFrame):
        return True
    if isinstance(fc, nw.DataFrame):
        native = nw.to_native(fc)
        return hasattr(native, "execute")  # ibis.Table has .execute(); polars DataFrame does not
    return False


class NarwhalsSchemaBackend(BaseSchemaBackend):
    """Base schema backend for Narwhals-backed DataFrames.

    Provides shared helpers used by ColumnBackend (components.py) and
    future container-level backends (Phase 4).
    """

    def subsample(
        self,
        check_obj,
        head: int | None = None,
        tail: int | None = None,
        sample: int | None = None,
        random_state: int | None = None,
    ):
        """Return a (possibly subsampled) version of check_obj.

        Never materializes check_obj — delegates directly to .head()/.tail()
        so the result stays lazy (nw.LazyFrame) for Polars inputs.

        :param head: Number of rows to take from the head.
        :param tail: Number of rows to take from the tail.
        :param sample: Not supported — raises NotImplementedError.
        :param random_state: Ignored (no random sampling supported).
        :raises NotImplementedError: If sample is not None, or if tail= is
            requested on a SQL-lazy backend (ibis.Table) that does not support
            TAIL without forced full ordering.
        """
        if sample is not None:
            raise NotImplementedError(
                "sample= is not supported in the Narwhals backend. "
                "Use head= or tail= instead."
            )

        if head is None and tail is None:
            return check_obj

        # Guard: SQL-lazy backends don't support tail without full ordering
        if tail is not None:
            native = nw.to_native(check_obj)
            if hasattr(native, "execute"):  # ibis.Table has .execute(); pl.LazyFrame does not
                raise NotImplementedError(
                    "tail= is not supported on SQL-lazy backends (Ibis, DuckDB, PySpark) "
                    "because SQL has no native TAIL without forced full ordering. "
                    "Use head= instead."
                )

        obj_subsample = []
        if head is not None:
            obj_subsample.append(check_obj.head(head))   # lazy — no _materialize()
        if tail is not None:
            obj_subsample.append(check_obj.tail(tail))   # lazy — polars-only (guarded above)

        return nw.concat(obj_subsample).unique()

    def run_check(self, check_obj, schema, check, check_index, *args):
        """Execute a single Check object and return a CoreCheckResult.

        Single unified code path — no _is_ibis_result bifurcation.
        Materializes only the scalar passed bool via _materialize(check_passed).
        failure_cases and check_output stay as narwhals wrappers in the returned
        CoreCheckResult; callers (failure_cases_metadata) materialize as needed.
        """
        check_result = check(check_obj, *args)

        passed_lf = check_result.check_passed  # nw.LazyFrame or nw.DataFrame
        passed = bool(_materialize(passed_lf)[CHECK_OUTPUT_KEY][0])

        message = None
        failure_cases = None

        if not passed:
            if check_result.failure_cases is None:
                failure_cases = passed
                message = f"Check '{check}' failed — no failure cases captured."
            else:
                fc = check_result.failure_cases
                # Drop CHECK_OUTPUT_KEY column if present (wide table includes it for key=="*" checks)
                if CHECK_OUTPUT_KEY in fc.collect_schema().names():
                    fc = fc.drop(CHECK_OUTPUT_KEY)
                failure_cases = fc  # narwhals wrapper — NOT collected here
                message = f"Check '{check}' failed."

            if check.raise_warning:
                warnings.warn(message, SchemaWarning)
                return CoreCheckResult(
                    passed=True,
                    check=check,
                    reason_code=SchemaErrorReason.DATAFRAME_CHECK,
                )

        return CoreCheckResult(
            passed=passed,
            check=check,
            check_index=check_index,
            check_output=check_result.check_output,  # stays lazy — NOT _materialize() here
            reason_code=SchemaErrorReason.DATAFRAME_CHECK,
            message=message,
            failure_cases=failure_cases,             # narwhals wrapper — NOT _to_native() here
        )

    def is_float_dtype(self, check_obj, col_name: str) -> bool:
        """Return True if the column col_name has a float dtype.

        Uses collect_schema() so it works on both LazyFrame and DataFrame
        without triggering full materialization.

        :param check_obj: Narwhals LazyFrame or DataFrame.
        :param col_name: Name of the column to inspect.
        :returns: True if the column dtype is a floating-point type.
        """
        return check_obj.collect_schema()[col_name].is_float()

    def failure_cases_metadata(
        self,
        schema_name: str,
        schema_errors: list[SchemaError],
    ) -> FailureCaseMetadata:
        """Create failure cases metadata required for SchemaErrors exception.

        Backend-agnostic: returns native ibis.Table for ibis inputs and
        pl.LazyFrame/pl.DataFrame for polars inputs — no forced polars
        conversion, no Arrow roundtrip for lazy/SQL backends.
        """
        error_counts: dict[str, int] = defaultdict(int)
        failure_case_collection = []

        for err in schema_errors:
            error_counts[err.reason_code] += 1

            check_identifier = (
                None
                if err.check is None
                else (
                    err.check
                    if isinstance(err.check, str)
                    else (
                        err.check.error
                        if err.check.error is not None
                        else (
                            err.check.name
                            if err.check.name is not None
                            else str(err.check)
                        )
                    )
                )
            )

            # Wrap native ibis.Table back to narwhals so the type checks below work uniformly.
            fc = err.failure_cases
            try:
                import ibis as _ibis
                if isinstance(fc, _ibis.Table):
                    fc = nw.from_native(fc, eager_or_interchange_only=False)
            except ImportError:
                pass

            if isinstance(fc, (nw.LazyFrame, nw.DataFrame)) and _is_lazy_or_sql(fc):
                # --- Lazy/SQL path (polars-lazy nw.LazyFrame or ibis nw.DataFrame) ---
                # Use narwhals ops only — no Arrow roundtrip, no polars import in this path.
                # Row index is always None — no forced materialization for ordering.
                col_names = fc.collect_schema().names()

                if len(col_names) == 1:
                    # Single-column: rename directly to "failure_case"
                    enriched = fc.rename({col_names[0]: "failure_case"})
                else:
                    # Multi-column: build a readable "col=value, col=value" string per row.
                    # nw.concat_str() is cross-backend (polars and ibis) and stays lazy.
                    parts = [
                        nw.lit(f"{c}=").cast(nw.String) + nw.col(c).cast(nw.String)
                        for c in col_names
                    ]
                    enriched = fc.select(nw.concat_str(*parts, separator=", ").alias("failure_case"))

                enriched = enriched.with_columns(
                    nw.lit(err.schema.__class__.__name__).alias("schema_context"),
                    nw.lit(err.schema.name).alias("column"),
                    nw.lit(check_identifier).alias("check"),
                    nw.lit(err.check_index).cast(nw.Int32).alias("check_number"),
                    nw.lit(None).cast(nw.Int32).alias("index"),
                )
                failure_case_collection.append(nw.to_native(enriched))

            elif isinstance(fc, (nw.LazyFrame, nw.DataFrame)):
                # --- Eager polars path (nw.DataFrame wrapping pl.DataFrame) ---
                # Keep existing polars-based logic — works correctly for eager inputs.
                # Row index is derivable from check_output.
                fc_eager = _materialize(fc)
                pl_fc = pl.from_arrow(fc_eager.to_arrow())

                # Compute row indices of failing cases from check_output.
                if err.check_output is not None:
                    co = err.check_output
                    if not isinstance(co, (nw.LazyFrame, nw.DataFrame)):
                        co = nw.from_native(co, eager_or_interchange_only=False)
                    co_eager = _materialize(co)
                    try:
                        co_indexed = co_eager.with_row_index("index")
                    except Exception:
                        co_indexed = co_eager.with_row_count("index")
                    failing_indices = co_indexed.filter(
                        ~nw.col(CHECK_OUTPUT_KEY)
                    )["index"].to_list()
                    index = pl.Series("index", failing_indices, dtype=pl.Int32)
                else:
                    index = pl.Series("index", [None] * len(pl_fc), dtype=pl.Int32)

                if len(pl_fc.columns) > 1:
                    failure_cases_df = pl_fc.with_columns(
                        failure_case=pl.Series(pl_fc.rows(named=True))
                    ).select(pl.col.failure_case.struct.json_encode())
                else:
                    failure_cases_df = pl_fc.rename(
                        {pl_fc.columns[0]: "failure_case"}
                    )

                failure_cases_df = failure_cases_df.with_columns(
                    schema_context=pl.lit(err.schema.__class__.__name__),
                    column=pl.lit(err.schema.name),
                    check=pl.lit(check_identifier),
                    check_number=pl.lit(err.check_index),
                    index=index.limit(failure_cases_df.shape[0]),
                ).cast(
                    {
                        "failure_case": pl.Utf8,
                        "column": pl.String,
                        "index": pl.Int32,
                        "check_number": pl.Int32,
                    }
                )
                failure_case_collection.append(failure_cases_df)

            else:
                # --- Scalar path (Python scalars, strings, etc.) ---
                scalar_failure_cases = defaultdict(list)
                scalar_failure_cases["failure_case"].append(err.failure_cases)
                scalar_failure_cases["schema_context"].append(
                    err.schema.__class__.__name__
                )
                scalar_failure_cases["column"].append(err.schema.name)
                scalar_failure_cases["check"].append(check_identifier)
                scalar_failure_cases["check_number"].append(err.check_index)
                scalar_failure_cases["index"].append(None)
                failure_cases_df = pl.DataFrame(scalar_failure_cases).cast(
                    {
                        "check_number": pl.Int32,
                        "column": pl.String,
                        "index": pl.Int32,
                    }
                )
                failure_case_collection.append(failure_cases_df)

        # Backend-aware concat: ibis uses .union(), polars uses pl.concat().
        if failure_case_collection:
            first = failure_case_collection[0]
            if hasattr(first, "union"):  # ibis.Table
                import functools
                failure_cases = functools.reduce(lambda a, b: a.union(b), failure_case_collection)
            else:
                failure_cases = pl.concat(failure_case_collection)  # pl.LazyFrame or pl.DataFrame
        else:
            failure_cases = pl.DataFrame()

        error_handler = ErrorHandler()
        # Only collect errors with a valid reason_code; errors without one
        # (e.g. manually-constructed SchemaError stubs) are silently skipped.
        valid_errors = [e for e in schema_errors if e.reason_code is not None]
        error_handler.collect_errors(valid_errors)
        error_dicts = {}

        def defaultdict_to_dict(d):
            if isinstance(d, defaultdict):
                d = {k: defaultdict_to_dict(v) for k, v in d.items()}
            return d

        if error_handler.collected_errors:
            error_dicts = error_handler.summarize(schema_name=schema_name)
            error_dicts = defaultdict_to_dict(error_dicts)

        error_counts = defaultdict(int)  # type: ignore
        for error in error_handler.collected_errors:
            error_counts[error["reason_code"].name] += 1

        return FailureCaseMetadata(
            failure_cases=failure_cases,
            message=error_dicts,
            error_counts=error_counts,
        )

    def drop_invalid_rows(self, check_obj, error_handler):
        """Remove invalid rows according to failures in error_handler.

        For Ibis: delegates to IbisSchemaBackend.drop_invalid_rows() since
        Narwhals has no positional-join / row_number abstraction for ibis.
        For Polars: uses nw.all_horizontal() to combine boolean check_outputs.

        :param check_obj: The frame to filter.
        :param error_handler: ErrorHandler whose schema_errors carry check_output.
        :returns: Filtered frame with only rows where all checks passed.
        """
        errors = getattr(error_handler, "schema_errors", [])
        if not errors:
            return check_obj

        # Detect ibis path: unwrap to native and check type
        native = nw.to_native(check_obj) if isinstance(check_obj, (nw.LazyFrame, nw.DataFrame)) else check_obj
        try:
            import ibis as _ibis
            if isinstance(native, _ibis.Table):
                from pandera.backends.ibis.base import IbisSchemaBackend
                result = IbisSchemaBackend().drop_invalid_rows(native, error_handler)
                return nw.from_native(result, eager_or_interchange_only=False)
        except ImportError:
            pass

        # Polars path: use nw.all_horizontal() for boolean reduction (replaces pl.fold)
        check_outputs = [
            err.check_output for err in errors
            if err.check_output is not None
        ]
        if not check_outputs:
            return check_obj

        # check_outputs are native pl.DataFrame with CHECK_OUTPUT_KEY boolean column
        merged_pl = pl.DataFrame(
            {str(i): co[CHECK_OUTPUT_KEY] for i, co in enumerate(check_outputs)}
        )
        merged_nw = nw.from_native(merged_pl)
        valid_rows_nw = merged_nw.select(
            nw.all_horizontal(*[nw.col(c) for c in merged_pl.columns]).alias("valid_rows")
        )
        valid_rows = nw.to_native(valid_rows_nw)["valid_rows"]
        return check_obj.filter(valid_rows)
