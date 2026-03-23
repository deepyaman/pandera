---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_plan: 2 of 3
status: in-progress
stopped_at: Completed 04-02-PLAN.md
last_updated: "2026-03-23T02:18:00.000Z"
last_activity: 2026-03-23 — Plan 04-02 complete (wide-table apply(), lazy postprocess_lazyframe_output, all 28 builtin check tests pass)
progress:
  total_phases: 4
  completed_phases: 3
  total_plans: 10
  completed_plans: 9
  percent: 90
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-15 after v1.0 milestone)

**Core value:** Users can validate any Narwhals-supported dataframe library through a single, consistent backend — reducing maintenance burden and unlocking lazy validation and future library support for free.
**Current focus:** Remaining PR Review Fixes (Phase 02) — eliminating polars-specific coupling and fragile concat in checks.py, plus custom checks delegation and check_dtype backend logic.

## Current Position

Phase: 04-lazy-postprocess-always-lazy-failure-cases
Current Plan: 2 of 3
Status: Plan 04-02 complete — apply() returns wide table, postprocess_lazyframe_output fully lazy
Last activity: 2026-03-23 — Plan 04-02 complete (wide-table apply(), lazy postprocess, all 28 builtin check tests pass)

Progress: [█████████░] 87%

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

Phase 03 decisions:
- native=False is placed before **kws in from_builtin_check_name cls() call — explicit keyword cannot be overridden by user-provided kwargs
- NarwhalsData import removed from builtin_checks.py — was only needed as a type annotation, no longer used after signature refactor
- test_builtin_checks_pass/fail are expected RED after plan 03-01 — plan 03-02 fixes apply() dispatch to call check_fn(frame, key) via native=False path
- [Phase 03]: Dispatcher used in native=False branch for ibis nw.DataFrame frames: look up nw.LazyFrame impl directly and call with partial kwargs to avoid KeyError
- [Phase 03]: postprocess_bool_output falls back to polars LazyFrame when nw.from_dict fails for ibis SQL-lazy backends
- [Phase 04-lazy-postprocess-always-lazy-failure-cases]: xfail(strict=False) used for polars postprocess stubs because polars path already returns nw.DataFrame from _materialize(); ibis path is the real bug target
- [Phase 04-lazy-postprocess-always-lazy-failure-cases]: TestBuiltinChecksPolars failure_cases assertions updated to nw.DataFrame alongside ibis — both must be RED before Phase 4 removes _to_native
- [Phase 04-02]: ibis wide-table via row_number join — narwhals cannot pass a Series from one ibis relation into with_columns of another; native ibis row_number().over(window()) join is the correct approach
- [Phase 04-02]: Backend detection via hasattr(nw.to_native(out), 'execute') — polars pl.LazyFrame has no .execute(); ibis.Table does — cleanly separates the two paths
- [Phase 04-02]: element_wise .select(selector) kept — plan said to drop it but removing would feed non-bool data columns through all_horizontal; narrow extraction before wide-table re-attachment is necessary

### Roadmap Evolution

- Phase 01 added: PR Review Architecture Fixes (4 plans)
- v1.0 milestone complete (5 phases, 18 plans)
- Phase 02 added: Remaining PR Review Fixes (horizontal concat, postprocess_bool_output polars code, custom checks delegation, check_dtype backend logic)
- Phase 03 added: Fix IbisCheckBackend delegation (approach TBD at planning time)

### Pending Todos

None.

### Blockers/Concerns

- coerce for Ibis is xfail(strict=True) — intentional v2 feature gate
- `drop_invalid_rows` for Ibis uses IbisSchemaBackend delegation — no narwhals abstraction
- 95 pre-existing ibis test failures unrelated to ErrorHandler changes (ibis backend integration issues)

## Session Continuity

Last session: 2026-03-23T02:18:00.000Z
Stopped at: Completed 04-02-PLAN.md
Resume file: None
