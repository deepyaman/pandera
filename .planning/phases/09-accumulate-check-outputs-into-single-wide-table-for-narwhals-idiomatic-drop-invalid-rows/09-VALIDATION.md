---
phase: 9
slug: accumulate-check-outputs-into-single-wide-table-for-narwhals-idiomatic-drop-invalid-rows
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `python -m pytest tests/backends/narwhals/ tests/polars/test_polars_container.py tests/ibis/test_ibis_container.py -x -q` |
| **Full suite command** | `python -m pytest tests/backends/narwhals/ tests/polars/test_polars_container.py tests/ibis/test_ibis_container.py -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 9-01-01 | 01 | 1 | RED baseline | unit | `python -m pytest tests/polars/test_polars_container.py -k "drop_invalid" tests/ibis/test_ibis_container.py -k "drop_invalid" -v` | ✅ | ⬜ pending |
| 9-02-01 | 02 | 2 | apply() Expr | unit | `python -m pytest tests/backends/narwhals/ -x -q` | ✅ | ⬜ pending |
| 9-02-02 | 02 | 2 | drop_invalid_rows | integration | `python -m pytest tests/polars/test_polars_container.py -k "drop_invalid" tests/ibis/test_ibis_container.py -k "drop_invalid" -v` | ✅ | ⬜ pending |
| 9-02-03 | 02 | 2 | no regressions | suite | `python -m pytest tests/backends/narwhals/ tests/polars/test_polars_container.py tests/ibis/test_ibis_container.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
