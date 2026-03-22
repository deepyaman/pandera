"""Built-in checks for Narwhals."""

import re
from collections.abc import Collection
from typing import Any, Optional, TypeVar, Union

import narwhals.stable.v1 as nw

from pandera.api.extensions import register_builtin_check

T = TypeVar("T")

_CLOSED_MAP = {
    (True, True): "both",
    (True, False): "left",
    (False, True): "right",
    (False, False): "none",
}


@register_builtin_check(
    aliases=["eq"],
    error="equal_to({value})",
)
def equal_to(frame: nw.LazyFrame, key: str, value: Any) -> nw.LazyFrame:
    """Ensure all elements of a column equal a certain value.

    :param frame: Narwhals LazyFrame containing the column to check.
    :param key: Name of the column to check.
    :param value: Values in this Narwhals data structure must be equal to this
        value.
    """
    return frame.select(nw.col(key) == value)


@register_builtin_check(
    aliases=["ne"],
    error="not_equal_to({value})",
)
def not_equal_to(frame: nw.LazyFrame, key: str, value: Any) -> nw.LazyFrame:
    """Ensure no element of a column equals a certain value.

    :param frame: Narwhals LazyFrame containing the column to check.
    :param key: Name of the column to check.
    :param value: This value must not occur in the checked data structure.
    """
    return frame.select(nw.col(key) != value)


@register_builtin_check(
    aliases=["gt"],
    error="greater_than({min_value})",
)
def greater_than(frame: nw.LazyFrame, key: str, min_value: Any) -> nw.LazyFrame:
    """Ensure values of a column are strictly greater than a minimum value.

    :param frame: Narwhals LazyFrame containing the column to check.
    :param key: Name of the column to check.
    :param min_value: Lower bound to be exceeded. Must be a type comparable to
        the dtype of the series datatype.
    """
    return frame.select(nw.col(key) > min_value)


@register_builtin_check(
    aliases=["ge"],
    error="greater_than_or_equal_to({min_value})",
)
def greater_than_or_equal_to(
    frame: nw.LazyFrame, key: str, min_value: Any
) -> nw.LazyFrame:
    """Ensure all values are greater than or equal to a minimum value.

    :param frame: Narwhals LazyFrame containing the column to check.
    :param key: Name of the column to check.
    :param min_value: Allowed minimum value. Must be a type comparable to the
        dtype of the series to be validated.
    """
    return frame.select(nw.col(key) >= min_value)


@register_builtin_check(
    aliases=["lt"],
    error="less_than({max_value})",
)
def less_than(frame: nw.LazyFrame, key: str, max_value: Any) -> nw.LazyFrame:
    """Ensure values of a column are strictly less than a maximum value.

    :param frame: Narwhals LazyFrame containing the column to check.
    :param key: Name of the column to check.
    :param max_value: All elements of a series must be strictly smaller than
        this. Must be a type comparable to the dtype of the series to be
        validated.
    """
    return frame.select(nw.col(key) < max_value)


@register_builtin_check(
    aliases=["le"],
    error="less_than_or_equal_to({max_value})",
)
def less_than_or_equal_to(frame: nw.LazyFrame, key: str, max_value: Any) -> nw.LazyFrame:
    """Ensure all values are less than or equal to a maximum value.

    :param frame: Narwhals LazyFrame containing the column to check.
    :param key: Name of the column to check.
    :param max_value: Upper bound not to be exceeded. Must be a type comparable
        to the dtype of the series to be validated.
    """
    return frame.select(nw.col(key) <= max_value)


@register_builtin_check(
    aliases=["between"],
    error="in_range({min_value}, {max_value})",
)
def in_range(
    frame: nw.LazyFrame,
    key: str,
    min_value: T,
    max_value: T,
    include_min: bool = True,
    include_max: bool = True,
) -> nw.LazyFrame:
    """Ensure all values of a series are within an interval.

    Both endpoints must be a type comparable to the dtype of the series to be
    validated.

    :param frame: Narwhals LazyFrame containing the column to check.
    :param key: Name of the column to check.
    :param min_value: Left / lower endpoint of the interval.
    :param max_value: Right / upper endpoint of the interval. Must not be
        smaller than min_value.
    :param include_min: Defines whether min_value is also an allowed value
        (the default) or whether all values must be strictly greater than
        min_value.
    :param include_max: Defines whether max_value is also an allowed value
        (the default) or whether all values must be strictly smaller than
        max_value.
    """
    closed = _CLOSED_MAP[(include_min, include_max)]
    return frame.select(
        nw.col(key).is_between(min_value, max_value, closed=closed)
    )


