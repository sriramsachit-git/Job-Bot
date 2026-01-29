import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { Job } from '../../types';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { ChevronLeft, ChevronRight, ArrowUpDown } from 'lucide-react';

interface JobsTableProps {
  jobs: Job[];
  onFilterChange?: (filters: any) => void;
  onPageChange?: (page: number) => void;
  total?: number;
  page?: number;
  pages?: number;
  limit?: number;
}

type SortField = 'title' | 'company' | 'location' | 'yoe_required' | 'relevance_score' | 'created_at';
type SortDirection = 'asc' | 'desc';

export default function JobsTable({
  jobs,
  onFilterChange,
  onPageChange,
  total = 0,
  page = 1,
  pages = 1,
  limit = 50,
}: JobsTableProps) {
  const [filters, setFilters] = useState({
    status: 'all',
    minScore: '',
    maxYoe: '',
    remote: 'all',
    search: '',
  });
  const [sortField, setSortField] = useState<SortField>('relevance_score');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const handleFilterChange = (key: string, value: string) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    if (onFilterChange) {
      onFilterChange({
        status: newFilters.status && newFilters.status !== 'all' ? newFilters.status : undefined,
        min_score: newFilters.minScore ? parseInt(newFilters.minScore) : undefined,
        max_yoe: newFilters.maxYoe ? parseInt(newFilters.maxYoe) : undefined,
        remote: newFilters.remote === 'true' ? true : newFilters.remote === 'false' ? false : undefined,
      });
    }
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedJobs = [...jobs].sort((a, b) => {
    let aVal: any = a[sortField];
    let bVal: any = b[sortField];

    if (sortField === 'created_at') {
      aVal = new Date(aVal).getTime();
      bVal = new Date(bVal).getTime();
    }

    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase();
      bVal = bVal.toLowerCase();
    }

    if (sortDirection === 'asc') {
      return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
    } else {
      return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
    }
  });

  const filteredJobs = sortedJobs.filter((job) => {
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      return (
        job.title.toLowerCase().includes(searchLower) ||
        job.company.toLowerCase().includes(searchLower) ||
        (job.location && job.location.toLowerCase().includes(searchLower))
      );
    }
    return true;
  });

  const SortButton = ({ field, children }: { field: SortField; children: React.ReactNode }) => (
    <button
      onClick={() => handleSort(field)}
      className="flex items-center gap-1 hover:text-primary"
    >
      {children}
      {sortField === field && (
        <ArrowUpDown className={`h-3 w-3 ${sortDirection === 'asc' ? 'rotate-180' : ''}`} />
      )}
    </button>
  );

  if (jobs.length === 0) {
    return <div className="text-center py-8 text-muted-foreground">No jobs found</div>;
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Input
          placeholder="Search jobs..."
          value={filters.search}
          onChange={(e) => handleFilterChange('search', e.target.value)}
        />
        <Select value={filters.status} onValueChange={(v) => handleFilterChange('status', v)}>
          <SelectTrigger>
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="new">New</SelectItem>
            <SelectItem value="reviewed">Reviewed</SelectItem>
            <SelectItem value="applied">Applied</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
          </SelectContent>
        </Select>
        <Input
          type="number"
          placeholder="Min Score"
          value={filters.minScore}
          onChange={(e) => handleFilterChange('minScore', e.target.value)}
        />
        <Input
          type="number"
          placeholder="Max YOE"
          value={filters.maxYoe}
          onChange={(e) => handleFilterChange('maxYoe', e.target.value)}
        />
        <Select value={filters.remote} onValueChange={(v) => handleFilterChange('remote', v)}>
          <SelectTrigger>
            <SelectValue placeholder="Remote" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="true">Remote Only</SelectItem>
            <SelectItem value="false">On-site Only</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border rounded-lg">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="text-left p-3">
                <SortButton field="title">Title</SortButton>
              </th>
              <th className="text-left p-3">
                <SortButton field="company">Company</SortButton>
              </th>
              <th className="text-left p-3">
                <SortButton field="location">Location</SortButton>
              </th>
              <th className="text-left p-3">
                <SortButton field="yoe_required">YOE</SortButton>
              </th>
              <th className="text-left p-3">
                <SortButton field="relevance_score">Score</SortButton>
              </th>
              <th className="text-left p-3">Resume</th>
              <th className="text-left p-3">Applied</th>
              <th className="text-left p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredJobs.map((job) => (
              <tr key={job.id} className="border-b hover:bg-muted/50">
                <td className="p-3">
                  <Link to={`/jobs/${job.id}`} className="text-primary hover:underline">
                    {job.title}
                  </Link>
                </td>
                <td className="p-3">{job.company}</td>
                <td className="p-3">
                  {job.location || 'N/A'}
                  {job.remote && <Badge variant="secondary" className="ml-2">Remote</Badge>}
                </td>
                <td className="p-3">{job.yoe_required}</td>
                <td className="p-3">
                  <Badge>{job.relevance_score}</Badge>
                </td>
                <td className="p-3">
                  {job.resume_url ? (
                    <a
                      href={job.resume_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      📄 PDF
                    </a>
                  ) : (
                    '-'
                  )}
                </td>
                <td className="p-3">{job.applied ? '✅' : '⬜'}</td>
                <td className="p-3">
                  <Link to={`/jobs/${job.id}`}>
                    <Button variant="outline" size="sm">
                      View
                    </Button>
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Showing {((page - 1) * limit) + 1} to {Math.min(page * limit, total)} of {total} jobs
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange && onPageChange(page - 1)}
              disabled={page === 1}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <div className="text-sm">
              Page {page} of {pages}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange && onPageChange(page + 1)}
              disabled={page >= pages}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
