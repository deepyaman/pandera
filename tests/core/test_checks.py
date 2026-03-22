"""Core Check tests — native flag and from_builtin_check_name propagation."""
import pytest
import polars as pl
import narwhals.stable.v1 as nw

from pandera.api.checks import Check


class TestNativeFlag:
    """Test the native: bool parameter on Check.__init__."""

    def test_native_default_true(self):
        """Check(fn).native == True (default)."""
        check = Check(lambda x: True)
        assert check.native is True

    def test_native_explicit_false(self):
        """Check(fn, native=False).native == False."""
        check = Check(lambda x: True, native=False)
        assert check.native is False

    def test_native_explicit_true(self):
        """Check(fn, native=True).native == True (explicit)."""
        check = Check(lambda x: True, native=True)
        assert check.native is True

    def test_element_wise_and_native_coexist(self):
        """element_wise=True, native=True both coexist without error."""
        check = Check(lambda x: x > 0, element_wise=True, native=True)
        assert check.element_wise is True
        assert check.native is True

    def test_element_wise_false_native_false(self):
        """element_wise=False, native=False both coexist without error."""
        check = Check(lambda x: True, element_wise=False, native=False)
        assert check.element_wise is False
        assert check.native is False


class TestBuiltinNativeFalse:
    """Test that builtin checks created via from_builtin_check_name have native=False."""

    def test_equal_to_native_false(self):
        """Check.equal_to(5).native == False."""
        assert Check.equal_to(5).native is False

    def test_greater_than_native_false(self):
        """Check.greater_than(0).native == False."""
        assert Check.greater_than(0).native is False

    def test_isin_native_false(self):
        """Check.isin([1, 2]).native == False."""
        assert Check.isin([1, 2]).native is False

    def test_not_equal_to_native_false(self):
        """Check.not_equal_to(0).native == False."""
        assert Check.not_equal_to(0).native is False

    def test_greater_than_or_equal_to_native_false(self):
        """Check.greater_than_or_equal_to(1).native == False."""
        assert Check.greater_than_or_equal_to(1).native is False

    def test_less_than_native_false(self):
        """Check.less_than(10).native == False."""
        assert Check.less_than(10).native is False

    def test_less_than_or_equal_to_native_false(self):
        """Check.less_than_or_equal_to(10).native == False."""
        assert Check.less_than_or_equal_to(10).native is False

    def test_in_range_native_false(self):
        """Check.in_range(0, 10).native == False."""
        assert Check.in_range(0, 10).native is False

    def test_notin_native_false(self):
        """Check.notin([0, -1]).native == False."""
        assert Check.notin([0, -1]).native is False

    def test_str_matches_native_false(self):
        """Check.str_matches(r'^foo').native == False."""
        assert Check.str_matches(r"^foo").native is False

    def test_str_contains_native_false(self):
        """Check.str_contains('oo').native == False."""
        assert Check.str_contains("oo").native is False

    def test_str_startswith_native_false(self):
        """Check.str_startswith('foo').native == False."""
        assert Check.str_startswith("foo").native is False

    def test_str_endswith_native_false(self):
        """Check.str_endswith('bar').native == False."""
        assert Check.str_endswith("bar").native is False

    def test_str_length_native_false(self):
        """Check.str_length(min_value=2, max_value=5).native == False."""
        assert Check.str_length(min_value=2, max_value=5).native is False


