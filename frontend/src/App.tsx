import { Routes, Route, Navigate } from "react-router-dom";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { RepositoriesPage } from "./pages/RepositoriesPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { InterviewPage } from "./pages/InterviewPage";
import { LearningPage } from "./pages/LearningPage";
import { OpenSourcePage } from "./pages/OpenSourcePage";
import { PortfolioPage } from "./pages/PortfolioPage";
import { ResumePage } from "./pages/ResumePage";
import { SkillsPage } from "./pages/SkillsPage";
import { SocialPage } from "./pages/SocialPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { ProtectedRoute } from "./components/ProtectedRoute";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/repositories"
        element={
          <ProtectedRoute>
            <RepositoriesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/documents"
        element={
          <ProtectedRoute>
            <DocumentsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/portfolio"
        element={
          <ProtectedRoute>
            <PortfolioPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/resume"
        element={
          <ProtectedRoute>
            <ResumePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/social"
        element={
          <ProtectedRoute>
            <SocialPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/skills"
        element={
          <ProtectedRoute>
            <SkillsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/learning"
        element={
          <ProtectedRoute>
            <LearningPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/interview"
        element={
          <ProtectedRoute>
            <InterviewPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/opensource"
        element={
          <ProtectedRoute>
            <OpenSourcePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/analytics"
        element={
          <ProtectedRoute>
            <AnalyticsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/notifications"
        element={
          <ProtectedRoute>
            <NotificationsPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
