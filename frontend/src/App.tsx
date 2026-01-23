import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import NewSearch from './pages/NewSearch';
import JobDetails from './pages/JobDetails';
import Settings from './pages/Settings';
import Layout from './components/Layout';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/search/new" element={<NewSearch />} />
          <Route path="/jobs/:id" element={<JobDetails />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
