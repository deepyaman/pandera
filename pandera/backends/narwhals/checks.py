"""Check backend for Narwhals."""

from functools import partial
from typing import Optional

import narwhals.stable.v1 as nw

from pandera.api.base.checks import CheckResult
from pandera.api.checks import Check
from pandera.api.narwhals.types import NarwhalsData
from pandera.backends.base import BaseCheckBackend
from pandera.constants import CHECK_OUTPUT_KEY


class NarwhalsCheckBackend(BaseCheckBackend):
    """Check backend for Narwhals."""

    def __init__(self, check: Check):
        """Initializes a check backend object."""
        super().__init__(check)
        assert check._check_fn is not None, "Check._check_fn must be set."
        self.check = check
        self.check_fn = partial(check._check_fn, **check._check_kwargs)

    def groupby(self, check_obj: nw.LazyFrame):
        """Implements groupby behavior for check object."""
        raise NotImplementedError

    def query(self, check_obj: nw.LazyFrame):
        """Implements querying behavior to produce subset of check object."""
        raise NotImplementedError

    def aggregate(self, check_obj: nw.LazyFrame):
        """Implements aggregation behavior for check object."""
        raise NotImplementedError

    def preprocess(self, check_obj: nw.LazyFrame, key: Optional[str]):
        """Preprocesses a check object before applying the check function."""
        return check_obj

    def apply(self, check_obj: NarwhalsData):
        """Apply check function — dispatch on self.check.native flag."""
        if self.check.element_wise:
            selector = nw.col(check_obj.key or "*")
            try:
                out = check_obj.frame.with_columns(
                    selector.map_batches(
                        self.check_fn, return_dtype=nw.Boolean
                    )
                ).select(selector)
            except NotImplementedError:
                raise NotImplementedError(
                    "element_wise checks are not supported on SQL-lazy backends "
                    "(Ibis, DuckDB, PySpark) because row-level Python functions "
                    "cannot be applied to lazy query plans. "
                    "Use a vectorized check instead."
                )
        elif self.check.native:
            # native=True: unwrap to backend-native type, call (native_frame, key)
            native_frame = nw.to_native(check_obj.frame)
            out = self.check_fn(native_frame, check_obj.key)
            out = self._normalize_native_output(out, check_obj)
        else:
            # native=False: narwhals frame and key (builtin checks path).
            # Builtin check_fn is a partial(Dispatcher, **kwargs). Ibis frames
            # arrive as nw.DataFrame but Dispatcher is keyed on nw.LazyFrame,
            # so we look up the nw.LazyFrame implementation and re-apply kwargs.
            from pandera.api.function_dispatch import Dispatcher
            check_fn = self.check_fn
            inner_fn = check_fn.func if hasattr(check_fn, "func") else check_fn
            kwargs = check_fn.keywords if hasattr(check_fn, "keywords") else {}
            if isinstance(inner_fn, Dispatcher) and not isinstance(
                check_obj.frame, nw.LazyFrame
            ):
                # Retrieve the narwhals-registered implementation directly.
                narwhals_fn = inner_fn._function_registry.get(nw.LazyFrame)
                if narwhals_fn is not None:
                    out = narwhals_fn(check_obj.frame, check_obj.key, **kwargs)
                else:
                    out = check_fn(check_obj.frame, check_obj.key)
            else:
                out = check_fn(check_obj.frame, check_obj.key)

        if isinstance(out, bool):
            return out

        # Rename single-column output or reduce multi-column to CHECK_OUTPUT_KEY
        col_names = out.collect_schema().names()
        if len(col_names) > 1:
            out = out.select(
                nw.all_horizontal(*[nw.col(c) for c in col_names]).alias(
                    CHECK_OUTPUT_KEY
                )
            )
        else:
            out = out.rename({col_names[0]: CHECK_OUTPUT_KEY})

        return out

    @staticmethod
    def _normalize_native_output(out, check_obj: NarwhalsData):
        """Normalize ibis outputs from native=True checks to narwhals types.

        Polars and bool outputs pass through unchanged.
        """
        try:
            import ibis
            import ibis.expr.types as ir
            if isinstance(out, ir.BooleanScalar):
                return bool(out.execute())
            elif isinstance(out, ir.BooleanColumn):
                # Promote to a one-column ibis Table then wrap with narwhals.
                # Use the native table from check_obj to host the column expression.
                native = nw.to_native(check_obj.frame)
                tbl = native.select(out.name(CHECK_OUTPUT_KEY))
                return nw.from_native(tbl, eager_or_interchange_only=False)
            elif isinstance(out, ibis.Table):
                return nw.from_native(out, eager_or_interchange_only=False)
        except ImportError:
            pass
        return out

    def postprocess(self, check_obj: NarwhalsData, check_output):
        """Postprocesses the result of applying the check function."""
        if isinstance(check_output, (nw.LazyFrame, nw.DataFrame)):
            return self.postprocess_lazyframe_output(check_obj, check_output)
        elif isinstance(check_output, bool):
            return self.postprocess_bool_output(check_obj, check_output)
        raise TypeError(
            f"output type of check_fn not recognized: {type(check_output)}"
        )

    @staticmethod
    def _materialize(frame) -> nw.DataFrame:
        """Materialize a LazyFrame or SQL-lazy DataFrame to a Narwhals DataFrame.

        - nw.LazyFrame (Polars): call .collect()
        - nw.DataFrame wrapping a SQL-lazy backend (Ibis): call
          nw.to_native().execute() then wrap with nw.from_native()
        """
        if isinstance(frame, nw.LazyFrame):
            return frame.collect()
        # SQL-lazy (Ibis, DuckDB): the frame is already a nw.DataFrame but
        # cannot be collected — execute via the native object instead.
        native = nw.to_native(frame)
        if hasattr(native, "execute"):
            return nw.from_native(native.execute())
        # Fallback: already an eager DataFrame
        return frame

    def postprocess_lazyframe_output(
        self,
        check_obj: NarwhalsData,
        check_output,
    ) -> CheckResult:
        """Postprocesses LazyFrame check output into a CheckResult."""
        # Materialize results so its Series can be passed to with_columns below.
        # data_df must also be collected to produce an eager combined frame.
        results_df = self._materialize(check_output)
        if self.check.ignore_na:
            results_df = results_df.with_columns(
                nw.col(CHECK_OUTPUT_KEY) | nw.col(CHECK_OUTPUT_KEY).is_null()
            )
        passed = results_df.select(nw.col(CHECK_OUTPUT_KEY).all())
        data_df = self._materialize(check_obj.frame)
        combined = data_df.with_columns(results_df[CHECK_OUTPUT_KEY])
        failure_cases = combined.filter(~nw.col(CHECK_OUTPUT_KEY))

        if check_obj.key != "*":
            failure_cases = failure_cases.select(check_obj.key)
        if self.check.n_failure_cases is not None:
            failure_cases = failure_cases.head(self.check.n_failure_cases)

        return CheckResult(
            check_output=results_df,
            check_passed=passed,
            checked_object=check_obj,
            failure_cases=failure_cases,
        )

    def postprocess_bool_output(
        self,
        check_obj: NarwhalsData,
        check_output: bool,
    ) -> CheckResult:
        """Postprocesses bool check output into a CheckResult."""
        # SQL-lazy backends (ibis) do not support nw.from_dict — use polars
        # as the eager namespace for bool scalar results.
        try:
            ns = nw.get_native_namespace(check_obj.frame)
            lf = nw.from_dict(
                {CHECK_OUTPUT_KEY: [check_output]}, native_namespace=ns
            ).lazy()
        except (ValueError, AttributeError):
            import polars as pl
            lf = nw.from_native(
                pl.LazyFrame({CHECK_OUTPUT_KEY: [check_output]}),
                eager_or_interchange_only=False,
            )
        return CheckResult(
            check_output=lf,
            check_passed=lf,
            checked_object=check_obj,
            failure_cases=None,
        )

    def __call__(
        self,
        check_obj: nw.LazyFrame,
        key: Optional[str] = None,
    ) -> CheckResult:
        check_obj = self.preprocess(check_obj, key)
        narwhals_data = NarwhalsData(check_obj, key or "*")
        check_output = self.apply(narwhals_data)
        return self.postprocess(narwhals_data, check_output)
