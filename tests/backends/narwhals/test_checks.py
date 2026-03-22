"""Tests for NarwhalsCheckBackend — CHECKS-01, CHECKS-02, CHECKS-03, TEST-01.

All tests are marked xfail(strict=True) until Plans 02-02 and 02-03 implement
the backend. Once the backend is in place, xfail stubs flip to passing.
"""
import pytest

from pandera.api.checks import Check


# ---------------------------------------------------------------------------
# Parametrize data for CHECKS-02: 14 builtin checks
# Each tuple: (check_name, check_kwargs, valid_data, invalid_data, col)
# ---------------------------------------------------------------------------
BUILTIN_CHECK_CASES = [
    # (check_name, check_kwargs, valid_col_data, invalid_col_data, col_name)
    pytest.param(
        "equal_to",
        {"value": 5},
        {"x": [5, 5, 5]},
        {"x": [5, 5, 4]},
        "x",
        id="equal_to",
    ),
    pytest.param(
        "not_equal_to",
        {"value": 0},
        {"x": [1, 2, 3]},
        {"x": [1, 0, 3]},
        "x",
        id="not_equal_to",
    ),
    pytest.param(
        "greater_than",
        {"min_value": 0},
        {"x": [1, 2, 3]},
        {"x": [1, -1, 3]},
        "x",
        id="greater_than",
    ),
    pytest.param(
        "greater_than_or_equal_to",
        {"min_value": 1},
        {"x": [1, 2, 3]},
        {"x": [1, 0, 3]},
        "x",
        id="greater_than_or_equal_to",
    ),
    pytest.param(
        "less_than",
        {"max_value": 10},
        {"x": [1, 5, 9]},
        {"x": [1, 10, 9]},
        "x",
        id="less_than",
    ),
    pytest.param(
        "less_than_or_equal_to",
        {"max_value": 10},
        {"x": [5, 10, 8]},
        {"x": [5, 11, 8]},
        "x",
        id="less_than_or_equal_to",
    ),
    pytest.param(
        "in_range",
        {"min_value": 1, "max_value": 10, "include_min": True, "include_max": True},
        {"x": [1, 5, 10]},
        {"x": [1, 5, 11]},
        "x",
        id="in_range",
    ),
    pytest.param(
        "isin",
        {"allowed_values": [1, 2, 3]},
        {"x": [1, 2, 3]},
        {"x": [1, 2, 4]},
        "x",
        id="isin",
    ),
    pytest.param(
        "notin",
        {"forbidden_values": [0, -1]},
        {"x": [1, 2, 3]},
        {"x": [1, 0, 3]},
        "x",
        id="notin",
    ),
    pytest.param(
        "str_matches",
        {"pattern": r"^foo"},
        {"s": ["foobar", "foo", "foooo"]},
        {"s": ["foobar", "bar", "foo"]},
        "s",
        id="str_matches",
    ),
    pytest.param(
        "str_contains",
        {"pattern": "oo"},
        {"s": ["foobar", "foo", "boo"]},
        {"s": ["foobar", "bar", "boo"]},
        "s",
        id="str_contains",
    ),
    pytest.param(
        "str_startswith",
        {"string": "foo"},
        {"s": ["foobar", "foo", "foooo"]},
        {"s": ["foobar", "bar", "foooo"]},
        "s",
        id="str_startswith",
    ),
    pytest.param(
        "str_endswith",
        {"string": "bar"},
        {"s": ["foobar", "bar", "mybar"]},
        {"s": ["foobar", "baz", "mybar"]},
        "s",
        id="str_endswith",
    ),
    pytest.param(
        "str_length",
        {"min_value": 2, "max_value": 5},
        {"s": ["ab", "abc", "abcde"]},
        {"s": ["ab", "a", "abcde"]},
        "s",
        id="str_length",
    ),
]


# ---------------------------------------------------------------------------
# CHECKS-01: builtin check routing — NarwhalsData dispatched
# ---------------------------------------------------------------------------

