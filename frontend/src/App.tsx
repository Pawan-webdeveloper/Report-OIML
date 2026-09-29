import { useEffect } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import { RequireAuth, RequireRole } from './components/guards';
import AppLayout from './components/layout/AppLayout';
import LoginPage from './pages/LoginPage';
import ChangePasswordPage from './pages/ChangePasswordPage';
import DashboardPage from './pages/DashboardPage';
import PartiesPage from './pages/PartiesPage';
import InstrumentsListPage from './pages/InstrumentsListPage';
import InstrumentFormPage from './pages/InstrumentFormPage';
import EvaluationCreatePage from './pages/EvaluationCreatePage';
import EvaluationDetailPage from './pages/EvaluationDetailPage';
import ReportsPage from './pages/ReportsPage';
import RulesetPage from './pages/RulesetPage';
import AuditLogPage from './pages/AuditLogPage';
import AdminUsersPage from './pages/AdminUsersPage';
import TestEntryPage from './pages/tests/TestEntryPage';
import { NotFoundPage } from './pages/PlaceholderPage';

export default function App() {
  const bootstrap = useAuthStore((s) => s.bootstrap);
  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<RequireAuth />}>
          <Route element={<AppLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="change-password" element={<ChangePasswordPage />} />

            <Route path="parties" element={<PartiesPage />} />

            <Route path="instruments" element={<InstrumentsListPage />} />
            <Route path="instruments/new" element={
              <RequireRole roles={['ADMIN', 'ENGINEER']}>
                <InstrumentFormPage mode="create" />
              </RequireRole>
            } />
            <Route path="instruments/:id/edit" element={
              <RequireRole roles={['ADMIN', 'ENGINEER']}>
                <InstrumentFormPage mode="edit" />
              </RequireRole>
            } />

            <Route path="evaluations" element={<DashboardPage />} />
            <Route path="evaluations/new" element={
              <RequireRole roles={['ADMIN', 'ENGINEER']}>
                <EvaluationCreatePage />
              </RequireRole>
            } />
            <Route path="evaluations/:id" element={<EvaluationDetailPage />} />
            <Route path="evaluations/:id/tests/:kind/:instanceNo?" element={
              <RequireRole roles={['ENGINEER', 'REVIEWER', 'ADMIN']}>
                <TestEntryPage />
              </RequireRole>
            } />

            <Route path="reports" element={<ReportsPage />} />
            <Route path="rulesets" element={<RulesetPage />} />

            <Route path="audit" element={
              <RequireRole roles={['ADMIN', 'REVIEWER']}>
                <AuditLogPage />
              </RequireRole>
            } />
            <Route path="admin/users" element={
              <RequireRole roles={['ADMIN']}>
                <AdminUsersPage />
              </RequireRole>
            } />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}