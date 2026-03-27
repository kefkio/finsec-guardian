import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Shield, Search, AlertTriangle, ScrollText, LayoutDashboard, Settings, ChevronLeft, Link2, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
const navItems = [{
  to: "/",
  icon: LayoutDashboard,
  label: "Dashboard"
}, {
  to: "/scanner",
  icon: Search,
  label: "Contract Scanner"
}, {
  to: "/threats",
  icon: AlertTriangle,
  label: "Threat Model"
}, {
  to: "/records",
  icon: Link2,
  label: "Tamper-Proof Records"
}, {
  to: "/audit-log",
  icon: ScrollText,
  label: "Audit Log"
}, {
  to: "/settings",
  icon: Settings,
  label: "Settings"
}];
const AppLayout = ({
  children
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  return /*#__PURE__*/_jsxs("div", {
    className: "flex min-h-screen",
    children: [/*#__PURE__*/_jsxs("aside", {
      className: cn("fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-border bg-sidebar transition-all duration-300", collapsed ? "w-16" : "w-60"),
      children: [/*#__PURE__*/_jsxs("div", {
        className: "flex h-16 items-center gap-3 border-b border-border px-4",
        children: [/*#__PURE__*/_jsx("div", {
          className: "flex h-8 w-8 items-center justify-center rounded-md gradient-primary",
          children: /*#__PURE__*/_jsx(Shield, {
            className: "h-5 w-5 text-primary-foreground"
          })
        }), !collapsed && /*#__PURE__*/_jsxs("div", {
          className: "flex flex-col",
          children: [/*#__PURE__*/_jsxs("span", {
            className: "text-sm font-bold text-foreground tracking-tight",
            children: ["DeFi", /*#__PURE__*/_jsx("span", {
              className: "text-gradient-primary",
              children: "Guard"
            })]
          }), /*#__PURE__*/_jsx("span", {
            className: "text-[10px] font-mono text-muted-foreground",
            children: "v1.0.0"
          })]
        })]
      }), /*#__PURE__*/_jsx("nav", {
        className: "flex-1 space-y-1 p-3",
        children: navItems.map(item => {
          const isActive = location.pathname === item.to;
          const link = /*#__PURE__*/_jsxs(Link, {
            to: item.to,
            className: cn("flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-all", isActive ? "bg-primary/10 text-primary glow-primary" : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"),
            children: [/*#__PURE__*/_jsx(item.icon, {
              className: cn("h-4 w-4 shrink-0", isActive && "text-primary")
            }), !collapsed && /*#__PURE__*/_jsx("span", {
              children: item.label
            })]
          }, item.to);
          if (collapsed) {
            return /*#__PURE__*/_jsxs(Tooltip, {
              delayDuration: 0,
              children: [/*#__PURE__*/_jsx(TooltipTrigger, {
                asChild: true,
                children: link
              }), /*#__PURE__*/_jsx(TooltipContent, {
                side: "right",
                children: item.label
              })]
            }, item.to);
          }
          return link;
        })
      }), /*#__PURE__*/_jsx("div", {
        className: "border-t border-border p-3",
        children: /*#__PURE__*/_jsx(Button, {
          variant: "ghost",
          size: "sm",
          onClick: () => setCollapsed(!collapsed),
          className: "w-full justify-center text-muted-foreground hover:text-foreground",
          children: collapsed ? /*#__PURE__*/_jsx(ChevronRight, {
            className: "h-4 w-4"
          }) : /*#__PURE__*/_jsx(ChevronLeft, {
            className: "h-4 w-4"
          })
        })
      })]
    }), /*#__PURE__*/_jsx("main", {
      className: cn("flex-1 transition-all duration-300", collapsed ? "ml-16" : "ml-60"),
      children: /*#__PURE__*/_jsx("div", {
        className: "p-6",
        children: children
      })
    })]
  });
};
export default AppLayout;