import { useEffect, useState } from 'react';

/**
 * Component to check if backend is reachable
 * Useful for debugging connection issues
 */
export default function BackendStatus() {
  const [status, setStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch('/health');
        if (response.ok) {
          setStatus('online');
        } else {
          setStatus('offline');
          setError(`Backend returned ${response.status}`);
        }
      } catch (err: any) {
        setStatus('offline');
        setError(err.message || 'Cannot connect to backend');
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 5000); // Check every 5 seconds
    return () => clearInterval(interval);
  }, []);

  if (status === 'checking') {
    return (
      <div className="text-xs text-muted-foreground">
        Checking backend connection...
      </div>
    );
  }

  if (status === 'offline') {
    return (
      <div className="text-xs text-red-600 bg-red-50 p-2 rounded border border-red-200">
        ⚠️ Backend offline: {error}
        <br />
        <span className="text-muted-foreground">
          Start backend: from project root run <code>cd backend && uvicorn app.main:app --reload</code> (or use your venv)
        </span>
      </div>
    );
  }

  return (
    <div className="text-xs text-green-600">
      ✓ Backend connected
    </div>
  );
}
