/**
 * API client for backend communication.
 */
import axios from 'axios';
import type { Job, Resume, SearchSession, DashboardStats, UserSettings } from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Jobs API
export const jobsApi = {
  getJobs: async (params?: {
    status?: string;
    min_score?: number;
    max_yoe?: number;
    remote?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<{ jobs: Job[]; total: number; page: number; pages: number; limit: number }> => {
    const response = await api.get('/jobs', { params });
    return response.data;
  },

  getJob: async (id: number): Promise<Job> => {
    const response = await api.get(`/jobs/${id}`);
    return response.data;
  },

  updateJob: async (id: number, data: Partial<Job>): Promise<Job> => {
    const response = await api.patch(`/jobs/${id}`, data);
    return response.data;
  },

  deleteJob: async (id: number): Promise<void> => {
    await api.delete(`/jobs/${id}`);
  },
};

// Search API
export const searchApi = {
  startSearch: async (data: {
    job_titles: string[];
    domains: string[];
    filters?: {
      max_yoe?: number;
      remote_only?: boolean;
      locations?: string[];
    };
  }) => {
    const response = await api.post('/search/start', data);
    return response.data;
  },

  getSearchStatus: async (searchId: number): Promise<SearchSession> => {
    const response = await api.get(`/search/${searchId}/status`);
    return response.data;
  },

  getSearchResults: async (searchId: number) => {
    const response = await api.get(`/search/${searchId}/results`);
    return response.data;
  },

  cancelSearch: async (searchId: number) => {
    const response = await api.post(`/search/cancel/${searchId}`);
    return response.data;
  },
};

// Resumes API
export const resumesApi = {
  generateResume: async (jobId: number, selectedProjects?: string[]): Promise<Resume> => {
    const response = await api.post('/resumes', {
      job_id: jobId,
      selected_projects: selectedProjects,
    });
    return response.data;
  },

  bulkGenerateResumes: async (jobIds: number[]) => {
    const response = await api.post('/resumes/bulk-generate', jobIds);
    return response.data;
  },

  getResumes: async (): Promise<Resume[]> => {
    const response = await api.get('/resumes');
    return response.data;
  },

  getResume: async (id: number): Promise<Resume> => {
    const response = await api.get(`/resumes/${id}`);
    return response.data;
  },

  deleteResume: async (id: number): Promise<void> => {
    await api.delete(`/resumes/${id}`);
  },
};

// Dashboard API
export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    const response = await api.get('/dashboard/stats');
    return response.data;
  },

  getRecentJobs: async (limit = 10): Promise<Job[]> => {
    const response = await api.get('/dashboard/recent-jobs', { params: { limit } });
    return response.data;
  },
};

// Settings API
export const settingsApi = {
  getSettings: async (): Promise<UserSettings> => {
    const response = await api.get('/settings');
    return response.data;
  },

  updateSettings: async (data: Partial<UserSettings>): Promise<UserSettings> => {
    const response = await api.put('/settings', data);
    return response.data;
  },
};