def test_builtin_check_routing(make_narwhals_frame):
    """CHECKS-01: builtin check (native=False) receives (nw.LazyFrame/DataFrame, key)."""
    import narwhals.stable.v1 as nw

    received = []

    # Wrap the underlying equal_to function to capture what it receives
    from pandera.api.function_dispatch import Dispatcher
    original_dispatcher = Check.equal_to(5)._check_fn
    assert isinstance(original_dispatcher, Dispatcher), "expected Dispatcher"
    original_fn = original_dispatcher._function_registry[nw.LazyFrame]

    def capturing_fn(frame, key, **kwargs):
        received.append((frame, key))
        return original_fn(frame, key, **kwargs)

    # Patch the registry so our capturing function runs
    original_dispatcher._function_registry[nw.LazyFrame] = capturing_fn
    try:
        check = Check.equal_to(5)
        frame = make_narwhals_frame({"x": [5, 5, 5]})

        from pandera.backends.narwhals.checks import NarwhalsCheckBackend
        backend = NarwhalsCheckBackend(check)
        backend(frame, key="x")
    finally:
        # Restore original function
        original_dispatcher._function_registry[nw.LazyFrame] = original_fn

    assert len(received) == 1
    frame_received, key_received = received[0]
    # Builtin receives narwhals frame (LazyFrame or DataFrame), not native
    assert isinstance(frame_received, (nw.LazyFrame, nw.DataFrame))
    assert key_received == "x"


def test_user_defined_check_routing(make_narwhals_frame):
    """CHECKS-01: user-defined check (native=True) receives (native_frame, key)."""
    import narwhals.stable.v1 as nw

    received = []

    def user_check(frame, key):
        received.append((frame, key))
        return True

    check = Check(user_check)  # native=True by default
    lf = make_narwhals_frame({"x": [1, 2, 3]})

    from pandera.backends.narwhals.checks import NarwhalsCheckBackend
    backend = NarwhalsCheckBackend(check)
    backend(lf, key="x")

    assert len(received) == 1
    frame_received, key_received = received[0]
    # User-defined check receives the native frame (not nw.LazyFrame/nw.DataFrame wrapper)
    assert not isinstance(frame_received, (nw.LazyFrame, nw.DataFrame))
    assert key_received == "x"


# ---------------------------------------------------------------------------
# CHECKS-02: all 14 builtin checks — valid data passes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "check_name,check_kwargs,valid_data,invalid_data,col",
    BUILTIN_CHECK_CASES,
)
def test_builtin_checks_pass(
    make_narwhals_frame,
    check_name,
    check_kwargs,
    valid_data,
    invalid_data,
    col,
):
    """CHECKS-02: each builtin check passes on valid data (check_passed is True)."""
    check = getattr(Check, check_name)(**check_kwargs)
    frame = make_narwhals_frame(valid_data)

    from pandera.backends.narwhals.checks import NarwhalsCheckBackend
    backend = NarwhalsCheckBackend(check)
    result = backend(frame, key=col)

    # check_passed may be a LazyFrame, DataFrame, or bool
    import narwhals.stable.v1 as nw
    from pandera.constants import CHECK_OUTPUT_KEY
    passed = result.check_passed
    if isinstance(passed, nw.LazyFrame):
        collected = passed.collect()
        val = collected[CHECK_OUTPUT_KEY][0]
    elif isinstance(passed, nw.DataFrame):
        val = passed[CHECK_OUTPUT_KEY][0]
    else:
        val = bool(passed)
    assert val == True  # noqa: E712


# ---------------------------------------------------------------------------
# CHECKS-02: all 14 builtin checks — invalid data fails
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "check_name,check_kwargs,valid_data,invalid_data,col",
    BUILTIN_CHECK_CASES,
)
def test_builtin_checks_fail(
    make_narwhals_frame,
    check_name,
    check_kwargs,
    valid_data,
    invalid_data,
    col,
):
    """CHECKS-02: each builtin check fails on invalid data (check_passed is False)."""
    check = getattr(Check, check_name)(**check_kwargs)
    frame = make_narwhals_frame(invalid_data)

    from pandera.backends.narwhals.checks import NarwhalsCheckBackend
    backend = NarwhalsCheckBackend(check)
    result = backend(frame, key=col)

    import narwhals.stable.v1 as nw
    from pandera.constants import CHECK_OUTPUT_KEY
    passed = result.check_passed
    if isinstance(passed, nw.LazyFrame):
        collected = passed.collect()
        val = collected[CHECK_OUTPUT_KEY][0]
    elif isinstance(passed, nw.DataFrame):
        val = passed[CHECK_OUTPUT_KEY][0]
    else:
        val = bool(passed)
    assert val == False  # noqa: E712


# ---------------------------------------------------------------------------
# CHECKS-03: element_wise on SQL-lazy backend raises NotImplementedError
# ---------------------------------------------------------------------------

