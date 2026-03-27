import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import AppLayout from "./components/AppLayout";
import Index from "./pages/Index";
import Scanner from "./pages/Scanner";
import ThreatModel from "./pages/ThreatModel";
import AuditLog from "./pages/AuditLog";
import SettingsPage from "./pages/Settings";
import TamperProofRecords from "./pages/TamperProofRecords";
import NotFound from "./pages/NotFound";
import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
const queryClient = new QueryClient();
const App = () => /*#__PURE__*/_jsx(QueryClientProvider, {
  client: queryClient,
  children: /*#__PURE__*/_jsxs(TooltipProvider, {
    children: [/*#__PURE__*/_jsx(Toaster, {}), /*#__PURE__*/_jsx(Sonner, {}), /*#__PURE__*/_jsx(BrowserRouter, {
      children: /*#__PURE__*/_jsx(AppLayout, {
        children: /*#__PURE__*/_jsxs(Routes, {
          children: [/*#__PURE__*/_jsx(Route, {
            path: "/",
            element: /*#__PURE__*/_jsx(Index, {})
          }), /*#__PURE__*/_jsx(Route, {
            path: "/scanner",
            element: /*#__PURE__*/_jsx(Scanner, {})
          }), /*#__PURE__*/_jsx(Route, {
            path: "/threats",
            element: /*#__PURE__*/_jsx(ThreatModel, {})
          }), /*#__PURE__*/_jsx(Route, {
            path: "/audit-log",
            element: /*#__PURE__*/_jsx(AuditLog, {})
          }), /*#__PURE__*/_jsx(Route, {
            path: "/records",
            element: /*#__PURE__*/_jsx(TamperProofRecords, {})
          }), /*#__PURE__*/_jsx(Route, {
            path: "/settings",
            element: /*#__PURE__*/_jsx(SettingsPage, {})
          }), /*#__PURE__*/_jsx(Route, {
            path: "*",
            element: /*#__PURE__*/_jsx(NotFound, {})
          })]
        })
      })
    })]
  })
});
export default App;