---
phase: 1
slug: pr-review-architecture-fixes
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-21
validated: 2026-03-24
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | setup.cfg / pyproject.toml |
| **Quick run command** | `python -m pytest tests/backends/narwhals/test_phase01_arch.py -v` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -k "narwhals or error_handler" -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | ARCH-01 | unit | `pytest tests/backends/narwhals/test_phase01_arch.py::test_base_error_handler_has_no_ibis_references -v` | ✅ | ✅ green |
| 1-01-02 | 01 | 1 | ARCH-01 | unit | `pytest tests/backends/narwhals/test_phase01_arch.py::test_narwhals_error_handler_is_subclass_of_base -v` | ✅ | ✅ green |
| 1-02-01 | 02 | 2 | ARCH-02, ARCH-03 | unit | `pytest tests/backends/narwhals/test_phase01_arch.py -k "error_handler or narwhals_error" -v` | ✅ | ✅ green |
| 1-02-02 | 02 | 2 | ARCH-04 | unit | `pytest tests/backends/narwhals/test_phase01_arch.py::test_container_has_no_polars_issubclass_check_in_to_frame_kind -v` | ✅ | ✅ green |
| 1-03-01 | 03 | 3 | ARCH-02 | unit | `pytest tests/backends/narwhals/test_phase01_arch.py::test_validate_does_not_materialize_before_subsample -v` | ✅ | ✅ green |
| 1-03-02 | 03 | 3 | ARCH-04 | unit | `pytest tests/backends/narwhals/test_phase01_arch.py::test_validate_lazyframe_returns_lazyframe tests/backends/narwhals/test_phase01_arch.py::test_validate_dataframe_returns_dataframe -v` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.*

---

## Known Implementation Issues

| Issue ID | Description | Test | Severity |
|----------|-------------|------|----------|
| IMPL-01 | `NarwhalsErrorHandler._count_failure_cases` crashes on string failure_cases via `nw.from_native(str)` | `test_narwhals_error_handler_counts_string_as_one` (xfail) | medium — causes `test_parity.py::test_custom_check_ibis_lazy` to fail |

The plan (01-01-PLAN.md Task 2) required `NarwhalsErrorHandler` to fall back to base class for non-frame failure_cases (strings, scalars). The implementation replaced the guarded fallback with a bare `nw.from_native()` call that only handles frame types. Strings passed as `failure_cases` (column names, dtype strings, error messages) cause `TypeError: Unsupported dataframe type, got: <class 'str'>`.

**Fix required in:** `pandera/api/narwhals/error_handler.py` — add try/except TypeError to fall back to `_ErrorHandler._count_failure_cases(failure_cases)`.

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-03-24 (12 green, 1 xfail for known impl bug IMPL-01)
