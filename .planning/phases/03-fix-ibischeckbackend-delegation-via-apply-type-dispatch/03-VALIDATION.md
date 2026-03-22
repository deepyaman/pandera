---
phase: 3
slug: fix-ibischeckbackend-delegation-via-apply-type-dispatch
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/core/test_checks.py -x -q` |
| **Full suite command** | `pytest tests/core/test_checks.py tests/backends/ -x -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/core/test_checks.py -x -q`
- **After every plan wave:** Run `pytest tests/core/test_checks.py tests/backends/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | builtin-sig | unit | `pytest tests/core/test_checks.py -x -q` | ✅ | ⬜ pending |
| 3-01-02 | 01 | 1 | builtin-sig | unit | `pytest tests/core/test_checks.py -x -q` | ✅ | ⬜ pending |
| 3-02-01 | 02 | 1 | dispatch-remove | unit | `pytest tests/core/test_checks.py -x -q` | ✅ | ⬜ pending |
| 3-02-02 | 02 | 2 | ibis-normalize | unit | `pytest tests/backends/ -x -q -k ibis` | ✅ | ⬜ pending |
| 3-02-03 | 02 | 2 | ibis-normalize | integration | `pytest tests/backends/ -x -q -k ibis` | ✅ | ⬜ pending |

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
