"""Handle schema errors for Narwhals backends."""

import narwhals.stable.v1 as nw

from pandera.api.base.error_handler import ErrorHandler as _ErrorHandler
from pandera.api.narwhals.utils import _materialize


class ErrorHandler(_ErrorHandler):
    """Handler for schema- and data-level errors during Narwhals validation."""

    @staticmethod
    def _count_failure_cases(failure_cases) -> int:
        if isinstance(failure_cases, (nw.LazyFrame, nw.DataFrame)):
            return len(_materialize(failure_cases.select(nw.len())))
        # Handle native ibis.Table: SchemaError.failure_cases is now native (Phase 6 contract).
        # ibis.Table.__len__() raises ExpressionError; use .count().execute() instead.
        try:
            import ibis as _ibis
            if isinstance(failure_cases, _ibis.Table):
                return int(failure_cases.count().execute())
        except ImportError:
            pass
        return _ErrorHandler._count_failure_cases(failure_cases)
