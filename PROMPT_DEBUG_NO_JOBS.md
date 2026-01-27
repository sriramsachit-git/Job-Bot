# Debug Prompt: "No Jobs" in Job Search Pipeline

**Copy the prompt below and give it to a new agent (or Cursor) to debug why the workflow returns no jobs.**

---

## Quick copy-paste (single block)

Paste the following into a new Cursor agent or chat:

```
You are debugging a "no jobs" bug in a job search pipeline. When we run the workflow via Swagger UI (POST /api/search/start → poll GET /api/search/{id}/status → GET /api/jobs), we get zero jobs. Fix it.

Project layout: Backend FastAPI in backend/app/ (API, async pipeline, DB). Sync pipeline in src/ — pipeline.py, search.py (Google Custom Search), extractor.py (Jina/Playwright), llm_parser.py (OpenAI), storage.py (SQLite), filters.py, pre_filters.py, config.py. Config via .env: GOOGLE_API_KEY, GOOGLE_CSE_ID, OPENAI_API_KEY.

Flow: (1) POST /api/search/start kicks off AsyncSearchPipeline, which runs sync JobSearchPipeline in a thread. (2) Sync pipeline: Google search → early filter → extract job pages → pre-filter → LLM parse → final filter → save to SQLite. (3) If saved > 0, async pipeline reads new_jobs from SQLite, maps to ParsedJob, calls JobService.save_jobs_batch to write to async DB. (4) GET /api/jobs reads only from async DB.

Where jobs can be lost: Google returns 0 URLs (API keys, CSE, quota); early filter drops all; extraction fails for all; pre-filter drops all; LLM parse fails; final filter drops all; all duplicates so save_batch saves 0; or async copy (new_jobs → JobService) never runs or errors. Two DBs: SQLite (data/jobs.db) vs async DB used by FastAPI. Jobs must be copied SQLite → async DB.

Your tasks: (1) Add or use logging at each stage (search count, after early filter, after extract, pre-filter, parse, final filter, save_batch, new_jobs length, JobService save/skip) and find the first stage that goes to zero. (2) Verify env vars and CSE setup. (3) Inspect SQLite jobs, unextracted_jobs, pre_filtered_jobs and compare with async DB. (4) Fix the root cause and ensure API filters (if any) are passed into the sync pipeline where intended. (5) Success: one full Swagger run yields at least one job when Google/extraction return results and filters don't exclude everything.

Key files: backend/app/core/pipeline.py (async wrapper), src/pipeline.py (JobSearchPipeline.run), backend/app/services/job_service.py (save_jobs_batch), src/storage.py (get_new_jobs_since). See PROMPT_DEBUG_NO_JOBS.md and SWAGGER_WORKFLOW_STEPS.md in the repo for full detail.
```

---

## Full prompt (detailed)

## Prompt Start

