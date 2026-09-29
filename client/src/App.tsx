import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';

import { AppShell } from '@/components/shell/AppShell';
import { useSessionBootstrap } from '@/hooks/useSessionBootstrap';
import { clearToken, hasToken } from '@/lib/auth';
import { useSessionStore } from '@/store/session';
import { CatalogPage } from '@/pages/CatalogPage';
import { DatabasesPage } from '@/pages/DatabasesPage';
import { GovernancePage } from '@/pages/GovernancePage';
import { LoginPage } from '@/pages/LoginPage';
import { ReportsPage } from '@/pages/ReportsPage';
import { SignupPage } from '@/pages/SignupPage';
import { WorkbenchPage } from '@/pages/WorkbenchPage';
import { WorkflowPage } from '@/pages/WorkflowPage';

function ProtectedLayout() {
  const location = useLocation();
  const queryClient = useQueryClient();
  const resetSession = useSessionStore((state) => state.resetSession);

  const { isPending, isError } = useSessionBootstrap();

  if (!hasToken()) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (isPending) {
    return <div className="route-loader">Rebuilding workspace context...</div>;
  }

  if (isError) {
    clearToken();
    resetSession();
    void queryClient.clear();
    return <Navigate to="/login" replace />;
  }

  return <AppShell><Outlet /></AppShell>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />

      <Route element={<ProtectedLayout />}>
        <Route path="/" element={<Navigate to="/workbench" replace />} />
        <Route path="/workbench" element={<WorkbenchPage />} />
        <Route path="/databases" element={<DatabasesPage />} />
        <Route path="/catalog" element={<CatalogPage />} />
        <Route path="/workflow" element={<WorkflowPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/governance" element={<GovernancePage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
