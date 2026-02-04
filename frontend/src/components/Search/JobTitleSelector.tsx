import { Button } from '../ui/button';
import { Checkbox } from '../ui/checkbox';
import { Label } from '../ui/label';

const DEFAULT_JOB_TITLES = [
  'Data Scientist',
  'AI engineer',
  'ML engineer',
  'Data engineer',
];

interface JobTitleSelectorProps {
  config: {
    jobTitles: string[];
    domains: string[];
    filters: any;
  };
  onChange: (config: any) => void;
}

export default function JobTitleSelector({ config, onChange }: JobTitleSelectorProps) {
  const toggleTitle = (title: string) => {
    if (config.jobTitles.includes(title)) {
      onChange({
        ...config,
        jobTitles: config.jobTitles.filter((t) => t !== title),
      });
    } else {
      onChange({
        ...config,
        jobTitles: [...config.jobTitles, title],
      });
    }
  };

  const selectAll = () => {
    onChange({
      ...config,
      jobTitles: [...DEFAULT_JOB_TITLES],
    });
  };

  const deselectAll = () => {
    onChange({
      ...config,
      jobTitles: [],
    });
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold mb-4">Step 1: Select Job Titles</h2>
        <p className="text-muted-foreground mb-4">
          Choose the job titles you want to search for. Select at least one.
        </p>
      </div>

      <div className="flex gap-2 mb-4">
        <Button variant="outline" onClick={selectAll} size="sm">
          Select All
        </Button>
        <Button variant="outline" onClick={deselectAll} size="sm">
          Deselect All
        </Button>
      </div>

      <div className="space-y-3">
        {DEFAULT_JOB_TITLES.map((title) => (
          <div key={title} className="flex items-center space-x-2">
            <Checkbox
              id={title}
              checked={config.jobTitles.includes(title)}
              onCheckedChange={() => toggleTitle(title)}
            />
            <Label htmlFor={title} className="cursor-pointer font-normal">
              {title}
            </Label>
          </div>
        ))}
      </div>

      {config.jobTitles.length === 0 && (
        <p className="text-sm text-muted-foreground mt-4">
          Select at least one job title to continue.
        </p>
      )}
    </div>
  );
}
