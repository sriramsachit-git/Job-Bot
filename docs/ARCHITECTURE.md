# 🏗️ Job Search Pipeline - Complete Architecture & Flow

## 📍 Entry Points

The system has **2 main entry points**:

### 1. **CLI Entry Point** (`main.py`)
- **Purpose**: Command-line interface for running searches and viewing stats
- **Usage**: `python main.py [options]`
- **Modes**:
  - `--daily` - Run automated daily search
  - `--keywords` - Custom keyword search
  - `--stats` - View database statistics
  - `--skill-stats` - View skill frequency stats
  - `--pre-filter-stats` - View pre-filter statistics
  - `--usage-report` - View API usage costs
  - `--comprehensive` - Matrix search (keywords × sites)
  - `--per-site` - Search each site individually

### 2. **Web API Entry Point** (`web_app.py`)
- **Purpose**: Flask web server for browser-based access
- **Usage**: `python web_app.py [--port 5000]`
- **Access**: `http://localhost:5000` (or network IP)
- **Endpoints**: REST API for viewing jobs, stats, running searches

---

## 🔄 Complete Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MAIN PIPELINE FLOW                              │
└─────────────────────────────────────────────────────────────────────────┘

START: main.py or web_app.py
  │
  ├─▶ JobSearchPipeline.__init__()
  │     │
  │     ├─▶ Config.validate()                    [config.py]
  │     ├─▶ GoogleJobSearch()                     [search.py]
  │     ├─▶ ContentExtractor()                    [extractor.py]
  │     ├─▶ JobParser()                           [llm_parser.py]
  │     ├─▶ JobDatabase()                         [storage.py]
  │     ├─▶ JobFilter(USER_PROFILE)               [filters.py]
  │     └─▶ PreParseFilter(max_yoe)               [pre_filters.py]
  │
  └─▶ pipeline.run() or pipeline.run_daily()
        │
        ├─▶ STEP 1: Google Search
        │     │
        │     └─▶ GoogleJobSearch.search_jobs()
        │           │
        │           ├─▶ Builds Boolean queries: "AI engineer" site:greenhouse.io
        │           ├─▶ Calls Google Custom Search API
        │           ├─▶ Handles pagination (max 100 results)
        │           └─▶ Returns: List[{title, link, snippet, displayLink}]
        │
        ├─▶ STEP 1.5: Early Filtering (Title/Snippet)
        │     │
        │     └─▶ JobFilter.should_skip_early()
        │           │
        │           ├─▶ Checks excluded keywords (senior, staff, etc.)
        │           └─▶ Checks location (USA/Remote only)
        │
        ├─▶ STEP 2: Content Extraction
        │     │
        │     └─▶ ContentExtractor.extract_batch()
        │           │
        │           ├─▶ For each URL:
        │           │     │
        │           │     ├─▶ Try Jina Reader API (for static sites)
        │           │     ├─▶ Try Playwright (for JS-heavy sites)
        │           │     └─▶ Try BeautifulSoup (fallback)
        │           │
        │           └─▶ Returns: List[{url, content, success, method, error}]
        │
        ├─▶ STEP 3: Pre-Parse Filtering (NEW - Cost Saving)
        │     │
        │     └─▶ PreParseFilter.filter_batch()
        │           │
        │           ├─▶ Check YOE > max_yoe (regex)
        │           ├─▶ Check non-US locations (regex)
        │           ├─▶ Check citizenship/clearance (regex)
        │           │
        │           ├─▶ Saves filtered jobs → pre_filtered_jobs table
        │           └─▶ Returns: (passed_contents, filtered_contents)
        │
        ├─▶ STEP 4: LLM Parsing
        │     │
        │     └─▶ JobParser.parse_batch()
        │           │
        │           ├─▶ For each extracted content:
        │           │     │
        │           │     ├─▶ Call OpenAI GPT-4o-mini API
        │           │     ├─▶ Extract structured JSON:
        │           │     │     - job_title, company, location
        │           │     │     - yoe_required, required_skills
        │           │     │     - nice_to_have_skills, salary, etc.
        │           │     │
        │           │     └─▶ Create ParsedJob object
        │           │
        │           └─▶ Returns: (List[ParsedJob], token_usage)
        │
        ├─▶ STEP 4.5: Skill Tracking (NEW)
        │     │
        │     └─▶ JobDatabase.save_skill_frequencies()
        │           │
        │           ├─▶ Normalize job title → category
        │           │     (Data Scientist, ML Engineer, AI Engineer, etc.)
        │           │
        │           ├─▶ For each skill:
        │           │     INSERT/UPDATE skill_frequency table
        │           │     (skill_name, job_title_category, times_seen++)
        │           │
        │           └─▶ Tracks: Which skills appear in which job categories
        │
        ├─▶ STEP 5: Relevance Filtering & Scoring
        │     │
        │     └─▶ JobFilter.filter_jobs()
        │           │
        │           ├─▶ For each ParsedJob:
        │           │     │
        │           │     ├─▶ Calculate relevance score (0-100):
        │           │     │     - YOE match: +30 (or -50 if over max)
        │           │     │     - Required skills: +5 each (max 25)
        │           │     │     - Preferred skills: +3 each (max 15)
        │           │     │     - Location match: +15
        │           │     │     - Remote bonus: +5 to +10
        │           │     │     - Title exclusion: -40
        │           │     │
        │           │     ├─▶ Filter by min_score (default 30)
        │           │     └─▶ Filter by location (USA/Remote only)
        │           │
        │           └─▶ Returns: List[(ParsedJob, score)] sorted by score
        │
        ├─▶ STEP 6: Database Storage
        │     │
        │     └─▶ JobDatabase.save_batch()
        │           │
        │           ├─▶ For each (job, score):
        │           │     │
        │           │     ├─▶ INSERT OR IGNORE INTO jobs
        │           │     │     (deduplication by URL)
        │           │     │
        │           │     └─▶ Track: saved vs skipped (duplicates)
        │           │
        │           └─▶ Returns: (saved_count, skipped_count)
        │
        ├─▶ STEP 7: CSV Export
        │     │
        │     └─▶ JobDatabase.export_csv()
        │           │
        │           └─▶ Exports to: data/jobs_YYYYMMDD_HHMMSS.csv
        │
        └─▶ STEP 8: Resume Generation (Optional)
              │
              └─▶ ResumeGenerator.generate_resumes()
                    │
                    ├─▶ For each new job:
                    │     │
                    │     ├─▶ Match location → approved resume location
                    │     ├─▶ AI ranks projects by relevance
                    │     ├─▶ Select top 3 projects
                    │     │
                    │     ├─▶ select_skills_for_job() (NEW)
                    │     │     │
                    │     │     ├─▶ Match JD skills → extended_skills
                    │     │     ├─▶ Add relevant skills to resume
                    │     │     └─▶ Track skills_added
                    │     │
                    │     ├─▶ Generate LaTeX resume
                    │     ├─▶ Compile to PDF (pdflatex)
                    │     │
                    │     └─▶ Save to:
                    │           - resumes table
                    │           - resume_changes table (NEW)
                    │           - data/resumes/ directory
                    │
                    └─▶ Returns: List[{success, tex_path, pdf_path, skills_added}]

