import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "@/shared/layout/Layout";
import { AdminApprovalsPage } from "@/features/admin/AdminApprovalsPage";
import { BookingsPage } from "@/features/emails/BookingsPage";
import { CancellationsPage } from "@/features/emails/CancellationsPage";
import { ChangesPage } from "@/features/emails/ChangesPage";
import { CostsPage } from "@/features/dashboard/CostsPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { MessagesPage } from "@/features/emails/MessagesPage";
import { OnboardingPage } from "@/features/onboarding/OnboardingPage";
import { PropertiesPage } from "@/features/properties/PropertiesPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { ReviewQueuePage } from "@/features/review/ReviewQueuePage";
import { SettingsPage } from "@/features/settings/SettingsPage";
import { PlatformAdminRoute } from "@/routes/PlatformAdminRoute";
import { ProtectedRoute } from "@/routes/ProtectedRoute";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="bookings" element={<BookingsPage />} />
            <Route path="cancellations" element={<CancellationsPage />} />
            <Route path="changes" element={<ChangesPage />} />
            <Route path="messages" element={<MessagesPage />} />
            <Route path="properties" element={<PropertiesPage />} />
            <Route path="review" element={<ReviewQueuePage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="costs" element={<CostsPage />} />
            <Route element={<PlatformAdminRoute />}>
              <Route path="admin/approvals" element={<AdminApprovalsPage />} />
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
