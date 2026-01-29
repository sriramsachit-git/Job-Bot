# Resume Generation Setup

Resume generation requires two configuration files. If you see an error like:

```
FileNotFoundError: Resume config not found: data/resume_config.yaml
```

Follow these steps to set up resume generation.

## Quick Setup

### 1. Create `data/resume_config.yaml`

Create this file in the **project root** (`job_search_pipeline/data/resume_config.yaml`):

```yaml
contact:
  name: "Your Name"
  email: "your.email@example.com"
  phone: "xxx-xxx-xxxx"
  linkedin: "linkedin.com/in/yourprofile"
  github: "github.com/yourusername"

default_location: "San Diego, CA"
approved_locations:
  - "San Diego, CA"
  - "Remote"

education:
  degree: "MS in Data Science"
  school: "University Name"
  gpa: "3.8"
  graduation: "2023"
  coursework: ["Machine Learning", "Deep Learning", "Statistics"]

experience:
  - title: "ML Engineer"
    company: "Company Name"
    dates: "2022 - Present"
    bullets:
      - "Built ML pipelines..."
      - "Deployed models..."

skills:
  languages: ["Python", "SQL", "R"]
  ml_frameworks: ["PyTorch", "TensorFlow", "Scikit-learn"]
  cloud_devops: ["AWS", "Docker", "Kubernetes"]
  ai_tools: ["LangChain", "HuggingFace", "OpenAI"]
  domains: ["NLP", "Computer Vision", "Recommendation Systems"]
```

### 2. Create `data/projects.json`

Create this file in the **project root** (`job_search_pipeline/data/projects.json`):

```json
{
  "projects": [
    {
      "id": "project1",
      "name": "RAG System",
      "one_liner": "Built a retrieval-augmented generation system",
      "skills": ["Python", "LangChain", "OpenAI", "Vector DB"],
      "metrics": "Improved accuracy by 30%",
      "bullets": [
        "Implemented semantic search with embeddings",
        "Built prompt engineering pipeline"
      ]
    },
    {
      "id": "project2",
      "name": "ML Model Deployment",
      "one_liner": "Deployed ML models to production",
      "skills": ["Python", "Docker", "AWS", "Kubernetes"],
      "metrics": "Reduced latency by 50%",
      "bullets": [
        "Containerized ML models with Docker",
        "Set up CI/CD pipeline"
      ]
    }
  ]
}
```

### 3. Verify Files Exist

```bash
# From project root
ls -la data/resume_config.yaml
ls -la data/projects.json
```

Both files should exist. If not, create them using the templates above.

## File Locations

**Important:** These files must be in the **project root** `data/` directory:

```
job_search_pipeline/
├── data/
│   ├── resume_config.yaml  ← HERE
│   ├── projects.json        ← HERE
│   └── resumes/             ← Single directory for all generated PDFs
├── backend/
└── frontend/
```

**NOT** in `backend/data/` - they need to be at the repo root level.

### Resume PDF directory (Option C)

All generated resume PDFs use **one directory**: `data/resumes/` at the project root. The backend resolves this as an absolute path, so it works regardless of where you run the server.

To override the location, set in `.env`:

```bash
RESUMES_DIR=/absolute/path/to/job_search_pipeline/data/resumes
```

The database stores only **filenames** (e.g. `resume_Company_Title_20260128_200315.pdf`); downloads are resolved against this single base directory.

## Testing

After creating the files, try generating a resume from the web UI:

1. Go to Dashboard
2. Click on a job
3. Click "Generate Resume"

If you still get errors, check:
- Files are in the correct location (`data/` at repo root)
- YAML syntax is correct (use a YAML validator)
- JSON syntax is correct (use a JSON validator)

## Troubleshooting

### Error: "Resume config not found"
- Check file path: Should be `job_search_pipeline/data/resume_config.yaml`
- Check file exists: `ls data/resume_config.yaml`
- Check you're running backend from correct directory

### Error: "Projects file not found"
- Check file path: Should be `job_search_pipeline/data/projects.json`
- Check file exists: `ls data/projects.json`

### Error: "Failed to generate resume"
- Check LaTeX is installed: `python scripts/check_pdf_setup.py`
- Check OpenAI API key is set in `.env`
- Check backend logs for detailed error messages
