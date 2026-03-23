"""Handle schema errors for Narwhals backends."""

from pandera.api.base.error_handler import ErrorHandler as _ErrorHandler


class ErrorHandler(_ErrorHandler):
    """Handler for schema- and data-level errors during Narwhals validation."""

    @staticmethod
    def _count_failure_cases(failure_cases) -> int:
        # Failure cases can be an ibis.Table, a nw.DataFrame wrapping ibis.Table,
        # a dataframe-like, or a scalar.
        # ibis.Table raises ExpressionError for len(); handle it explicitly.
        try:
            import ibis as _ibis
            if isinstance(failure_cases, _ibis.Table):
                return failure_cases.count().to_pyarrow().as_py()
            # nw.DataFrame wrapping ibis.Table: unwrap and count natively.
            try:
                import narwhals.stable.v1 as nw
                if isinstance(failure_cases, nw.DataFrame):
                    native = nw.to_native(failure_cases)
                    if isinstance(native, _ibis.Table):
                        return native.count().to_pyarrow().as_py()
            except ImportError:
                pass
        except ImportError:
            pass
        return _ErrorHandler._count_failure_cases(failure_cases)
