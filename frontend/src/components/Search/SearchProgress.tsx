import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { searchApi } from '../../services/api';
import { Card, CardContent } from '../ui/card';
import { Progress } from '../ui/progress';
import { CheckCircle2, Loader2, XCircle } from 'lucide-react';

interface SearchProgressProps {
  searchId: number;
  onComplete: () => void;
}

export default function SearchProgress({ searchId, onComplete }: SearchProgressProps) {
  const [ws, setWs] = useState<WebSocket | null>(null);

  const { data: status } = useQuery({
    queryKey: ['search-status', searchId],
    queryFn: () => searchApi.getSearchStatus(searchId),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === 'completed' || data?.status === 'failed' || data?.status === 'cancelled') {
        return false;
      }
      return 2000; // Poll every 2 seconds
    },
  });

  useEffect(() => {
    // Connect to WebSocket for real-time updates
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/search/ws/${searchId}`;
    
    const websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
      console.log('WebSocket connected');
    };
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Update query cache with new status
      // This will trigger a re-render
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    websocket.onclose = () => {
      console.log('WebSocket disconnected');
    };
    
    setWs(websocket);
    
    return () => {
      websocket.close();
    };
  }, [searchId]);

  useEffect(() => {
    if (status?.status === 'completed' || status?.status === 'failed') {
      if (status.status === 'completed') {
        onComplete();
      }
    }
  }, [status?.status, onComplete]);

  if (!status) {
    return <div className="text-center py-12">Loading search status...</div>;
  }

  const steps = [
    { key: 'searching', label: 'Google Search', icon: Loader2 },
    { key: 'extracting', label: 'Content Extraction', icon: Loader2 },
    { key: 'filtering', label: 'Pre-filtering', icon: Loader2 },
    { key: 'parsing', label: 'AI Parsing', icon: Loader2 },
    { key: 'scoring', label: 'Scoring', icon: Loader2 },
    { key: 'saving', label: 'Saving Results', icon: Loader2 },
  ];

  const getStepStatus = (stepKey: string) => {
    if (!status.current_step) return 'pending';
    const currentIndex = steps.findIndex((s) => s.key === status.current_step);
    const stepIndex = steps.findIndex((s) => s.key === stepKey);
    
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-4">Search in Progress</h2>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Progress</span>
            <span>{status.progress}%</span>
          </div>
          <Progress value={status.progress} className="h-2" />
        </div>
      </div>

      <div className="space-y-4">
        {steps.map((step) => {
          const stepStatus = getStepStatus(step.key);
          const Icon = step.icon;
          
          return (
            <div key={step.key} className="flex items-center gap-4">
              {stepStatus === 'completed' ? (
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              ) : stepStatus === 'active' ? (
                <Loader2 className="h-5 w-5 text-primary animate-spin" />
              ) : (
                <div className="h-5 w-5 rounded-full border-2 border-muted" />
              )}
              <div className="flex-1">
                <p className={`font-medium ${stepStatus === 'active' ? 'text-primary' : ''}`}>
                  {step.label}
                </p>
                {step.key === 'searching' && status.urls_found > 0 && (
                  <p className="text-sm text-muted-foreground">
                    Found {status.urls_found} URLs
                  </p>
                )}
                {step.key === 'extracting' && status.jobs_extracted > 0 && (
                  <p className="text-sm text-muted-foreground">
                    Extracted {status.jobs_extracted} jobs
                  </p>
                )}
                {step.key === 'parsing' && status.jobs_parsed > 0 && (
                  <p className="text-sm text-muted-foreground">
                    Parsed {status.jobs_parsed} jobs
                  </p>
                )}
                {step.key === 'saving' && status.jobs_saved > 0 && (
                  <p className="text-sm text-muted-foreground">
                    Saved {status.jobs_saved} jobs
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {status.error_message && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <XCircle className="h-5 w-5" />
              <p className="font-medium">Error: {status.error_message}</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