END: Summary dict with statistics
```

---

## 🔗 Component Dependencies

### **Core Components (Connected)**

```
┌─────────────────────────────────────────────────────────────┐
│                    CORE PIPELINE CHAIN                       │
└─────────────────────────────────────────────────────────────┘

main.py / web_app.py
  │
  └─▶ JobSearchPipeline (pipeline.py)
        │
        ├─▶ GoogleJobSearch (search.py)
        │     └─▶ Depends on: config.py (API keys)
        │
        ├─▶ ContentExtractor (extractor.py)
        │     ├─▶ Uses: Jina Reader API
        │     ├─▶ Uses: Playwright (browser automation)
        │     └─▶ Uses: BeautifulSoup (HTML parsing)
        │
        ├─▶ PreParseFilter (pre_filters.py) [NEW]
        │     └─▶ Independent: Pure regex, no external deps
        │
        ├─▶ JobParser (llm_parser.py)
        │     └─▶ Depends on: OpenAI API (GPT-4o-mini)
        │
        ├─▶ JobFilter (filters.py)
        │     └─▶ Depends on: USER_PROFILE (config.py)
        │
        └─▶ JobDatabase (storage.py)
              └─▶ SQLite database (persistent storage)
```

### **Independent Components**

These can be used standalone or in different contexts:

1. **`config.py`**
   - **Independent**: No dependencies on other modules
   - **Used by**: All components (singleton pattern)
   - **Purpose**: Centralized configuration management

2. **`storage.py` (JobDatabase)**
   - **Independent**: Can be used without pipeline
   - **Dependencies**: SQLite, json
   - **Can be used for**: Direct database queries, stats, exports

3. **`filters.py` (JobFilter)**
   - **Independent**: Can filter any list of ParsedJob objects
   - **Dependencies**: USER_PROFILE from config
   - **Can be used for**: Standalone job scoring

4. **`pre_filters.py` (PreParseFilter)** [NEW]
   - **Independent**: Pure regex filtering, no external APIs
   - **Dependencies**: None (except re, logging)
   - **Can be used for**: Pre-filtering any text content

5. **`resume_generator.py` (ResumeGenerator)**
   - **Semi-independent**: Can generate resumes from job data
   - **Dependencies**: OpenAI API, LaTeX compiler, YAML config
   - **Can be used for**: Standalone resume generation

---

## 📊 Data Flow

### **Data Structures**

```
┌─────────────────────────────────────────────────────────────┐
│                      DATA TRANSFORMATIONS                    │
└─────────────────────────────────────────────────────────────┘

