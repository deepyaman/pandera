---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: Tech Debt Cleanup
current_plan: 2 of 3
status: completed
stopped_at: Completed 08-fix-lazy-true-critical-regressions/08-02-PLAN.md
last_updated: "2026-03-25T02:13:50.613Z"
last_activity: 2026-03-23 — Plan 06-02 complete (run_check unified, check_nullable scalar-only, SchemaError.failure_cases now native pl.DataFrame/ibis.Table)
progress:
  total_phases: 8
  completed_phases: 8
  total_plans: 20
  completed_plans: 20
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-15 after v1.0 milestone)

**Core value:** Users can validate any Narwhals-supported dataframe library through a single, consistent backend — reducing maintenance burden and unlocking lazy validation and future library support for free.
**Current focus:** Remaining PR Review Fixes (Phase 02) — eliminating polars-specific coupling and fragile concat in checks.py, plus custom checks delegation and check_dtype backend logic.

## Current Position

Phase: 06-eliminate-unnecessary-materialization-lazy-first-failure-cases-and-check-output
Current Plan: 2 of 3
Status: Plan 06-02 complete — run_check unified (no _is_ibis_result), check_nullable scalar-only, SchemaError.failure_cases now native
Last activity: 2026-03-23 — Plan 06-02 complete (run_check unified, check_nullable scalar-only, SchemaError.failure_cases now native pl.DataFrame/ibis.Table)

Progress: [██████████] 100%

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
- [Phase 04-03]: isinstance(fc, nw.LazyFrame) in run_check distinguishes polars (LazyFrame from filter → collect) from ibis (DataFrame wrapping ibis.Table → keep lazy)
- [Phase 04-03]: to_arrow() + pl.from_arrow() in failure_cases_metadata is backend-agnostic: _materialize produces eager nw.DataFrame, to_arrow extracts Arrow, pl.from_arrow converts to polars — zero ibis/pyarrow isinstance needed
- [Phase 04-03]: NarwhalsErrorHandler._count_failure_cases extended to handle nw.DataFrame wrapping ibis.Table (nw.to_native → ibis.Table.count().to_pyarrow().as_py())
- [Phase 05]: Use _function_registry.get(nw.Expr) in RED baseline test to avoid KeyError before migration — test FAILs at assertion, not ERRORs at setup
- [Phase 05-02]: Transitional state accepted — apply() still calls fn(frame, key) causing KeyError until Plan 05-03 rewires apply() to use nw.Expr protocol
- [Phase 05-02]: No frame.select() inside any builtin — return expression directly; Dispatcher auto-rekeys to nw.Expr via first-param annotation reflection
- [Phase 05-03]: element_wise try/except wraps frame.with_columns() call — NotImplementedError fires at evaluation time in narwhals for SQL-lazy backends, not at map_batches construction
- [Phase 05-03]: _normalize_native_output ir.BooleanColumn uses native.mutate(**{CHECK_OUTPUT_KEY: out}) to produce wide table — native.select() produced 1-column frame that broke postprocess_lazyframe_output's failure_cases.select(key) after removal of old reassembly block
- [Phase 06-01 RED baseline]: SchemaError.failure_cases Phase 6 contract is native (pl.DataFrame for polars, ibis.Table for ibis) — not nw.DataFrame wrapper; consistent with polars backend behavior
- [Phase 06-01 RED baseline]: SchemaErrors.failure_cases Phase 6 contract: ibis.Table for ibis inputs — failure_cases_metadata() must not force pl.DataFrame conversion via to_arrow()+pl.from_arrow()
- [Phase 06-01 RED baseline]: subsample() Phase 6 contract: head= and tail= stay lazy (nw.LazyFrame for polars); ibis tail= raises NotImplementedError matching element_wise pattern
- [Phase 06-02]: ibis nw.LazyFrame failure_cases: nw.to_native(lf) gives ibis.Table without execution — hasattr(native, "execute") detects ibis, skips _materialize() to avoid pyarrow detour
- [Phase 06-02]: failure_cases_metadata handles native ibis.Table: wrap to nw.from_native() to reuse existing narwhals materialization path — avoids duplicating pl.from_arrow conversion
- [Phase 06-02]: NarwhalsErrorHandler._count_failure_cases: ibis.Table.count().execute() is the correct count — ibis.Table.__len__() raises ExpressionError
- [Phase 06]: _is_lazy_or_sql() helper: isinstance(fc, nw.LazyFrame) OR ibis nw.DataFrame with hasattr(execute) — detects both polars-lazy and SQL-lazy; container.py boundary unwrap uses same manual detection pattern as components.py since _to_native(nw.LazyFrame) returns pl.LazyFrame uncollected; nw.DataFrame.lazy() works for ibis, subsample normalization unchanged
- [Phase 07]: nw.from_native(failure_cases, eager_only=False) is the correct unified pattern for _count_failure_cases — accepts pl.DataFrame, pl.LazyFrame, and ibis.Table without backend-specific isinstance branches
- [Phase 07]: _materialize import removed from error_handler.py — Phase 6 contract ensures failure_cases is always native at SchemaError boundary, so nw.from_native wrapping handles all types
- [Phase 07]: ROADMAP progress table restructured to reflect current 7-phase layout (v1.0 milestones moved to details block)
- [Phase 08-fix-lazy-true-critical-regressions]: ibis MISSING-01 test is GREEN (Phase 6 already fixed ibis.Table rewrap); MISSING-02 requires native=True bool-returning check to trigger failure_cases=False path
- [Phase 08-fix-lazy-true-critical-regressions]: pl.DataFrame routes to eager polars path in failure_cases_metadata — _is_lazy_or_sql returns False for nw.DataFrame wrapping pl.DataFrame (no .execute()); failure_case column is Utf8 by design
- [Phase 08-fix-lazy-true-critical-regressions]: isinstance(failure_cases, str) guard removed from _count_failure_cases — dead code after try/except TypeError since nw.from_native(str) also raises TypeError, returning 1 via except branch

### Roadmap Evolution

- Phase 01 added: PR Review Architecture Fixes (4 plans)
- v1.0 milestone complete (5 phases, 18 plans)
- Phase 05 added: Expression-based check protocol — eliminate framework-specific apply() branching
- Phase 02 added: Remaining PR Review Fixes (horizontal concat, postprocess_bool_output polars code, custom checks delegation, check_dtype backend logic)
- Phase 03 added: Fix IbisCheckBackend delegation (approach TBD at planning time)
- Phase 06 added: Eliminate unnecessary materialization — lazy-first failure_cases and check_output

### Pending Todos

None.

### Blockers/Concerns

- coerce for Ibis is xfail(strict=True) — intentional v2 feature gate
- `drop_invalid_rows` for Ibis uses IbisSchemaBackend delegation — no narwhals abstraction
- 95 pre-existing ibis test failures unrelated to ErrorHandler changes (ibis backend integration issues)

## Session Continuity

Last session: 2026-03-25T02:09:55.492Z
Stopped at: Completed 08-fix-lazy-true-critical-regressions/08-02-PLAN.md
Resume file: None
