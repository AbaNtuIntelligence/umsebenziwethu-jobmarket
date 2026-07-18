import { Navigate, Route, Routes } from "react-router-dom";
import AppShell from "./components/AppShell";
import ProtectedRoute from "./components/ProtectedRoute";
import ApplicationsPage from "./pages/ApplicationsPage";
import EmployerDashboard from "./pages/EmployerDashboard";
import HomePage from "./pages/HomePage";
import JobDetailPage from "./pages/JobDetailPage";
import LoginPage from "./pages/LoginPage";
import PostJobPage from "./pages/PostJobPage";
import RegisterPage from "./pages/RegisterPage";
import SavedJobsPage from "./pages/SavedJobsPage";
import ApplicantsPage from "./pages/ApplicantsPage";
import FeedbackPage from "./pages/FeedbackPage";
import PrivacyPage from "./pages/PrivacyPage";
import ProfilePage from "./pages/ProfilePage";
import SettingsPage from "./pages/SettingsPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import ApplicationDetailPage from "./pages/ApplicationDetailPage";
import NotificationsPage from "./pages/NotificationsPage";
import InterviewHubPage from "./pages/InterviewHubPage";

export default function App() {
  return <Routes>
    <Route element={<AppShell />}>
      <Route path="/" element={<HomePage />} />
      <Route path="/jobs/:id" element={<JobDetailPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/privacy" element={<PrivacyPage />} />
      <Route path="/feedback" element={<FeedbackPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password/:uid/:token" element={<ResetPasswordPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/saved" element={<SavedJobsPage />} />
        <Route path="/applications" element={<ApplicationsPage />} />
        <Route path="/applications/:id" element={<ApplicationDetailPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/interviews" element={<InterviewHubPage />} />
        <Route path="/employer" element={<EmployerDashboard />} />
        <Route path="/post-job" element={<PostJobPage />} />
        <Route path="/applicants" element={<ApplicantsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>;
}
