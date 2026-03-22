---
phase: 4
slug: lazy-postprocess-always-lazy-failure-cases
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/backends/narwhals/test_checks.py tests/backends/narwhals/test_e2e.py -x -q` |
| **Full suite command** | `pytest tests/backends/narwhals/ -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/backends/narwhals/test_checks.py tests/backends/narwhals/test_e2e.py -x -q`
- **After every plan wave:** Run `pytest tests/backends/narwhals/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 0 | LAZY-01,02,03,07,08 | unit stubs | `pytest tests/backends/narwhals/test_checks.py -x -q` | ❌ W0 | ⬜ pending |
| 4-01-02 | 01 | 0 | LAZY-04,05 | e2e update | `pytest tests/backends/narwhals/test_e2e.py -k "TestBuiltinChecksIbis" -x -q` | ✅ needs update | ⬜ pending |
| 4-01-03 | 01 | 1 | LAZY-01 | unit | `pytest tests/backends/narwhals/test_checks.py -k "apply" -x -q` | ❌ W0 | ⬜ pending |
| 4-01-04 | 01 | 1 | LAZY-02,03 | unit | `pytest tests/backends/narwhals/test_checks.py -k "postprocess_lazy" -x -q` | ❌ W0 | ⬜ pending |
| 4-01-05 | 01 | 1 | LAZY-07,08 | unit | `pytest tests/backends/narwhals/test_checks.py -k "ignore_na or n_failure_cases" -x -q` | ❌ W0 | ⬜ pending |
| 4-01-06 | 01 | 2 | LAZY-04,05 | e2e | `pytest tests/backends/narwhals/test_e2e.py -k "TestBuiltinChecksIbis" -x -q` | ✅ updated | ⬜ pending |
| 4-01-07 | 01 | 2 | LAZY-06 | e2e regression | `pytest tests/backends/narwhals/test_e2e.py -k "TestBuiltinChecksPolars" -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/backends/narwhals/test_checks.py` — stubs for LAZY-01 (apply returns wide table)
- [ ] `tests/backends/narwhals/test_checks.py` — stubs for LAZY-02,03 (no materialization in postprocess for polars/ibis)
- [ ] `tests/backends/narwhals/test_checks.py` — stubs for LAZY-07 (ignore_na stays lazy)
- [ ] `tests/backends/narwhals/test_checks.py` — stubs for LAZY-08 (n_failure_cases limits lazily)
- [ ] `tests/backends/narwhals/test_e2e.py` — update `test_greater_than_fails_failure_cases_type` assertion (LAZY-04)
- [ ] `tests/backends/narwhals/test_e2e.py` — update `test_greater_than_fails_failure_cases_values` to use `nw.to_native(fc).execute()` (LAZY-05)

*Existing infrastructure covers the test framework — no new installs needed.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
