---
phase: 8
slug: fix-lazy-true-critical-regressions
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/backends/narwhals/test_lazy_regressions.py -x -q` |
| **Full suite command** | `pytest tests/backends/narwhals/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/backends/narwhals/test_lazy_regressions.py -x -q`
- **After every plan wave:** Run `pytest tests/backends/narwhals/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 8-01-01 | 01 | 1 | MISSING-01 | unit | `pytest tests/backends/narwhals/test_lazy_regressions.py -k "failure_cases_metadata" -x -q` | ❌ W0 | ⬜ pending |
| 8-01-02 | 01 | 1 | MISSING-02 | unit | `pytest tests/backends/narwhals/test_lazy_regressions.py -k "count_failure_cases" -x -q` | ❌ W0 | ⬜ pending |
| 8-02-01 | 02 | 2 | MISSING-01 | integration | `pytest tests/backends/narwhals/test_lazy_regressions.py -k "polars_lazy" -x -q` | ❌ W0 | ⬜ pending |
| 8-02-02 | 02 | 2 | MISSING-01 | integration | `pytest tests/backends/narwhals/test_lazy_regressions.py -k "ibis_lazy" -x -q` | ❌ W0 | ⬜ pending |
| 8-02-03 | 02 | 2 | MISSING-02 | integration | `pytest tests/backends/narwhals/test_lazy_regressions.py -k "bool_scalar" -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/backends/narwhals/test_lazy_regressions.py` — stubs for MISSING-01, MISSING-02

*Existing pytest infrastructure (conftest.py, fixtures) covers all other needs.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
