import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchApi } from '../services/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import JobTitleSelector from '../components/Search/JobTitleSelector';
import DomainSelector from '../components/Search/DomainSelector';
import SearchProgress from '../components/Search/SearchProgress';
import SearchResults from '../components/Search/SearchResults';

export default function NewSearch() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [searchConfig, setSearchConfig] = useState({
    jobTitles: [] as string[],
    domains: [] as string[],
    filters: { maxYoe: 5, remoteOnly: false, locations: [] as string[] },
  });
  const [searchId, setSearchId] = useState<number | null>(null);

  const handleStartSearch = async () => {
    try {
      const result = await searchApi.startSearch({
        job_titles: searchConfig.jobTitles,
        domains: searchConfig.domains,
        filters: searchConfig.filters,
      });
      setSearchId(result.search_id);
      setStep(3);
    } catch (error) {
      console.error('Failed to start search:', error);
    }
  };

  const handleSearchComplete = () => {
    setStep(4);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">New Job Search</h1>

      {/* Progress Steps */}
      <div className="flex items-center justify-between mb-8">
        {[1, 2, 3, 4].map((s) => (
          <div key={s} className="flex items-center flex-1">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${
                step >= s ? 'bg-primary text-primary-foreground' : 'bg-muted'
              }`}
            >
              {s}
            </div>
            {s < 4 && (
              <div
                className={`flex-1 h-1 mx-2 ${
                  step > s ? 'bg-primary' : 'bg-muted'
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* Step Content */}
      <Card>
        <CardContent className="pt-6">
          {step === 1 && (
            <JobTitleSelector
              config={searchConfig}
              onChange={setSearchConfig}
            />
          )}
          {step === 2 && (
            <DomainSelector
              config={searchConfig}
              onChange={setSearchConfig}
            />
          )}
          {step === 3 && searchId && (
            <SearchProgress
              searchId={searchId}
              onComplete={handleSearchComplete}
            />
          )}
          {step === 4 && searchId && (
            <SearchResults searchId={searchId} />
          )}
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between mt-8">
        <Button
          variant="outline"
          onClick={() => setStep((s) => Math.max(1, s - 1))}
          disabled={step === 1}
        >
          Back
        </Button>
        {step === 2 && (
          <Button onClick={handleStartSearch}>Start Search</Button>
        )}
        {step === 4 && (
          <Button onClick={() => navigate('/')}>Save to Dashboard</Button>
        )}
        {step < 2 && (
          <Button onClick={() => setStep((s) => s + 1)}>Next</Button>
        )}
      </div>
    </div>
  );
}
