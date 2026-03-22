# Roadmap: Pandera Narwhals Backend

## Milestones

- ✅ **v1.0 Narwhals Backend** — Phases 1-5 (shipped 2026-03-15)

## Phases

<details>
<summary>✅ v1.0 Narwhals Backend (Phases 1-5) — SHIPPED 2026-03-15</summary>

- [x] Phase 1: Foundation (2/2 plans) — completed 2026-03-09
- [x] Phase 2: Check Backend (3/3 plans) — completed 2026-03-10
- [x] Phase 3: Column Backend (2/2 plans) — completed 2026-03-14
- [x] Phase 4: Container Backend and Polars Registration (5/5 plans) — completed 2026-03-14
- [x] Phase 5: Ibis Registration and Integration (6/6 plans) — completed 2026-03-15

See `.planning/milestones/v1.0-ROADMAP.md` for full phase details.

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 2/2 | Complete | 2026-03-09 |
| 2. Check Backend | 1/2 | In Progress|  | 2026-03-10 |
| 3. Column Backend | v1.0 | 2/2 | Complete | 2026-03-14 |
| 4. Container Backend and Polars Registration | v1.0 | 5/5 | Complete | 2026-03-14 |
| 5. Ibis Registration and Integration | v1.0 | 6/6 | Complete | 2026-03-15 |

### Phase 1: PR Review Architecture Fixes

**Goal:** Address architectural feedback from PR Review #2223 — separate ibis logic from base ErrorHandler, create NarwhalsErrorHandler, remove polars-specific coupling from narwhals container backend, fix misleading comments, and fix Narwhals capitalization.
**Requirements**: ARCH-01, ARCH-02, ARCH-03, ARCH-04
**Depends on:** v1.0 Narwhals Backend
**Plans:** 3 plans

Plans:
- [x] 01-01-PLAN.md — ErrorHandler architecture: strip ibis from base, create NarwhalsErrorHandler (1/1 complete)
- [x] 01-02-PLAN.md — Wire NarwhalsErrorHandler into backends, fix container polars coupling, fix comment, fix capitalization
- [x] 01-03-PLAN.md — Gap closure: fix validate() premature materialization, remaining capitalization nits, ROADMAP marker

### Phase 2: Remaining PR Review Fixes

**Goal:** Address the remaining unresolved PR #2223 review comments — redesign horizontal concat in checks/components, remove Polars-specific code from postprocess_bool_output, investigate custom checks Ibis delegation, and fix backend-specific dtype logic in check_dtype.
**Requirements**: TBD
**Depends on:** Phase 1
**Plans:** 1/2 plans executed

Plans:
- [ ] 02-01-PLAN.md — checks.py: replace horizontal concat with with_columns, replace polars import in postprocess_bool_output, document IbisCheckBackend delegation
- [ ] 02-02-PLAN.md — components.py: refactor check_nullable to with_columns, simplify check_dtype to single narwhals-engine pass

### Phase 3: Fix IbisCheckBackend delegation via apply() type-dispatch

**Goal:** Remove IbisCheckBackend delegation from NarwhalsCheckBackend by introducing a native flag on Check that controls what apply() passes to the check function. Unify the calling convention for all checks to check_fn(frame, key). No new user-facing capabilities — purely architectural clean-up.
**Requirements**: TBD
**Depends on:** Phase 2
**Plans:** 2 plans

Plans:
- [ ] 03-01-PLAN.md — Add native param to Check, propagate native=False for builtins, refactor all 14 builtin check signatures
- [ ] 03-02-PLAN.md — Rewrite apply() with native-flag dispatch, remove ibis delegation from __call__, add normalization helper and tests
