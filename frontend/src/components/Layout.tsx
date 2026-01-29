import { Link, useLocation } from 'react-router-dom';
import { Briefcase, Search, Settings } from 'lucide-react';
import BackendStatus from './BackendStatus';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2">
              <Briefcase className="h-6 w-6" />
              <span className="text-xl font-bold">Job Search Pipeline</span>
            </Link>
            <BackendStatus />
            <nav className="flex items-center gap-4">
              <Link
                to="/"
                className={`flex items-center gap-2 px-3 py-2 rounded-md ${
                  location.pathname === '/' ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
                }`}
              >
                <Briefcase className="h-4 w-4" />
                Dashboard
              </Link>
              <Link
                to="/search/new"
                className={`flex items-center gap-2 px-3 py-2 rounded-md ${
                  location.pathname === '/search/new' ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
                }`}
              >
                <Search className="h-4 w-4" />
                New Search
              </Link>
              <Link
                to="/settings"
                className={`flex items-center gap-2 px-3 py-2 rounded-md ${
                  location.pathname === '/settings' ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
                }`}
              >
                <Settings className="h-4 w-4" />
                Settings
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  );
}
