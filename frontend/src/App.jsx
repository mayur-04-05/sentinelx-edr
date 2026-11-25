import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Endpoints from './pages/Endpoints';
import Alerts from './pages/Alerts';
import Incidents from './pages/Incidents';
import IOCs from './pages/IOCs';
import Mitre from './pages/Mitre';
import FileAnalysis from './pages/FileAnalysis';
import Reports from './pages/Reports';
import AuditLogs from './pages/AuditLogs';
import Settings from './pages/Settings';
import MainLayout from './layouts/MainLayout';
import EndpointDetail from './pages/EndpointDetail';
import IncidentDetail from './pages/IncidentDetail';

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-bgDark flex items-center justify-center text-textPrimary">
        <span className="w-8 h-8 border-4 border-accentBlue border-t-transparent rounded-full animate-spin"></span>
      </div>
    );
  }
  
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Authentication Route */}
          <Route path="/login" element={<Login />} />

          {/* Protected SOC Dashboard Routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="endpoints" element={<Endpoints />} />
            <Route path="endpoints/:id" element={<EndpointDetail />} />
            <Route path="alerts" element={<Alerts />} />
            <Route path="incidents" element={<Incidents />} />
            <Route path="incidents/:id" element={<IncidentDetail />} />
            <Route path="iocs" element={<IOCs />} />
            <Route path="mitre" element={<Mitre />} />
            <Route path="file-analysis" element={<FileAnalysis />} />
            <Route path="reports" element={<Reports />} />
            <Route path="audit-logs" element={<AuditLogs />} />
            <Route path="settings" element={<Settings />} />
          </Route>

          {/* Fallback Catch-all Redirect */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
