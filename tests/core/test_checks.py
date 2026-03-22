"""Core Check tests — native flag and from_builtin_check_name propagation."""
import pytest

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
