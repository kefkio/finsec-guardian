import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import AppLayout from "./components/AppLayout";
import Index from "./pages/Index";
import Scanner from "./pages/Scanner";
import ScanDetail from "./pages/ScanDetail";
import ThreatModel from "./pages/ThreatModel";
import AuditLog from "./pages/AuditLog";
import SettingsPage from "./pages/Settings";
import TamperProofRecords from "./pages/TamperProofRecords";
import NotFound from "./pages/NotFound";
import Login from "./pages/Login";
import { tokenStorage } from "./lib/api";

const queryClient = new QueryClient();

const ProtectedRoute = ({ children }) => {
  if (!tokenStorage.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <Routes>
                    <Route path="/" element={<Index />} />
                    <Route path="/scanner" element={<Scanner />} />
                    <Route path="/scanner/:id" element={<ScanDetail />} />
                    <Route path="/threats" element={<ThreatModel />} />
                    <Route path="/audit-log" element={<AuditLog />} />
                    <Route path="/records" element={<TamperProofRecords />} />
                    <Route path="/settings" element={<SettingsPage />} />
                    <Route path="*" element={<NotFound />} />
                  </Routes>
                </AppLayout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;