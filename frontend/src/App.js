import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { Toaster } from "@/components/ui/sonner";
import AppLayout from "@/components/AppLayout";
import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import UploadPage from "@/pages/Upload";
import Insights from "@/pages/Insights";
import Approvals from "@/pages/Approvals";
import Reports from "@/pages/Reports";
import Audit from "@/pages/Audit";
import Journey from "@/pages/Journey";
import HRResumeScreening from "@/pages/HRResumeScreening";
import HROnboarding from "@/pages/HROnboarding";

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading)
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="h-8 w-8 rounded-lg bg-primary/20 border border-primary/40 animate-pulse" />
      </div>
    );
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function RoleGuard({ allowedRoles, children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/app/dashboard" replace />;
  }
  return children;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/app/journey" element={<Protected><Journey /></Protected>} />
          <Route path="/app" element={<Protected><AppLayout /></Protected>}>
            <Route index element={<Navigate to="/app/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="upload" element={<RoleGuard allowedRoles={["admin", "analyst"]}><UploadPage /></RoleGuard>} />
            <Route path="insights" element={<RoleGuard allowedRoles={["admin", "analyst", "manager"]}><Insights /></RoleGuard>} />
            <Route path="hr-screening" element={<RoleGuard allowedRoles={["admin", "hr_manager"]}><HRResumeScreening /></RoleGuard>} />
            <Route path="hr-onboarding" element={<RoleGuard allowedRoles={["admin", "hr_manager"]}><HROnboarding /></RoleGuard>} />
            <Route path="approvals" element={<RoleGuard allowedRoles={["admin", "manager", "executive", "hr_manager"]}><Approvals /></RoleGuard>} />
            <Route path="reports" element={<RoleGuard allowedRoles={["admin", "executive"]}><Reports /></RoleGuard>} />
            <Route path="audit" element={<RoleGuard allowedRoles={["admin", "manager", "analyst", "hr_manager"]}><Audit /></RoleGuard>} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="bottom-right" theme="light" richColors />
    </AuthProvider>
  );
}

export default App;
