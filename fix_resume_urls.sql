-- Fix resume URLs for existing resumes
-- Run this with: sqlite3 data/jobs.db < fix_resume_urls.sql

-- Update jobs to link to resumes and set resume_url
UPDATE jobs 
SET 
    resume_id = (
        SELECT id FROM resumes 
        WHERE resumes.job_id = jobs.id 
        ORDER BY resumes.created_at DESC 
        LIMIT 1
    ),
    resume_url = '/api/resumes/' || (
        SELECT id FROM resumes 
        WHERE resumes.job_id = jobs.id 
        ORDER BY resumes.created_at DESC 
        LIMIT 1
    ) || '/download'
WHERE EXISTS (
    SELECT 1 FROM resumes 
    WHERE resumes.job_id = jobs.id
)
AND resume_id IS NULL;

-- Show results
SELECT 
    j.id as job_id,
    j.title,
    j.company,
    j.resume_id,
    j.resume_url,
    r.pdf_path
FROM jobs j
LEFT JOIN resumes r ON j.resume_id = r.id
WHERE j.resume_id IS NOT NULL
LIMIT 10;
