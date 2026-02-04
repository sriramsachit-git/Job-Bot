import { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Checkbox } from '../ui/checkbox';
import { Label } from '../ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface DomainSelectorProps {
  config: {
    jobTitles: string[];
    domains: string[];
    filters: {
      maxYoe: number;
      remoteOnly: boolean;
      locations: string[];
      numResults: number;
      maxExtractionBatch: number | '';
    };
  };
  onChange: (config: any) => void;
}

const DEFAULT_DOMAINS = [
  'ashbyhq.com',
  'greenhouse.io',
  'lever.co',
  'pinpointhq.com',
  'jobs.workable.com',
  'breezy.hr',
  'wellfound.com',
  'workatastartup.com',
  'oraclecloud.com',
  'myworkdayjobs.com',
  'recruitee.com',
  'rippling.com',
  'rippling-ats.com',
  'jobs.gusto.com',
  'careerpuck.com',
  'teamtailor.com',
  'jobs.smartrecruiters.com',
  'jobappnetwork.com',
  'homerun.co',
  'gem.com',
  'trakstar.com',
  'catsone.com',
  'applytojob.com',
  'jobvite.com',
  'icims.com',
  'dover.io',
  'notion.site',
  'builtin.com',
  'workforcenow.adp.com',
  'myjobs.adp.com',
  'trinethire.com',
  'recruiting.paylocity.com',
  'keka.com',
];

export default function DomainSelector({ config, onChange }: DomainSelectorProps) {
  const [customDomain, setCustomDomain] = useState('');

  const toggleDomain = (domain: string) => {
    if (config.domains.includes(domain)) {
      onChange({
        ...config,
        domains: config.domains.filter((d) => d !== domain),
      });
    } else {
      onChange({
        ...config,
        domains: [...config.domains, domain],
      });
    }
  };

  const selectAll = () => {
    onChange({
      ...config,
      domains: [...DEFAULT_DOMAINS],
    });
  };

  const deselectAll = () => {
    onChange({
      ...config,
      domains: [],
    });
  };

  const addCustomDomain = () => {
    if (customDomain.trim() && !config.domains.includes(customDomain.trim())) {
      onChange({
        ...config,
        domains: [...config.domains, customDomain.trim()],
      });
      setCustomDomain('');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-4">Step 2: Select Job Boards</h2>
        <p className="text-muted-foreground mb-4">
          Choose which job boards to search. Select at least one domain.
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

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {DEFAULT_DOMAINS.map((domain) => (
          <div key={domain} className="flex items-center space-x-2">
            <Checkbox
              id={domain}
              checked={config.domains.includes(domain)}
              onCheckedChange={() => toggleDomain(domain)}
            />
            <Label htmlFor={domain} className="cursor-pointer">
              {domain}
            </Label>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <Input
          placeholder="Add custom domain (e.g., example.com)"
          value={customDomain}
          onChange={(e) => setCustomDomain(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              addCustomDomain();
            }
          }}
          className="flex-1"
        />
        <Button onClick={addCustomDomain} variant="outline">
          Add
        </Button>
      </div>

      {/* Additional Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Additional Filters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="remote-only"
              checked={config.filters.remoteOnly}
              onCheckedChange={(checked) =>
                onChange({
                  ...config,
                  filters: { ...config.filters, remoteOnly: !!checked },
                })
              }
            />
            <Label htmlFor="remote-only">Remote Only</Label>
          </div>

          <div>
            <Label htmlFor="max-yoe">Max Years of Experience:</Label>
            <Input
              id="max-yoe"
              type="number"
              min="0"
              max="10"
              value={config.filters.maxYoe}
              onChange={(e) =>
                onChange({
                  ...config,
                  filters: {
                    ...config.filters,
                    maxYoe: parseInt(e.target.value) || 5,
                  },
                })
              }
              className="mt-2"
            />
          </div>

          {/* Execution limits (customisable at run time) */}
          <div className="border-t pt-4 mt-4 space-y-4">
            <p className="text-sm font-medium text-muted-foreground">
              Search execution limits
            </p>
            <div>
              <Label htmlFor="num-results">
                Max search results per query (1–100)
              </Label>
              <Input
                id="num-results"
                type="number"
                min={1}
                max={100}
                value={config.filters.numResults ?? 100}
                onChange={(e) => {
                  const v = parseInt(e.target.value, 10);
                  onChange({
                    ...config,
                    filters: {
                      ...config.filters,
                      numResults: Number.isNaN(v) ? 100 : Math.min(100, Math.max(1, v)),
                    },
                  });
                }}
                className="mt-2"
              />
            </div>
            <div>
              <Label htmlFor="max-extraction">
                Max URLs to extract per run (leave empty for no limit)
              </Label>
              <Input
                id="max-extraction"
                type="number"
                min={1}
                placeholder="No limit"
                value={config.filters.maxExtractionBatch === '' ? '' : config.filters.maxExtractionBatch}
                onChange={(e) => {
                  const raw = e.target.value.trim();
                  const v = raw === '' ? '' : parseInt(raw, 10);
                  onChange({
                    ...config,
                    filters: {
                      ...config.filters,
                      maxExtractionBatch:
                        v === '' || Number.isNaN(v as number)
                          ? ''
                          : Math.max(1, v as number),
                    },
                  });
                }}
                className="mt-2"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {config.domains.length === 0 && (
        <p className="text-sm text-destructive">
          Please select at least one domain to continue.
        </p>
      )}
    </div>
  );
}