def test_element_wise_sql_lazy_raises(make_narwhals_frame):
    """CHECKS-03: element_wise=True on ibis backend raises NotImplementedError."""
    import narwhals.stable.v1 as nw

    check = Check(lambda x: x > 0, element_wise=True)
    frame = make_narwhals_frame({"x": [1, 2, 3]})

    # Only ibis (SQL-lazy) should raise; polars should not
    # The fixture is parameterized — test only runs for ibis backend
    native = nw.to_native(frame)
    backend_name = type(native).__module__.split(".")[0]

    if backend_name != "ibis":
        pytest.skip("element_wise SQL-lazy guard only applies to ibis backend")

    from pandera.backends.narwhals.checks import NarwhalsCheckBackend
    backend = NarwhalsCheckBackend(check)

    with pytest.raises(NotImplementedError, match="element_wise checks are not supported"):
        backend(frame, key="x")


# ---------------------------------------------------------------------------
# TEST-01: native=True dispatch convention — new tests for plan 03-02
# ---------------------------------------------------------------------------

def test_native_true_user_check_polars(make_narwhals_frame):
    """native=True check on Polars receives (pl.LazyFrame, key)."""
    import narwhals.stable.v1 as nw

    received = []

    def user_check(frame, key):
        received.append((type(frame), key))
        return True

    check = Check(user_check)  # native=True by default
    lf = make_narwhals_frame({"x": [1, 2, 3]})

    native = nw.to_native(lf)
    backend_name = type(native).__module__.split(".")[0]
    if backend_name != "polars":
        pytest.skip("polars-specific test")

    from pandera.backends.narwhals.checks import NarwhalsCheckBackend
    backend = NarwhalsCheckBackend(check)
    backend(lf, key="x")

    assert len(received) == 1
    frame_type, key_received = received[0]
    # Native Polars frame, not narwhals wrapper
    assert "polars" in frame_type.__module__
    assert key_received == "x"


def test_native_true_user_check_ibis(make_narwhals_frame):
    """native=True check on Ibis receives (ibis.Table, key)."""
    pytest.importorskip("ibis")
    import ibis
    import narwhals.stable.v1 as nw

    received = []

    def user_check(frame, key):
        received.append((frame, key))
        return True

    check = Check(user_check)  # native=True by default
    lf = make_narwhals_frame({"x": [1, 2, 3]})

    native = nw.to_native(lf)
    if not isinstance(native, ibis.Table):
        pytest.skip("ibis-specific test")

    from pandera.backends.narwhals.checks import NarwhalsCheckBackend
    backend = NarwhalsCheckBackend(check)
    backend(lf, key="x")

    assert len(received) == 1
    frame_received, key_received = received[0]
    assert isinstance(frame_received, ibis.Table)
    assert key_received == "x"


def test_native_false_user_check(make_narwhals_frame):
    """native=False check receives narwhals-wrapped frame and key."""
    import narwhals.stable.v1 as nw

    received = []

    def user_check(frame, key):
        received.append((frame, key))
        return frame.select(nw.col(key) > 0)

    check = Check(user_check, native=False)
    lf = make_narwhals_frame({"x": [1, 2, 3]})

    from pandera.backends.narwhals.checks import NarwhalsCheckBackend
    backend = NarwhalsCheckBackend(check)
    result = backend(lf, key="x")

    assert len(received) == 1
    frame_received, key_received = received[0]
    assert isinstance(frame_received, (nw.LazyFrame, nw.DataFrame))
    assert key_received == "x"


def test_ibis_boolean_scalar_normalization(make_narwhals_frame):
    """native=True check returning ir.BooleanScalar normalizes to bool CheckResult."""
    pytest.importorskip("ibis")
    import ibis
    import narwhals.stable.v1 as nw

    def scalar_check(frame, key):
        # Return a scalar: all values > 0
        return frame[key].min() > 0

    check = Check(scalar_check)  # native=True
    lf = make_narwhals_frame({"x": [1, 2, 3]})

    native = nw.to_native(lf)
    if not isinstance(native, ibis.Table):
        pytest.skip("ibis-specific test")

    from pandera.backends.narwhals.checks import NarwhalsCheckBackend
    backend = NarwhalsCheckBackend(check)
    result = backend(lf, key="x")

    # check_passed should be truthy for all-positive data
    passed = result.check_passed
    if isinstance(passed, (nw.LazyFrame, nw.DataFrame)):
        from pandera.constants import CHECK_OUTPUT_KEY
        if isinstance(passed, nw.LazyFrame):
            passed = passed.collect()
        val = bool(passed[CHECK_OUTPUT_KEY][0])
    else:
        val = bool(passed)
    assert val is True
