# Resume Download Debugging Guide

If you're having issues downloading or viewing resumes, follow these steps:

## Quick Fix Script

If you have resumes in the database but jobs aren't linked to them, run:

```bash
cd backend
python scripts/fix_resume_links.py
```

This will:
- Link resumes to jobs
- Set resume_url for all jobs
- Try to find PDF files and update pdf_path

## Quick Checks

1. **Check if resume was generated successfully:**
   ```bash
   # Check database
   sqlite3 data/jobs.db "SELECT id, job_id, pdf_path FROM resumes WHERE job_id = YOUR_JOB_ID;"
   ```

2. **Check if PDF file exists:**
   ```bash
   ls -la data/resumes/*.pdf
   ```

3. **Check resume URL in database:**
   ```bash
   sqlite3 data/jobs.db "SELECT id, resume_id, resume_url FROM jobs WHERE id = YOUR_JOB_ID;"
   ```

## Common Issues

### Issue 1: `pdf_path` is `None` in database

**Symptoms:** Resume exists but `pdf_path` is NULL

**Causes:**
- PDF generation failed (check backend logs)
- LaTeX compilation failed (pdflatex not installed or error)
- Path not saved correctly

**Fix:**
1. Check backend logs for PDF generation errors
2. Verify pdflatex is installed: `which pdflatex`
3. Regenerate the resume from the web UI

### Issue 2: Resume URL is wrong format

**Symptoms:** Clicking download doesn't work, or shows 404

**Check:**
- Resume URL should be: `/api/resumes/{resume_id}/download`
- NOT an absolute filesystem path like `/Users/.../resume.pdf`

**Fix:**
- If URL is wrong, regenerate the resume (new resumes will have correct URL)
- Or update manually in database:
  ```sql
  UPDATE jobs SET resume_url = '/api/resumes/' || resume_id || '/download' WHERE resume_id IS NOT NULL;
  ```

### Issue 3: PDF file doesn't exist

**Symptoms:** 404 error when downloading

**Check:**
```bash
# Check if file exists
ls -la data/resumes/resume_*.pdf
```

**Fix:**
- Regenerate the resume
- Check backend logs for PDF generation errors

### Issue 4: CORS or Network Error

**Symptoms:** Network error in browser console

**Check:**
- Backend is running on port 8000
- Frontend proxy is configured correctly (check `vite.config.ts`)
- CORS settings allow the frontend origin

## Debug Endpoints

### Check Resume Info
```bash
curl http://localhost:8000/api/resumes/{resume_id}/info
```

This will show:
- Resume ID and job ID
- PDF path stored in database
- Whether PDF file exists
- Download URL

### Test Download Directly
```bash
# Test download endpoint
curl -I http://localhost:8000/api/resumes/{resume_id}/download

# Download PDF
curl http://localhost:8000/api/resumes/{resume_id}/download -o test_resume.pdf
```

## Browser Console Debugging

1. Open browser console (F12)
2. Click "Download Resume" button
3. Check console for:
   - Network errors
   - The actual URL being used
   - Any CORS errors

## Backend Logs

Check backend logs for:
- Resume generation errors
- PDF path resolution issues
- File not found errors

```bash
# If running backend, check logs
# Look for lines like:
# "Resume generation result: ..."
# "PDF path in result doesn't exist: ..."
# "Found PDF at alternative path: ..."
```

## Manual Fix for Existing Resumes

If you have existing resumes with wrong URLs:

1. **Update resume URLs in database:**
   ```sql
   UPDATE jobs 
   SET resume_url = '/api/resumes/' || resume_id || '/download' 
   WHERE resume_id IS NOT NULL 
   AND (resume_url IS NULL OR resume_url NOT LIKE '/api/resumes/%');
   ```

2. **Or regenerate resumes:**
   - Go to job details page
   - Click "Regenerate Resume"
   - This will create a new resume with correct URL

## Still Not Working?

1. Check browser console (F12) for errors
2. Check backend logs for errors
3. Try accessing download URL directly in browser: `http://localhost:8000/api/resumes/{resume_id}/download`
4. Verify PDF file exists: `ls -la data/resumes/`
5. Check resume info endpoint: `http://localhost:8000/api/resumes/{resume_id}/info`
