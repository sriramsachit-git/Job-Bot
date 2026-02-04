import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { searchApi, resumesApi } from '../../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Checkbox } from '../ui/checkbox';
import { useState } from 'react';
import { MapPin, Calendar, FileText, Link as LinkIcon } from 'lucide-react';

interface SearchResultsProps {
  searchId: number;
}

export default function SearchResults({ searchId }: SearchResultsProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedJobs, setSelectedJobs] = useState<number[]>([]);

  const { data: results, isLoading } = useQuery({
    queryKey: ['search-results', searchId],
    queryFn: () => searchApi.getSearchResults(searchId),
  });

  const { data: preFiltered } = useQuery({
    queryKey: ['search-prefiltered', searchId],
    queryFn: () => searchApi.getPreFiltered(searchId),
    enabled: !!searchId,
  });

  const { data: unextracted } = useQuery({
    queryKey: ['search-unextracted', searchId],
    queryFn: () => searchApi.getUnextracted(searchId),
    enabled: !!searchId,
  });

  const bulkGenerateMutation = useMutation({
    mutationFn: (jobIds: number[]) => resumesApi.bulkGenerateResumes(jobIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });

  const toggleJobSelection = (jobId: number) => {
    setSelectedJobs((prev) =>
      prev.includes(jobId)
        ? prev.filter((id) => id !== jobId)
        : [...prev, jobId]
    );
  };

  const selectAll = () => {
    if (results?.jobs) {
      setSelectedJobs(results.jobs.map((j: any) => j.id));
    }
  };

  const deselectAll = () => {
    setSelectedJobs([]);
  };

  const handleBulkGenerate = () => {
    if (selectedJobs.length > 0) {
      bulkGenerateMutation.mutate(selectedJobs);
    }
  };

  if (isLoading) {
    return <div className="text-center py-12">Loading results...</div>;
  }

  if (!results || results.jobs.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No jobs found in this search.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold">
            Found {results.total} Eligible Jobs
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Select jobs to generate resumes
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={selectAll} size="sm">
            Select All
          </Button>
          <Button variant="outline" onClick={deselectAll} size="sm">
            Deselect All
          </Button>
          {selectedJobs.length > 0 && (
            <Button
              onClick={handleBulkGenerate}
              disabled={bulkGenerateMutation.isPending}
            >
              Generate Selected ({selectedJobs.length})
            </Button>
          )}
        </div>
      </div>

      <div className="space-y-4">
        {results.jobs.map((job: any) => (
          <Card key={job.id}>
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <Checkbox
                  checked={selectedJobs.includes(job.id)}
                  onCheckedChange={() => toggleJobSelection(job.id)}
                  className="mt-1"
                />
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="text-lg font-semibold">{job.title}</h3>
                      <p className="text-muted-foreground">{job.company}</p>
                    </div>
                    <Badge>{job.relevance_score}</Badge>
                  </div>

                  <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mb-3">
                    {job.location && (
                      <div className="flex items-center gap-1">
                        <MapPin className="h-4 w-4" />
                        {job.location}
                        {job.remote && (
                          <Badge variant="secondary" className="ml-2">
                            Remote OK
                          </Badge>
                        )}
                      </div>
                    )}
                    <div className="flex items-center gap-1">
                      <Calendar className="h-4 w-4" />
                      {job.date_posted || job.created_at
                        ? new Date(job.date_posted || job.created_at).toLocaleDateString()
                        : 'Date N/A'}
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="font-medium text-foreground/70">YOE:</span> {job.yoe_required}
                    </div>
                  </div>

                  {job.url && (
                    <div className="flex items-center gap-2 text-sm mb-3">
                      <LinkIcon className="h-4 w-4 text-muted-foreground" />
                      <a
                        href={job.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline break-all"
                      >
                        {job.url}
                      </a>
                    </div>
                  )}

                  {job.required_skills && job.required_skills.length > 0 && (
                    <div className="mb-3">
                      <p className="text-sm font-medium mb-2">Key Skills:</p>
                      <div className="flex flex-wrap gap-2">
                        {job.required_skills.slice(0, 5).map((skill: string) => (
                          <Badge key={skill} variant="secondary">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex gap-2 mt-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/jobs/${job.id}`)}
                    >
                      View Details
                    </Button>
                    {job.resume_url ? (
                      <a href={job.resume_url} target="_blank" rel="noopener noreferrer">
                        <Button variant="outline" size="sm">
                          <FileText className="h-4 w-4 mr-2" />
                          View Resume
                        </Button>
                      </a>
                    ) : (
                      <Button
                        size="sm"
                        onClick={() => {
                          resumesApi.generateResume(job.id).then(() => {
                            queryClient.invalidateQueries({ queryKey: ['search-results', searchId] });
                          });
                        }}
                      >
                        Generate Resume
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Post-run diagnostics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Pre-filtered (excluded before LLM) ({Array.isArray(preFiltered) ? preFiltered.length : 0})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!preFiltered || preFiltered.length === 0 ? (
              <p className="text-sm text-muted-foreground">None</p>
            ) : (
              <div className="space-y-3">
                {preFiltered.slice(0, 50).map((item: any) => (
                  <div key={item.url} className="text-sm">
                    <div className="flex items-center justify-between gap-2">
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline break-all"
                      >
                        {item.title || item.url}
                      </a>
                      {item.filter_reason && <Badge variant="secondary">{item.filter_reason}</Badge>}
                    </div>
                    {item.filter_details && (
                      <div className="text-xs text-muted-foreground mt-1">{item.filter_details}</div>
                    )}
                  </div>
                ))}
                {preFiltered.length > 50 && (
                  <p className="text-xs text-muted-foreground">Showing first 50.</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Unextracted (failed to fetch content) ({Array.isArray(unextracted) ? unextracted.length : 0})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!unextracted || unextracted.length === 0 ? (
              <p className="text-sm text-muted-foreground">None</p>
            ) : (
              <div className="space-y-3">
                {unextracted.slice(0, 50).map((item: any) => (
                  <div key={item.url} className="text-sm">
                    <div className="flex items-center justify-between gap-2">
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline break-all"
                      >
                        {item.title || item.url}
                      </a>
                      {typeof item.retry_count === 'number' && (
                        <Badge variant="secondary">retries: {item.retry_count}</Badge>
                      )}
                    </div>
                    {item.error_message && (
                      <div className="text-xs text-muted-foreground mt-1">{item.error_message}</div>
                    )}
                  </div>
                ))}
                {unextracted.length > 50 && (
                  <p className="text-xs text-muted-foreground">Showing first 50.</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
