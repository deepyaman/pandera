---
phase: 5
slug: expression-based-check-protocol-eliminate-framework-specific-apply-branching
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | pyproject.toml |
| **Quick run command** | `python -m pytest tests/backends/narwhals/test_checks.py -q` |
| **Full suite command** | `python -m pytest tests/backends/narwhals/ -q` |
| **Estimated runtime** | ~5 seconds (quick), ~10 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/backends/narwhals/test_checks.py -q`
- **After every plan wave:** Run `python -m pytest tests/backends/narwhals/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | EXPR-01 | unit/RED | `python -m pytest tests/backends/narwhals/test_checks.py -q` | ✅ | ⬜ pending |
| 05-02-01 | 02 | 2 | EXPR-01..03 | unit/GREEN | `python -m pytest tests/backends/narwhals/test_checks.py -q` | ✅ | ⬜ pending |
| 05-02-02 | 02 | 2 | EXPR-04 | integration | `python -m pytest tests/backends/narwhals/ -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing test infrastructure covers all phase requirements.
- Wave 1 adds RED stubs to `tests/backends/narwhals/test_checks.py` before implementation.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
