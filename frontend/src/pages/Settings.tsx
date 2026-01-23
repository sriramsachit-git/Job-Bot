import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsApi } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
import { useToast } from '../hooks/use-toast';

export default function Settings() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    default_job_titles: [] as string[],
    default_domains: [] as string[],
    max_yoe: 5,
    preferred_locations: [] as string[],
    remote_only: false,
    excluded_keywords: [] as string[],
  });

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: () => settingsApi.getSettings(),
    onSuccess: (data) => {
      setFormData({
        default_job_titles: data.default_job_titles || [],
        default_domains: data.default_domains || [],
        max_yoe: data.max_yoe || 5,
        preferred_locations: data.preferred_locations || [],
        remote_only: data.remote_only || false,
        excluded_keywords: data.excluded_keywords || [],
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: settingsApi.updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      toast({
        title: 'Settings saved',
        description: 'Your preferences have been updated successfully.',
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to save settings',
        variant: 'destructive',
      });
    },
  });

  const handleSave = () => {
    updateMutation.mutate(formData);
  };

  const addJobTitle = () => {
    const input = document.getElementById('job-title-input') as HTMLInputElement;
    if (input?.value.trim()) {
      setFormData({
        ...formData,
        default_job_titles: [...formData.default_job_titles, input.value.trim()],
      });
      input.value = '';
    }
  };

  const removeJobTitle = (title: string) => {
    setFormData({
      ...formData,
      default_job_titles: formData.default_job_titles.filter((t) => t !== title),
    });
  };

  const addDomain = () => {
    const input = document.getElementById('domain-input') as HTMLInputElement;
    if (input?.value.trim()) {
      setFormData({
        ...formData,
        default_domains: [...formData.default_domains, input.value.trim()],
      });
      input.value = '';
    }
  };

  const removeDomain = (domain: string) => {
    setFormData({
      ...formData,
      default_domains: formData.default_domains.filter((d) => d !== domain),
    });
  };

  const addLocation = () => {
    const input = document.getElementById('location-input') as HTMLInputElement;
    if (input?.value.trim()) {
      setFormData({
        ...formData,
        preferred_locations: [...formData.preferred_locations, input.value.trim()],
      });
      input.value = '';
    }
  };

  const removeLocation = (location: string) => {
    setFormData({
      ...formData,
      preferred_locations: formData.preferred_locations.filter((l) => l !== location),
    });
  };

  const addExcludedKeyword = () => {
    const input = document.getElementById('keyword-input') as HTMLInputElement;
    if (input?.value.trim()) {
      setFormData({
        ...formData,
        excluded_keywords: [...formData.excluded_keywords, input.value.trim()],
      });
      input.value = '';
    }
  };

  const removeExcludedKeyword = (keyword: string) => {
    setFormData({
      ...formData,
      excluded_keywords: formData.excluded_keywords.filter((k) => k !== keyword),
    });
  };

  if (isLoading) {
    return <div className="text-center py-12">Loading settings...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Settings</h1>
        <Button onClick={handleSave} disabled={updateMutation.isPending}>
          {updateMutation.isPending ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>

      {/* Default Job Titles */}
      <Card>
        <CardHeader>
          <CardTitle>Default Job Titles</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              id="job-title-input"
              placeholder="e.g., AI Engineer"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addJobTitle();
                }
              }}
            />
            <Button onClick={addJobTitle} variant="outline">
              Add
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {formData.default_job_titles.map((title) => (
              <div
                key={title}
                className="flex items-center gap-2 px-3 py-1 bg-secondary rounded-md"
              >
                <span>{title}</span>
                <button
                  onClick={() => removeJobTitle(title)}
                  className="text-destructive hover:text-destructive/80"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Default Domains */}
      <Card>
        <CardHeader>
          <CardTitle>Default Job Boards</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              id="domain-input"
              placeholder="e.g., greenhouse.io"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addDomain();
                }
              }}
            />
            <Button onClick={addDomain} variant="outline">
              Add
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {formData.default_domains.map((domain) => (
              <div
                key={domain}
                className="flex items-center gap-2 px-3 py-1 bg-secondary rounded-md"
              >
                <span>{domain}</span>
                <button
                  onClick={() => removeDomain(domain)}
                  className="text-destructive hover:text-destructive/80"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Search Filters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="max-yoe">Maximum Years of Experience</Label>
            <Input
              id="max-yoe"
              type="number"
              min="0"
              max="10"
              value={formData.max_yoe}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  max_yoe: parseInt(e.target.value) || 5,
                })
              }
              className="mt-2"
            />
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="remote-only"
              checked={formData.remote_only}
              onCheckedChange={(checked) =>
                setFormData({ ...formData, remote_only: !!checked })
              }
            />
            <Label htmlFor="remote-only">Remote Only</Label>
          </div>

          <div>
            <Label htmlFor="location-input">Preferred Locations</Label>
            <div className="flex gap-2 mt-2">
              <Input
                id="location-input"
                placeholder="e.g., San Francisco"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addLocation();
                  }
                }}
              />
              <Button onClick={addLocation} variant="outline">
                Add
              </Button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {formData.preferred_locations.map((location) => (
                <div
                  key={location}
                  className="flex items-center gap-2 px-3 py-1 bg-secondary rounded-md"
                >
                  <span>{location}</span>
                  <button
                    onClick={() => removeLocation(location)}
                    className="text-destructive hover:text-destructive/80"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div>
            <Label htmlFor="keyword-input">Excluded Keywords</Label>
            <div className="flex gap-2 mt-2">
              <Input
                id="keyword-input"
                placeholder="e.g., senior, director"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addExcludedKeyword();
                  }
                }}
              />
              <Button onClick={addExcludedKeyword} variant="outline">
                Add
              </Button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {formData.excluded_keywords.map((keyword) => (
                <div
                  key={keyword}
                  className="flex items-center gap-2 px-3 py-1 bg-secondary rounded-md"
                >
                  <span>{keyword}</span>
                  <button
                    onClick={() => removeExcludedKeyword(keyword)}
                    className="text-destructive hover:text-destructive/80"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
