/**
 * src/App.jsx — Route definitions.
 *
 * All 11 routes are defined here.
 * Protected routes are wrapped with <RouteGuard>.
 */

import { Routes, Route, Navigate } from 'react-router-dom';

import Layout from './components/Layout';
import RouteGuard from './components/RouteGuard';

import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import DashboardPage from './pages/DashboardPage';
import OrgSetupPage from './pages/OrgSetupPage';
import AssetsPage from './pages/AssetsPage';
import AssetDetailPage from './pages/AssetDetailPage';
import AllocationsPage from './pages/AllocationsPage';
import BookingsPage from './pages/BookingsPage';
import MaintenancePage from './pages/MaintenancePage';
import AuditsPage from './pages/AuditsPage';
import ReportsPage from './pages/ReportsPage';
import NotificationsPage from './pages/NotificationsPage';

export default function App() {
  return (
    <Routes>
      {/* ── Public routes ── */}
      <Route path="/login"  element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />

      {/* ── Protected routes (shared Layout) ── */}
      <Route
        element={
          <RouteGuard>
            <Layout />
          </RouteGuard>
        }
      >
        <Route path="/dashboard"     element={<DashboardPage />} />
        <Route path="/assets"        element={<AssetsPage />} />
        <Route path="/my-assets"     element={<AssetsPage endpoint="/assets/mine" title="My Assets" />} />
        <Route path="/assets/:id"    element={<AssetDetailPage />} />
        <Route path="/allocations"   element={<AllocationsPage />} />
        <Route path="/bookings"      element={<BookingsPage />} />
        <Route path="/maintenance"   element={<MaintenancePage />} />
        <Route path="/notifications" element={<NotificationsPage />} />

        {/* Admin + AssetManager only */}
        <Route
          path="/audits"
          element={
            <RouteGuard roles={['Admin', 'AssetManager']}>
              <AuditsPage />
            </RouteGuard>
          }
        />
        <Route
          path="/reports"
          element={
            <RouteGuard roles={['Admin', 'AssetManager']}>
              <ReportsPage />
            </RouteGuard>
          }
        />

        {/* Admin only */}
        <Route
          path="/org-setup"
          element={
            <RouteGuard roles={['Admin']}>
              <OrgSetupPage />
            </RouteGuard>
          }
        />
      </Route>

      {/* ── Default redirect ── */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
