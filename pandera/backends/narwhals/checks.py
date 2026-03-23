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
        frame = check_obj.frame
        key = check_obj.key

        if self.check.element_wise:
            selector = nw.col(key or "*")
            try:
                expr = selector.map_batches(
                    self.check_fn, return_dtype=nw.Boolean
                )
                return frame.with_columns(expr.alias(CHECK_OUTPUT_KEY))
            except NotImplementedError:
                raise NotImplementedError(
                    "element_wise checks are not supported on SQL-lazy backends "
                    "(Ibis, DuckDB, PySpark) because row-level Python functions "
                    "cannot be applied to lazy query plans. "
                    "Use a vectorized check instead."
                )

        elif self.check.native:
            # native=True: unwrap to backend-native type, call (native_frame, key)
            native_frame = nw.to_native(frame)
            out = self.check_fn(native_frame, key)
            return self._normalize_native_output(out, check_obj)

        else:
            # native=False: expression protocol.
            # Column check: pass nw.col(key). Frame check (key=="*"): pass frame.
            if key and key != "*":
                expr = self.check_fn(nw.col(key))
            else:
                expr = self.check_fn(frame)
            return frame.with_columns(expr.alias(CHECK_OUTPUT_KEY))

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


    def postprocess_lazyframe_output(
        self,
        check_obj: NarwhalsData,
        check_output,
    ) -> CheckResult:
        """Postprocesses LazyFrame check output into a CheckResult."""
        # check_output is the wide table (frame + CHECK_OUTPUT_KEY column). Stay lazy.
        if self.check.ignore_na:
            check_output = check_output.with_columns(
                nw.col(CHECK_OUTPUT_KEY) | nw.col(CHECK_OUTPUT_KEY).is_null()
            )
        passed = check_output.select(nw.col(CHECK_OUTPUT_KEY).all())
        failure_cases = check_output.filter(~nw.col(CHECK_OUTPUT_KEY))

        if check_obj.key != "*":
            failure_cases = failure_cases.select(check_obj.key)
        if self.check.n_failure_cases is not None:
            failure_cases = failure_cases.head(self.check.n_failure_cases)

        return CheckResult(
            check_output=check_output,
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