```
You are debugging a "no jobs" bug in a job search pipeline. When we run the workflow via Swagger UI (POST /api/search/start → poll GET /api/search/{id}/status → GET /api/jobs), we get zero jobs. Fix it.

## Project layout
- **Backend (FastAPI)**: `backend/app/` — API routes, services, async pipeline, Postgres/SQLite DB.
- **Sync pipeline**: `src/` — `pipeline.py` (orchestrator), `search.py` (Google Custom Search), `extractor.py` (Jina/Playwright), `llm_parser.py` (OpenAI), `storage.py` (SQLite), `filters.py`, `pre_filters.py`, `config.py`.
- **Config**: `src/config.py` uses env vars; `.env` at project root. Required: `GOOGLE_API_KEY`, `GOOGLE_CSE_ID`, `OPENAI_API_KEY`.

## How the workflow works
1. **POST /api/search/start** — Creates a SearchSession, starts `AsyncSearchPipeline.run_search` in a background task.
2. **Async pipeline** (`backend/app/core/pipeline.py`) runs the **sync** `JobSearchPipeline` (`src/pipeline.py`) in a thread pool via `run_in_executor`. The sync pipeline:
   - **Step 1**: `GoogleJobSearch.search_jobs()` — Google Custom Search API, returns URLs (stored in `summary["searched"]`).
   - **Step 1.5**: Early filter (`filters.should_skip_early`) — keyword/location; can drop all.
   - **Step 2**: `ContentExtractor.extract_batch()` — Fetches job pages (Jina Reader / Playwright). Failures → `unextracted_jobs` table.
   - **Step 3**: Pre-parse filter (`PreParseFilter.filter_batch`) — e.g. max YOE; can drop all.
   - **Step 4**: `JobParser.parse_batch()` — OpenAI LLM parsing.
   - **Step 5**: `JobFilter.filter_jobs()` — min_score, USA-only; can drop all.
   - **Step 6**: `JobDatabase.save_batch()` — Saves to **SQLite** (`data/jobs.db`). Dedupe by URL.
3. **After sync pipeline returns**: If `summary["saved"] > 0`, the async pipeline reads `summary["new_jobs"]` (from `JobDatabase.get_new_jobs_since()`), converts to `ParsedJob`, and calls `JobService.save_jobs_batch(db, ...)` to persist into the **FastAPI/async DB** (used by `GET /api/jobs`).
4. **GET /api/search/{id}/status** — Returns `urls_found`, `jobs_extracted`, `jobs_parsed`, `jobs_saved` from `SearchSession`. These are updated from `summary` (searched, extracted, parsed, saved) **only at the end** when the pipeline completes; intermediate progress is limited.
5. **GET /api/jobs** — Reads from the **async DB** only. If no jobs were ever saved there, this returns empty.

## Where "no jobs" can come from
- **Google search**: No URLs (`searched == 0`). Causes: missing/wrong `GOOGLE_API_KEY` or `GOOGLE_CSE_ID`, CSE not set up for job domains, quota, or query/sites returning nothing.
- **Early filtering**: All URLs dropped by `should_skip_early` (keywords, location).
- **Extraction**: All pages fail (Jina/Playwright issues, timeouts, etc.). Check `unextracted_jobs` in SQLite.
- **Pre-filter**: All dropped by YOE or other pre-parse rules.
- **LLM parsing**: All fail (OpenAI key, rate limits, or parse errors).
- **Final filter**: All dropped by `filter_jobs` (min_score too high, USA-only, etc.).
- **All duplicates**: `save_batch` saves 0 (all URLs already in SQLite). Then `new_jobs` is empty, so nothing is written to async DB.
- **Async DB never receives jobs**: Sync pipeline saves to SQLite only. Async pipeline copies to async DB only when `saved > 0` and `new_jobs` is non-empty. Bugs in mapping, or in `JobService.save_jobs_batch`, or silent exceptions can prevent async DB from getting any jobs.
- **SearchSession update bug**: Status/results might show completed but with wrong counts; or the frontend could be checking the wrong DB. Verify with direct API calls.

## API → pipeline wiring quirks
- **POST /api/search/start** body: `job_titles`, `domains`, optional `filters` (`SearchFilters`: max_yoe, remote_only, locations, excluded_keywords). The sync pipeline is called with `job_titles` → keywords, `domains` → sites. **`filters` from the API do NOT currently include `num_results`, `date_restrict`, or `min_score`.** The async pipeline uses `filters.get("num_results", 50)`, `filters.get("date_restrict", "d1")`, `filters.get("min_score", 30)`. So those effectively use defaults. The sync pipeline uses `USER_PROFILE` and internal config for filtering; API `filters` (max_yoe, etc.) may not be passed through to the sync pipeline at all. Confirm and fix if we want API filters to affect the search.
- **Two databases**: (1) SQLite `data/jobs.db` used by `JobDatabase` in `src/storage.py`; (2) Async DB used by FastAPI (`app.database`). `GET /api/jobs` reads only from the async DB. Jobs must be copied from SQLite → async DB by the async pipeline.

## What you must do
1. **Add logging** (or inspect existing logs) around: (a) Google search result count, (b) after early filter, (c) after extraction, (d) after pre-filter, (e) after LLM parse, (f) after final filter, (g) `save_batch` saved/skipped counts, (h) `new_jobs` length, (i) `JobService.save_jobs_batch` saved/skipped. Identify the **first** stage where counts drop to zero.
2. **Verify env**: `GOOGLE_API_KEY`, `GOOGLE_CSE_ID`, `OPENAI_API_KEY` set and correct. Ensure the Custom Search Engine is configured for job-related sites and returns results for test queries.
3. **Check SQLite**: Inspect `data/jobs.db` — `jobs`, `unextracted_jobs`, `pre_filtered_jobs` tables. See if jobs exist in `jobs` but not in the async DB (indicates sync→async copy issue).
4. **Check async DB**: Ensure FastAPI uses the same DB you query with `GET /api/jobs` (e.g. SQLite vs Postgres, path/connection string).
5. **Fix the root cause**: Depending on where jobs are lost — e.g. API keys, filter logic, extraction, mapping from `new_jobs` to `ParsedJob`, or `JobService` — implement minimal fixes and add clear logging or error messages.
6. **Ensure API filters are applied** (if desired): Pass `max_yoe`, `excluded_keywords`, etc., from `SearchStart.filters` into the sync pipeline and use them in filters/pre-filters. Document any new parameters.

## Success criteria
- Running the Swagger workflow once (start search → poll status until completed → GET /api/jobs) yields at least one job when Google and extraction return results, and when filters are not excluding everything.
- Logs or status responses make it clear at which stage jobs are dropped (if any).
```

## Prompt End

---

## Extra context for the agent

- **Swagger workflow**: See `SWAGGER_WORKFLOW_STEPS.md` for step-by-step API usage.
- **Sync pipeline entrypoint**: `JobSearchPipeline.run()` in `src/pipeline.py`. It uses `config` and `USER_PROFILE` from `src/config.py`.
- **Async wrapper**: `AsyncSearchPipeline._run_sync_pipeline_with_db_save` in `backend/app/core/pipeline.py`. It invokes `self.pipeline.run(...)` and then maps `summary["new_jobs"]` into `JobService.save_jobs_batch`.
- **Job dict format**: `get_new_jobs_since` returns SQLite rows as dicts (e.g. `url`, `title`, `company`, `salary`, `location`, `remote`, `employment_type`, `yoe_required`, `required_skills`, `nice_to_have_skills`, `responsibilities`, `job_summary`, `source_domain`, `relevance_score`). The async pipeline maps these to `ParsedJob` fields (e.g. `source_url` ← `url`, `salary_range` ← `salary`) before saving to the async DB.

Use this prompt with a **new Cursor agent** (or another AI) that has access to the full repo. It should be able to trace the flow, find where jobs are lost, and fix it.
