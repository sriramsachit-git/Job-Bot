import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi, resumesApi } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';

export default function JobDetails() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const jobId = parseInt(id || '0', 10);

  const { data: job, isLoading } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.getJob(jobId),
    enabled: !!jobId,
  });

  const generateResumeMutation = useMutation({
    mutationFn: () => resumesApi.generateResume(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job', jobId] });
    },
  });

  if (isLoading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  if (!job) {
    return <div className="text-center py-12">Job not found</div>;
  }

  return (
    <div className="max-w-4xl mx-auto">
      <Link to="/" className="text-primary hover:underline mb-4 inline-block">
        ← Back to Dashboard
      </Link>

      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-2xl">{job.title}</CardTitle>
              <p className="text-muted-foreground mt-2">{job.company}</p>
            </div>
            <Badge>{job.relevance_score}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <strong>Location:</strong> {job.location || 'N/A'}
            {job.remote && <Badge variant="secondary" className="ml-2">Remote</Badge>}
          </div>
          <div>
            <strong>Years of Experience Required:</strong> {job.yoe_required}
          </div>
          <div>
            <strong>Source:</strong> {job.source_domain || 'N/A'}
          </div>

          {job.required_skills && job.required_skills.length > 0 && (
            <div>
              <strong>Required Skills:</strong>
              <div className="flex flex-wrap gap-2 mt-2">
                {job.required_skills.map((skill) => (
                  <Badge key={skill} variant="secondary">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {job.job_summary && (
            <div>
              <strong>Summary:</strong>
              <p className="mt-2">{job.job_summary}</p>
            </div>
          )}

          {job.responsibilities && job.responsibilities.length > 0 && (
            <div>
              <strong>Responsibilities:</strong>
              <ul className="list-disc list-inside mt-2">
                {job.responsibilities.map((resp, idx) => (
                  <li key={idx}>{resp}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex gap-4 pt-4">
            <Button
              onClick={() => generateResumeMutation.mutate()}
              disabled={generateResumeMutation.isPending}
            >
              {generateResumeMutation.isPending
                ? 'Generating...'
                : job.resume_url
                ? 'Regenerate Resume'
                : 'Generate Resume'}
            </Button>
            {job.resume_url && (
              <a href={job.resume_url} target="_blank" rel="noopener noreferrer">
                <Button variant="outline">Download Resume</Button>
              </a>
            )}
            <a href={job.url} target="_blank" rel="noopener noreferrer">
              <Button variant="outline">View Original Posting</Button>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
