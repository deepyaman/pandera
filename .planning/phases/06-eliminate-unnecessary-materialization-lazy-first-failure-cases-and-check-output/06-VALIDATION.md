---
phase: 6
slug: eliminate-unnecessary-materialization-lazy-first-failure-cases-and-check-output
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/backends/narwhals/ -x -q` |
| **Full suite command** | `pytest tests/backends/narwhals/ -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/backends/narwhals/ -x -q`
- **After every plan wave:** Run `pytest tests/backends/narwhals/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 6-01-01 | 01 | 1 | lazy-first run_check | unit | `pytest tests/backends/narwhals/test_checks.py -x -q` | ✅ | ⬜ pending |
| 6-01-02 | 01 | 1 | failure_cases narwhals wrapper | unit | `pytest tests/backends/narwhals/test_checks.py -x -q` | ✅ | ⬜ pending |
| 6-01-03 | 01 | 1 | subsample lazy head/tail | unit | `pytest tests/backends/narwhals/test_components.py -x -q` | ❌ W0 | ⬜ pending |
| 6-01-04 | 01 | 1 | check_nullable scalar-only materialize | unit | `pytest tests/backends/narwhals/test_components.py -x -q` | ✅ | ⬜ pending |
| 6-02-01 | 02 | 2 | failure_cases_metadata ibis return type | unit | `pytest tests/backends/narwhals/ -k failure_cases_metadata -x -q` | ❌ W0 | ⬜ pending |
| 6-02-02 | 02 | 2 | failure_cases_metadata polars-lazy return type | unit | `pytest tests/backends/narwhals/ -k failure_cases_metadata -x -q` | ❌ W0 | ⬜ pending |
| 6-03-01 | 03 | 3 | SchemaError.failure_cases native polars | e2e | `pytest tests/backends/narwhals/test_e2e.py -x -q` | ✅ | ⬜ pending |
| 6-03-02 | 03 | 3 | SchemaError.failure_cases native ibis.Table | e2e | `pytest tests/backends/narwhals/test_e2e.py -x -q` | ✅ | ⬜ pending |
| 6-03-03 | 03 | 3 | SchemaErrors.failure_cases ibis lazy | e2e | `pytest tests/backends/narwhals/test_e2e.py -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/backends/narwhals/test_components.py` — new tests for `subsample()` lazy head/tail and NotImplementedError for ibis tail=
- [ ] `tests/backends/narwhals/test_checks.py` or new test — new test for `failure_cases_metadata()` with ibis input asserting ibis.Table return type

*Existing infrastructure covers the rest; assertions need updating not new files.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `_is_ibis_result` block fully deleted | lazy-first principle | Code review / grep | `grep -r "_is_ibis_result" pandera/` should return no results |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
