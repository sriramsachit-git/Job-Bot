import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { searchApi, resumesApi } from '../../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Checkbox } from '../ui/checkbox';
import { useState } from 'react';
import { MapPin, Calendar, FileText } from 'lucide-react';

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
                      {job.yoe_required} YOE
                    </div>
                  </div>

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
    </div>
  );
}
