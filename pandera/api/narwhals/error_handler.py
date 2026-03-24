"""Handle schema errors for Narwhals backends."""

import narwhals.stable.v1 as nw

from pandera.api.base.error_handler import ErrorHandler as _ErrorHandler


class ErrorHandler(_ErrorHandler):
    """Handler for schema- and data-level errors during Narwhals validation."""

    @staticmethod
    def _count_failure_cases(failure_cases) -> int:
        # failure_cases is always native at SchemaError boundary (Phase 6 contract).
        # nw.from_native wraps pl.DataFrame, pl.LazyFrame, and ibis.Table uniformly
        # without backend-specific isinstance checks.
        return int(
            nw.from_native(failure_cases, eager_only=False)
            .lazy()
            .select(nw.len())
            .collect()["len"][0]
        )
