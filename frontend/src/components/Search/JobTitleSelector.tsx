import { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { X, Plus } from 'lucide-react';
import { Badge } from '../ui/badge';

interface JobTitleSelectorProps {
  config: {
    jobTitles: string[];
    domains: string[];
    filters: any;
  };
  onChange: (config: any) => void;
}

export default function JobTitleSelector({ config, onChange }: JobTitleSelectorProps) {
  const [inputValue, setInputValue] = useState('');

  const addJobTitle = () => {
    if (inputValue.trim() && !config.jobTitles.includes(inputValue.trim())) {
      onChange({
        ...config,
        jobTitles: [...config.jobTitles, inputValue.trim()],
      });
      setInputValue('');
    }
  };

  const removeJobTitle = (title: string) => {
    onChange({
      ...config,
      jobTitles: config.jobTitles.filter((t) => t !== title),
    });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addJobTitle();
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold mb-4">Step 1: Select Job Titles</h2>
        <p className="text-muted-foreground mb-4">
          Enter the job titles you want to search for. You can add multiple titles.
        </p>
      </div>

      <div className="flex gap-2">
        <Input
          placeholder="e.g., AI Engineer, ML Engineer"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          className="flex-1"
        />
        <Button onClick={addJobTitle} type="button">
          <Plus className="h-4 w-4 mr-2" />
          Add
        </Button>
      </div>

      {config.jobTitles.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium">Selected Job Titles:</p>
          <div className="flex flex-wrap gap-2">
            {config.jobTitles.map((title) => (
              <Badge key={title} variant="secondary" className="flex items-center gap-2">
                {title}
                <button
                  onClick={() => removeJobTitle(title)}
                  className="hover:text-destructive"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
        </div>
      )}

      {config.jobTitles.length === 0 && (
        <p className="text-sm text-muted-foreground">
          Add at least one job title to continue.
        </p>
      )}
    </div>
  );
}