1. Search Results (Dict)
   {
     "title": "AI Engineer",
     "link": "https://...",
     "snippet": "...",
     "displayLink": "greenhouse.io"
   }
   │
   └─▶ [Early Filter] → Filtered by title/snippet
   │
   └─▶ [Extraction] → Extracted Content (Dict)
         {
           "url": "https://...",
           "content": "Full job posting text...",
           "success": True,
           "method": "jina" | "playwright" | "beautifulsoup"
         }
         │
         └─▶ [Pre-Filter] → Filtered by regex (YOE, location, citizenship)
         │
         └─▶ [LLM Parse] → ParsedJob (Pydantic Model)
               {
                 job_title: str
                 company: str
                 location: str
                 yoe_required: int
                 required_skills: List[str]
                 nice_to_have_skills: List[str]
                 ...
               }
               │
               └─▶ [Skill Tracking] → skill_frequency table
               │
               └─▶ [Scoring] → (ParsedJob, score: int)
                     │
                     └─▶ [Storage] → jobs table (SQLite)
                           │
                           └─▶ [Resume Gen] → LaTeX + PDF
                                 │
                                 └─▶ resumes table + resume_changes table
```

---

## 🗄️ Database Schema

### **Tables & Relationships**

```
┌─────────────────────────────────────────────────────────────┐
│                      DATABASE STRUCTURE                      │
└─────────────────────────────────────────────────────────────┘

jobs (Main table)
  ├─ id (PK)
  ├─ url (UNIQUE)
  ├─ title, company, location
  ├─ yoe_required, required_skills, nice_to_have_skills
  ├─ relevance_score
  └─ created_at, updated_at

resumes
  ├─ id (PK)
  ├─ job_id (FK → jobs.id)
  ├─ job_title, company, job_url
  ├─ resume_location, selected_projects
  ├─ tex_path, pdf_path
  └─ created_at

resume_changes [NEW]
  ├─ id (PK)
  ├─ resume_id (FK → resumes.id)
  ├─ job_id (FK → jobs.id)
  ├─ location_used
  ├─ skills_added (JSON)
  ├─ projects_selected (JSON)
  └─ created_at

pre_filtered_jobs [NEW]
  ├─ id (PK)
  ├─ url (UNIQUE)
  ├─ title, snippet, source_domain
  ├─ filter_reason, filter_details
  ├─ raw_content_preview
  └─ created_at

skill_frequency [NEW]
  ├─ id (PK)
  ├─ skill_name
  ├─ job_title_category
  ├─ times_seen
  ├─ first_seen, last_seen
  └─ UNIQUE(skill_name, job_title_category)

unextracted_jobs
  ├─ id (PK)
  ├─ url (UNIQUE)
  ├─ title, snippet, source_domain
  ├─ extraction_methods_attempted (JSON)
  ├─ error_message
  ├─ retry_count
  └─ created_at, updated_at
