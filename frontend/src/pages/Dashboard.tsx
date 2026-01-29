import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Plus, Briefcase, CheckCircle, Clock, FileText } from 'lucide-react';
import { dashboardApi, jobsApi } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import JobsTable from '../components/Dashboard/JobsTable';

export default function Dashboard() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<any>({});

  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardApi.getStats(),
    retry: 1,
    // Keep showing loading state even if one query fails
    refetchOnWindowFocus: false,
  });

  const { data: jobsData, isLoading: jobsLoading, error: jobsError } = useQuery({
    queryKey: ['jobs', { ...filters, limit: 50, offset: (page - 1) * 50 }],
    queryFn: () => jobsApi.getJobs({ ...filters, limit: 50, offset: (page - 1) * 50 }),
    retry: 1,
    refetchOnWindowFocus: false,
  });

  // Log errors for debugging
  if (statsError) {
    console.error('Dashboard stats error:', statsError);
  }
  if (jobsError) {
    console.error('Jobs API error:', jobsError);
  }

  // Show loading only if BOTH are loading
  if (statsLoading && jobsLoading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  // Show error only if BOTH failed (or show partial data if one succeeds)
  if (statsError && jobsError && !statsLoading && !jobsLoading) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">Error loading data</div>
        <div className="text-sm text-muted-foreground mb-2">
          {statsError?.message || jobsError?.message || 'Unknown error'}
        </div>
        <div className="text-xs text-muted-foreground mb-4">
          Make sure the backend is running on http://localhost:8000
        </div>
        <Button onClick={() => window.location.reload()} className="mt-4">
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Job Search Dashboard</h1>
        <Link to="/search/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Search
          </Button>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
            <Briefcase className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_jobs || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Applied</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats?.applied || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
            <Clock className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats?.pending || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resumes Generated</CardTitle>
            <FileText className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats?.resumes_generated || 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Jobs Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          {jobsError && !jobsLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              <div className="text-red-600 mb-2">Failed to load jobs</div>
              <div className="text-sm">{jobsError.message || 'Unknown error'}</div>
            </div>
          ) : (
            <JobsTable
              jobs={jobsData?.jobs || []}
              onFilterChange={setFilters}
              onPageChange={setPage}
              total={jobsData?.total || 0}
              page={jobsData?.page || 1}
              pages={jobsData?.pages || 1}
              limit={50}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
