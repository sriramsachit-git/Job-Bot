# Swagger UI Workflow Steps

## Complete Workflow: Search Jobs → Generate Resume

### Prerequisites
1. Make sure the backend server is running (usually at `http://localhost:8000`)
2. Open Swagger UI at `http://localhost:8000/docs`

---

## Step 1: Start a Job Search

**Endpoint:** `POST /api/search/start`

1. Click on the **`POST /api/search/start`** endpoint
2. Click **"Try it out"**
3. Fill in the request body:

```json
{
  "job_titles": ["Software Engineer", "Data Scientist", "ML Engineer"],
  "domains": ["linkedin.com", "indeed.com"],
  "filters": {
    "max_yoe": 5,
    "remote_only": false,
    "locations": ["San Francisco", "Remote"],
    "excluded_keywords": ["intern", "internship"]
  }
}
```

**Note:** You can customize:
- `job_titles`: List of job titles to search for
- `domains`: List of job board domains to search
- `filters`: Optional filters (can be omitted or set to `null`)

4. Click **"Execute"**
5. **Copy the `search_id`** from the response (you'll need it for the next steps)

**Example Response:**
```json
{
  "search_id": 1,
  "status": "started"
}
```

---

## Step 2: Check Search Status

**Endpoint:** `GET /api/search/{search_id}/status`

1. Click on the **`GET /api/search/{search_id}/status`** endpoint
2. Click **"Try it out"**
3. Enter the `search_id` from Step 1 in the `search_id` parameter field
4. Click **"Execute"**
5. Check the response:
   - `status`: Should be "running" or "completed"
   - `progress`: 0-100 percentage
   - `jobs_saved`: Number of jobs found and saved

**Repeat this step** until `status` is `"completed"` or `"failed"`

**Example Response:**
```json
{
  "search_id": 1,
  "status": "completed",
  "progress": 100,
  "current_step": "completed",
  "urls_found": 50,
  "jobs_extracted": 45,
  "jobs_parsed": 45,
  "jobs_saved": 45,
  "error_message": null,
  "started_at": "2026-01-24T00:00:00",
  "completed_at": "2026-01-24T00:05:00"
}
```

---

## Step 3: Get Search Results (Optional)

**Endpoint:** `GET /api/search/{search_id}/results`

1. Click on the **`GET /api/search/{search_id}/results`** endpoint
2. Click **"Try it out"**
3. Enter the `search_id` from Step 1
4. Click **"Execute"**
5. Review the jobs found in the response

---

## Step 4: List All Jobs

**Endpoint:** `GET /api/jobs`

1. Click on the **`GET /api/jobs`** endpoint
2. Click **"Try it out"**
3. Optionally set query parameters:
   - `status`: Filter by status (e.g., "new", "reviewed", "applied")
   - `min_score`: Minimum relevance score
   - `max_yoe`: Maximum years of experience required
   - `remote`: Filter by remote jobs (true/false)
   - `limit`: Number of results (default: 50)
   - `offset`: Pagination offset (default: 0)
4. Click **"Execute"**
5. **Copy a `job_id`** from the response that you want to generate a resume for

**Example Response:**
```json
{
  "jobs": [
    {
      "id": 1,
      "title": "Software Engineer",
      "company": "Tech Corp",
      "location": "San Francisco",
      "relevance_score": 85,
      ...
    }
  ],
  "total": 45,
  "page": 1,
  "pages": 1,
  "limit": 50
}
```

---

## Step 5: Generate Resume for a Job

**Endpoint:** `POST /api/resumes`

1. Click on the **`POST /api/resumes`** endpoint
2. Click **"Try it out"**
3. Fill in the request body:

```json
{
  "job_id": 1,
  "selected_projects": null
}
```

**Note:**
- `job_id`: The ID of the job from Step 4
- `selected_projects`: Leave as `null` to auto-select top 3 projects, or provide a list of project names

4. Click **"Execute"**
5. Wait for the response (this may take 30-60 seconds as it generates the resume)
6. The response will include:
   - `id`: Resume ID
   - `pdf_path`: Path to the generated PDF
   - `cloud_url`: Cloud storage URL (if configured)

**Example Response:**
```json
{
  "id": 1,
  "job_id": 1,
  "job_title": "Software Engineer",
  "company": "Tech Corp",
  "resume_location": "San Francisco, CA",
  "selected_projects": ["Project A", "Project B", "Project C"],
  "tex_path": "/path/to/resume.tex",
  "pdf_path": "/path/to/resume.pdf",
  "cloud_url": null,
  "created_at": "2026-01-24T00:10:00"
}
```

---

## Step 6: Download Resume (Optional)

**Endpoint:** `GET /api/resumes/download/{filename}`

1. Extract the filename from `pdf_path` in Step 5 response (e.g., if path is `/data/resumes/resume_123.pdf`, filename is `resume_123.pdf`)
2. Click on the **`GET /api/resumes/download/{filename}`** endpoint
3. Click **"Try it out"**
4. Enter the filename in the `filename` parameter
5. Click **"Execute"**
6. The PDF will be downloaded

---

## Alternative: Bulk Generate Resumes

**Endpoint:** `POST /api/resumes/bulk-generate`

1. Click on the **`POST /api/resumes/bulk-generate`** endpoint
2. Click **"Try it out"**
3. Fill in the request body with an array of job IDs:

```json
[1, 2, 3, 4, 5]
```

4. Click **"Execute"**
5. This will generate resumes for all specified jobs

---

## Quick Reference: Complete Workflow

```
1. POST /api/search/start          → Get search_id
2. GET /api/search/{id}/status     → Poll until completed
3. GET /api/jobs                   → Get job_id
4. POST /api/resumes               → Generate resume
5. GET /api/resumes/download/{file} → Download PDF (optional)
```

---

## Troubleshooting

- **Search stuck on "running"**: Check the `error_message` in the status response
- **No jobs found**: Try different job titles or domains
- **Resume generation fails**: Check that the job exists and has required fields
- **404 errors**: Make sure you're using the correct IDs from previous steps