```

---

## 🔌 External Dependencies

### **API Services**

1. **Google Custom Search API**
   - Used by: `search.py`
   - Cost: Free tier (100 queries/day), then $5/1,000 queries
   - Rate limit: 100 queries/day (free tier)

2. **Jina Reader API**
   - Used by: `extractor.py`
   - Purpose: Extract content from static websites
   - Cost: Free tier available

3. **OpenAI API (GPT-4o-mini)**
   - Used by: `llm_parser.py`, `resume_generator.py`
   - Cost: ~$0.50 per 1,000 job postings parsed
   - Rate limit: Based on tier

4. **Playwright**
   - Used by: `extractor.py`
   - Purpose: Browser automation for JS-heavy sites
   - Local dependency (no API calls)

---

## 🎯 Key Design Patterns

### **1. Pipeline Pattern**
- Sequential processing through stages
- Each stage transforms data for the next
- Failures at any stage don't crash the pipeline

### **2. Strategy Pattern**
- Multiple extraction methods (Jina, Playwright, BeautifulSoup)
- Fallback chain: Try method 1, if fails try method 2, etc.

### **3. Repository Pattern**
- `JobDatabase` abstracts database operations
- All database access goes through storage layer

### **4. Configuration Singleton**
- `config.py` provides centralized configuration
- Single source of truth for API keys, paths, settings

### **5. Dependency Injection**
- Components initialized in `JobSearchPipeline.__init__()`
- Can be swapped/mocked for testing

---

## 🔄 Alternative Flows

### **Web App Flow**

```
User Browser
  │
  └─▶ web_app.py (Flask)
        │
        ├─▶ GET /api/jobs → JobDatabase.get_jobs()
        ├─▶ GET /api/stats → JobDatabase.get_stats()
        ├─▶ GET /api/skills → JobDatabase.get_top_skills_by_category()
        ├─▶ GET /api/pre-filtered → JobDatabase.get_pre_filtered_jobs()
        └─▶ POST /api/search/run → JobSearchPipeline.run()
```

### **Resume Generation Flow**

```
generate_resumes.py (standalone script)
  │
  └─▶ ResumeGenerator.generate_recommendations()
        │
        ├─▶ Load jobs from database
        ├─▶ Rank projects using AI
        ├─▶ Select skills dynamically
        └─▶ Generate LaTeX → PDF
```

### **Stats/Reporting Flow**

```
main.py --stats
  │
  └─▶ JobDatabase.get_stats()
        │
        ├─▶ Count jobs, applied, saved
        ├─▶ Top companies, domains
        └─▶ Average YOE

main.py --skill-stats
  │
  └─▶ JobDatabase.get_skill_stats_summary()
        │
        ├─▶ Unique skills count
        ├─▶ Skills by category
        └─▶ Top skills by frequency
```

---

## 🚦 Error Handling & Recovery

### **Retry Logic**

1. **Google Search API** (`search.py`)
   - Retries: 3 attempts with exponential backoff
   - Handles: HttpError, ConnectionError

2. **Content Extraction** (`extractor.py`)
   - Fallback chain: Jina → Playwright → BeautifulSoup
   - Failed extractions saved to `unextracted_jobs` table

3. **LLM Parsing** (`llm_parser.py`)
   - Retries: 3 attempts with exponential backoff
   - Failed parses logged but don't stop pipeline

### **Failure Points**

- **Search fails**: Pipeline stops (no URLs to process)
- **Extraction fails**: Job saved to `unextracted_jobs` for retry
- **Parsing fails**: Job skipped, logged
- **Database fails**: Transaction rolled back, error logged

---

## 📈 Performance Considerations

### **Bottlenecks**

1. **LLM Parsing** (slowest)
   - Cost: ~$0.50 per 1,000 jobs
   - Time: ~2-5 seconds per job
   - **Solution**: Pre-filtering reduces LLM calls by 20-40%

2. **Content Extraction**
   - Playwright: ~3-5 seconds per page
   - Jina: ~1-2 seconds per page
   - **Solution**: Batch processing, parallel extraction

3. **Google Search API**
   - Rate limit: 100 queries/day (free tier)
   - **Solution**: Comprehensive search uses pagination efficiently

### **Optimizations**

- Pre-filtering saves 20-40% of LLM costs
- Early filtering (title/snippet) saves extraction costs
- Batch database operations (save_batch)
- Caching: Deduplication by URL prevents reprocessing

---

## 🔐 Security & Privacy

- **API Keys**: Stored in `.env` file (not committed)
- **Database**: Local SQLite (no network exposure)
- **Web App**: Runs on localhost by default (can bind to network)
- **Data**: Job postings are public data, no PII stored

---

## 📝 Summary

**Entry Points**: `main.py` (CLI), `web_app.py` (Web)

**Main Flow**: Search → Extract → Pre-Filter → Parse → Track Skills → Score → Store → Generate Resumes

**Connected Components**: Pipeline orchestrates all components sequentially

**Independent Components**: Config, Storage, Filters, Pre-Filters can be used standalone

**Data Flow**: Dict → Dict → ParsedJob → (ParsedJob, score) → Database → LaTeX/PDF

**Key Innovation**: Pre-filtering reduces LLM costs by filtering disqualifying jobs before expensive API calls
