---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_plan: 1 of 3
status: in_progress
stopped_at: Completed 02-remaining-pr-review-fixes/02-01-PLAN.md
last_updated: "2026-03-22T15:09:00.000Z"
last_activity: 2026-03-22 — Plan 02-01 complete (NarwhalsCheckBackend refactor)
progress:
  total_phases: 2
  completed_phases: 1
  total_plans: 6
  completed_plans: 4
  percent: 67
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-15 after v1.0 milestone)

**Core value:** Users can validate any Narwhals-supported dataframe library through a single, consistent backend — reducing maintenance burden and unlocking lazy validation and future library support for free.
**Current focus:** Remaining PR Review Fixes (Phase 02) — eliminating polars-specific coupling and fragile concat in checks.py, plus custom checks delegation and check_dtype backend logic.

## Current Position

Phase: 02-remaining-pr-review-fixes
Current Plan: 1 of 3
Status: Plan 02-01 complete — NarwhalsCheckBackend refactored
Last activity: 2026-03-22 — Plan 02-01 complete (NarwhalsCheckBackend refactor)

Progress: [███████░░░] 67%

## Accumulated Context

### Decisions

Previous milestone decisions (v1.0):
- Auto-detection via try/except in `register_polars_backends()` / `register_ibis_backends()` (not config flags)
- Direct BACKEND_REGISTRY writes required to override existing entries
- `group_by().agg(nw.len())` for SQL-lazy uniqueness checks
- Dual ibis.Table / pyarrow.Table detection in `failure_cases_metadata`
- try/except ImportError guard for optional ibis in shared code

Phase 01 decisions:
- NarwhalsErrorHandler uses guarded try/except ImportError for ibis — ibis remains optional dependency
- Fallback to _ErrorHandler._count_failure_cases() in NarwhalsErrorHandler avoids duplicating len()/None logic
- Base ErrorHandler must have zero knowledge of ibis — all backend-specific logic lives in subclasses
- hasattr(return_type, "collect") on the class (not instance) correctly distinguishes lazy (pl.LazyFrame) from eager (pl.DataFrame/ibis.Table) return types without importing polars
- Dynamic Column import via schema.__class__.__module__ check avoids hardcoding polars in a backend-agnostic method
- [Phase 01-pr-review-architecture-fixes]: subsample() receives nw.LazyFrame directly; _to_frame_kind_nw deferred to return statements only — no native round-trips before checks
- [Phase 01-pr-review-architecture-fixes]: drop_invalid_rows branch creates check_obj_parsed locally via _to_frame_kind_nw and returns immediately

Phase 02 decisions:
- data_df.with_columns(results_df[CHECK_OUTPUT_KEY]) is the correct pattern for column attachment — avoids positional alignment brittleness of horizontal concat
- nw.get_native_namespace(frame) + nw.from_dict(...).lazy() creates backend-agnostic LazyFrames without importing polars directly

### Roadmap Evolution

- Phase 01 added: PR Review Architecture Fixes (4 plans)
- v1.0 milestone complete (5 phases, 18 plans)
- Phase 02 added: Remaining PR Review Fixes (horizontal concat, postprocess_bool_output polars code, custom checks delegation, check_dtype backend logic)

### Pending Todos

None.

### Blockers/Concerns

- coerce for Ibis is xfail(strict=True) — intentional v2 feature gate
- `drop_invalid_rows` for Ibis uses IbisSchemaBackend delegation — no narwhals abstraction
- 95 pre-existing ibis test failures unrelated to ErrorHandler changes (ibis backend integration issues)

## Session Continuity

Last session: 2026-03-22T15:09:00.000Z
Stopped at: Completed 02-remaining-pr-review-fixes/02-01-PLAN.md
Resume file: .planning/phases/02-remaining-pr-review-fixes/02-01-SUMMARY.md