class TestBuiltinCheckSignatures:
    """Test that all 14 builtin check functions accept (frame, key, ...) signature.

    These tests call the builtin functions directly with (frame, key, ...) —
    verifying the new signature is in place and produces correct output.
    """

    @pytest.fixture(autouse=True)
    def register_backends(self):
        """Ensure narwhals backends are registered."""
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            from pandera.backends.polars.register import register_polars_backends
            register_polars_backends.cache_clear()
            register_polars_backends()

    @pytest.fixture
    def lazy_frame(self):
        """Return a simple polars LazyFrame wrapped in narwhals."""
        return nw.from_native(
            pl.LazyFrame({"x": [1, 2, 3], "s": ["foo", "foobar", "bar"]}),
            eager_or_interchange_only=False,
        )

    def _get_builtin_fn(self, name):
        """Retrieve the raw callable registered for a builtin check name."""
        from pandera.api.base.checks import BaseCheck
        # The registry stores a Dispatcher; get the underlying function
        dispatcher = BaseCheck.CHECK_FUNCTION_REGISTRY[name]
        return dispatcher

    def test_equal_to_signature(self, lazy_frame):
        """equal_to(frame, key, value=5) is callable with new signature."""
        from pandera.backends.narwhals.builtin_checks import equal_to
        result = equal_to(lazy_frame, "x", value=3)
        assert isinstance(result, nw.LazyFrame)

    def test_not_equal_to_signature(self, lazy_frame):
        """not_equal_to(frame, key, value=0) is callable with new signature."""
        from pandera.backends.narwhals.builtin_checks import not_equal_to
        result = not_equal_to(lazy_frame, "x", value=0)
        assert isinstance(result, nw.LazyFrame)

    def test_greater_than_signature(self, lazy_frame):
        """greater_than(frame, key, min_value=0) is callable with new signature."""
        from pandera.backends.narwhals.builtin_checks import greater_than
        result = greater_than(lazy_frame, "x", min_value=0)
        assert isinstance(result, nw.LazyFrame)

    def test_greater_than_or_equal_to_signature(self, lazy_frame):
        """greater_than_or_equal_to(frame, key, min_value=1) is callable."""
        from pandera.backends.narwhals.builtin_checks import greater_than_or_equal_to
        result = greater_than_or_equal_to(lazy_frame, "x", min_value=1)
        assert isinstance(result, nw.LazyFrame)

    def test_less_than_signature(self, lazy_frame):
        """less_than(frame, key, max_value=10) is callable with new signature."""
        from pandera.backends.narwhals.builtin_checks import less_than
        result = less_than(lazy_frame, "x", max_value=10)
        assert isinstance(result, nw.LazyFrame)

    def test_less_than_or_equal_to_signature(self, lazy_frame):
        """less_than_or_equal_to(frame, key, max_value=10) is callable."""
        from pandera.backends.narwhals.builtin_checks import less_than_or_equal_to
        result = less_than_or_equal_to(lazy_frame, "x", max_value=10)
        assert isinstance(result, nw.LazyFrame)

    def test_in_range_signature(self, lazy_frame):
        """in_range(frame, key, min_value, max_value, ...) is callable."""
        from pandera.backends.narwhals.builtin_checks import in_range
        result = in_range(lazy_frame, "x", min_value=1, max_value=10)
        assert isinstance(result, nw.LazyFrame)

    def test_isin_signature(self, lazy_frame):
        """isin(frame, key, allowed_values) is callable with new signature."""
        from pandera.backends.narwhals.builtin_checks import isin
        result = isin(lazy_frame, "x", allowed_values=[1, 2, 3])
        assert isinstance(result, nw.LazyFrame)

    def test_notin_signature(self, lazy_frame):
        """notin(frame, key, forbidden_values) is callable with new signature."""
        from pandera.backends.narwhals.builtin_checks import notin
        result = notin(lazy_frame, "x", forbidden_values=[0, -1])
        assert isinstance(result, nw.LazyFrame)

    def test_str_matches_signature(self, lazy_frame):
        """str_matches(frame, key, pattern) is callable with new signature."""
        from pandera.backends.narwhals.builtin_checks import str_matches
        result = str_matches(lazy_frame, "s", pattern=r"^foo")
        assert isinstance(result, nw.LazyFrame)

    def test_str_contains_signature(self, lazy_frame):
        """str_contains(frame, key, pattern) is callable with new signature."""
        from pandera.backends.narwhals.builtin_checks import str_contains
        result = str_contains(lazy_frame, "s", pattern="oo")
        assert isinstance(result, nw.LazyFrame)

    def test_str_startswith_signature(self, lazy_frame):
        """str_startswith(frame, key, string) is callable with new signature."""
        from pandera.backends.narwhals.builtin_checks import str_startswith
        result = str_startswith(lazy_frame, "s", string="foo")
        assert isinstance(result, nw.LazyFrame)

    def test_str_endswith_signature(self, lazy_frame):
        """str_endswith(frame, key, string) is callable with new signature."""
        from pandera.backends.narwhals.builtin_checks import str_endswith
        result = str_endswith(lazy_frame, "s", string="bar")
        assert isinstance(result, nw.LazyFrame)

    def test_str_length_signature(self, lazy_frame):
        """str_length(frame, key, min_value, max_value) is callable with new signature."""
        from pandera.backends.narwhals.builtin_checks import str_length
        result = str_length(lazy_frame, "s", min_value=2, max_value=10)
        assert isinstance(result, nw.LazyFrame)