@register_builtin_check(
    error="isin({allowed_values})",
)
def isin(frame: nw.LazyFrame, key: str, allowed_values: Collection) -> nw.LazyFrame:
    """Ensure only allowed values occur within a series.

    This checks whether all elements of a series are part of the set of
    elements of allowed values. If allowed values is a string, the set of
    elements consists of all distinct characters of the string. Thus only
    single characters which occur in allowed_values at least once can meet
    this condition. If you want to check for substrings use
    :meth:`Check.str_contains`.

    :param frame: Narwhals LazyFrame containing the column to check.
    :param key: Name of the column to check.
    :param allowed_values: The set of allowed values. May be any iterable.
    """
    return frame.select(nw.col(key).is_in(allowed_values))


@register_builtin_check(
    error="notin({forbidden_values})",
)
def notin(frame: nw.LazyFrame, key: str, forbidden_values: Collection) -> nw.LazyFrame:
    """Ensure some defined values don't occur within a series.

    Like :meth:`Check.isin`, this check operates on single characters if it is
    applied on strings. If forbidden_values is a string, it is understood as
    set of prohibited characters. Any string of length > 1 can't be in it by
    design.

    :param frame: Narwhals LazyFrame containing the column to check.
    :param key: Name of the column to check.
    :param forbidden_values: The set of values which should not occur. May be
        any iterable.
    """
    return frame.select(~nw.col(key).is_in(forbidden_values))


@register_builtin_check(
    error="str_matches('{pattern}')",
)
def str_matches(
    frame: nw.LazyFrame,
    key: str,
    pattern: Union[str, re.Pattern],
) -> nw.LazyFrame:
    """Ensure that all values start with a match of a regular expression
    pattern.

    :param frame: Narwhals LazyFrame containing the column to check.
    :param key: Name of the column to check.
    :param pattern: Regular expression pattern to use for matching.
    """
    pattern = pattern.pattern if isinstance(pattern, re.Pattern) else pattern
    if not pattern.startswith("^"):
        pattern = f"^{pattern}"
    return frame.select(nw.col(key).str.contains(pattern))


@register_builtin_check(
    error="str_contains('{pattern}')",
)
def str_contains(
    frame: nw.LazyFrame,
    key: str,
    pattern: Union[str, re.Pattern],
) -> nw.LazyFrame:
    """Ensure that a pattern can be found within each row.

    :param frame: Narwhals LazyFrame containing the column to check.
    :param key: Name of the column to check.
    :param pattern: Regular expression pattern to use for searching.
    """
    pattern = pattern.pattern if isinstance(pattern, re.Pattern) else pattern
    return frame.select(nw.col(key).str.contains(pattern))


@register_builtin_check(
    error="str_startswith('{string}')",
)
def str_startswith(frame: nw.LazyFrame, key: str, string: str) -> nw.LazyFrame:
    """Ensure that all values start with a certain string.

    :param frame: Narwhals LazyFrame containing the column to check.
    :param key: Name of the column to check.
    :param string: String all values should start with.
    """
    return frame.select(nw.col(key).str.starts_with(string))


@register_builtin_check(error="str_endswith('{string}')")
def str_endswith(frame: nw.LazyFrame, key: str, string: str) -> nw.LazyFrame:
    """Ensure that all values end with a certain string.

    :param frame: Narwhals LazyFrame containing the column to check.
    :param key: Name of the column to check.
    :param string: String all values should end with.
    """
    return frame.select(nw.col(key).str.ends_with(string))


@register_builtin_check()
def str_length(
    frame: nw.LazyFrame,
    key: str,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    exact_value: Optional[int] = None,
) -> nw.LazyFrame:
    """Ensure that the length of strings is within a specified range.

    :param frame: Narwhals LazyFrame containing the column to check.
    :param key: Name of the column to check.
    :param min_value: Minimum length of strings (inclusive).
        (default: no minimum)
    :param max_value: Maximum length of strings (inclusive).
        (default: no maximum)
    :param exact_value: Exact length of strings. (default: no exact value)
    """
    n_chars = nw.col(key).str.len_chars()
    if exact_value is not None:
        return frame.select(n_chars == exact_value)

    if min_value is None and max_value is None:
        raise ValueError(
            "Must provide at least one of 'min_value' and 'max_value'"
        )
    elif min_value is None:
        return frame.select(n_chars <= max_value)
    elif max_value is None:
        return frame.select(n_chars >= min_value)
    else:
        return frame.select(
            n_chars.is_between(min_value, max_value, closed="both")
        )
