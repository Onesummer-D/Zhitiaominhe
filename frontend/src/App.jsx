import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Mediation from './pages/Mediation';
import Cases from './pages/Cases';
import Knowledge from './pages/Knowledge';
import Training from './pages/Training';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/mediation" element={<Mediation />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/knowledge" element={<Knowledge />} />
          <Route path="/training" element={<Training />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
