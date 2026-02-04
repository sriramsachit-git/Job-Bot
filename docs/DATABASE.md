# Database organisation and data

The pipeline uses a **single SQLite database** at `data/jobs.db` (relative to project root). It is used by both the **CLI pipeline** (`src/storage.py`) and the **backend API** (FastAPI + SQLAlchemy). The file is gitignored.

## How to analyse the database

From the project root:

```bash
python scripts/analyze_db.py
# Or with a custom path:
python scripts/analyze_db.py /path/to/jobs.db
```

The script prints every table, its columns, row counts, and up to 3 sample rows per table.

---

## Tables and purpose

| Table | Purpose |
|-------|--------|
| **jobs** | Parsed job postings (URL, title, company, location, YOE, skills, summary, relevance_score, status, applied, resume link, etc.). Deduplicated by `url`. |
| **resumes** | Generated resumes: link to `job_id`, job_title, company, paths (tex/pdf/cloud), selected projects. |
| **search_sessions** | Web-app searches: job_titles, domains, filters, status, progress, counts (urls_found, jobs_extracted, jobs_parsed, jobs_saved), started_at / completed_at. |
| **unextracted_jobs** | URLs that failed extraction (title/snippet from search, source_domain, error_message, retry_count). Shown per search by filtering `created_at >= session.started_at`. |
| **pre_filtered_jobs** | Jobs excluded before LLM parsing (e.g. senior/lead, non-US). Same time-window link to searches via `created_at`. |
| **skill_frequency** | Aggregated skill counts by job title category (e.g. ML Engineer, Data Scientist) for analytics. |
| **resume_changes** | Audit of resume customisation: resume_id, job_id, location_used, skills_added, projects_selected. |
| **user_settings** | Single-row app settings (default_job_titles, default_domains, max_yoe, etc.). |

---

## How “per search” data is linked

- **Jobs** for a search are not stored with a `search_session_id`. The API infers them by **creation time**: jobs with `created_at >= search_session.started_at` are considered part of that run.
- **Pre-filtered** and **unextracted** lists for a search use the same idea: `PreFilteredJob.created_at >= session.started_at` and `UnextractedJob.created_at >= session.started_at`.

So all three (jobs, pre_filtered_jobs, unextracted_jobs) are **time-windowed** by the search’s `started_at` rather than a foreign key.

---

## Who writes what

- **CLI pipeline** (`src/storage.py`): creates/updates `jobs`, `resumes`, `unextracted_jobs`, `pre_filtered_jobs`, `skill_frequency`, `resume_changes`. It does not create `search_sessions`.
- **Backend** (FastAPI): creates `search_sessions` and `user_settings`; when a search runs via the API it uses the same pipeline and thus writes to `jobs`, `unextracted_jobs`, `pre_filtered_jobs` (and can write resumes/skill_frequency/resume_changes depending on flow). The backend uses SQLAlchemy models; the CLI uses raw SQL. Schema may have evolved (e.g. extra columns) so both can write to the same file.

---

## Current data (from last analysis)

Running `scripts/analyze_db.py` gives exact counts. Typical contents:

- **jobs**: Parsed postings (e.g. 67 rows); samples show title, company, location, yoe_required, relevance_score, status, resume_id.
- **resumes**: One row per generated resume (e.g. 50), linked to jobs.
- **search_sessions**: Rows when searches are started from the web app (can be 0 if only CLI has been used).
- **unextracted_jobs**: URLs that failed extraction (e.g. 16).
- **pre_filtered_jobs**: Jobs excluded by pre-filters (e.g. 10), often with `filter_reason` like `non_us_location`.
- **skill_frequency**: Skill × category counts (e.g. 151 rows).
- **resume_changes**: History of resume customisations (e.g. 19).
- **user_settings**: 0 or 1 row.

For up-to-date row counts and sample rows, run:

```bash
python scripts/analyze_db.py
```
