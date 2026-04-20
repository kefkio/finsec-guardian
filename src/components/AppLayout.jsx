import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Shield, Search, AlertTriangle, ScrollText, LayoutDashboard, Settings, ChevronLeft, Link2, ChevronRight, LogOut, Menu, X, Sun, Moon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { authApi } from "@/lib/api";
import { useIsMobile } from "@/hooks/use-mobile";
import { useTheme } from "@/hooks/use-theme";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/scanner", icon: Search, label: "Contract Scanner" },
  { to: "/threats", icon: AlertTriangle, label: "Threat Model" },
  { to: "/records", icon: Link2, label: "Tamper-Proof Records" },
  { to: "/audit-log", icon: ScrollText, label: "Audit Log" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

const AppLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const isMobile = useIsMobile();
  const location = useLocation();
  const { theme, toggle: toggleTheme } = useTheme();

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen">
      {/* Mobile backdrop */}
      {isMobile && mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside
        className={cn(
          "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-border bg-sidebar transition-all duration-300",
          isMobile
            ? cn("w-64", mobileOpen ? "translate-x-0" : "-translate-x-full")
            : collapsed ? "w-16" : "w-60"
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center gap-3 border-b border-border px-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-md gradient-primary shrink-0">
            <Shield className="h-5 w-5 text-primary-foreground" />
          </div>
          {(!collapsed || isMobile) && (
            <div className="flex flex-col min-w-0">
              <span className="text-sm font-bold text-foreground tracking-tight">
                FinSec<span className="text-gradient-primary">Guardian</span>
              </span>
              <span className="text-[10px] font-mono text-muted-foreground">v1.0.0</span>
            </div>
          )}
          {isMobile && (
            <button
              className="ml-auto p-1 rounded-md text-muted-foreground hover:text-foreground transition-colors"
              onClick={() => setMobileOpen(false)}
              aria-label="Close menu"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-1 overflow-y-auto p-3">
          {navItems.map((item) => {
            const isActive = location.pathname === item.to;
            const isIconOnly = collapsed && !isMobile;
            const link = (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-all",
                  isActive
                    ? "bg-primary/10 text-primary glow-primary"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                )}
              >
                <item.icon className={cn("h-4 w-4 shrink-0", isActive && "text-primary")} />
                {!isIconOnly && <span>{item.label}</span>}
              </Link>
            );
            if (isIconOnly) {
              return (
                <Tooltip key={item.to} delayDuration={0}>
                  <TooltipTrigger asChild>{link}</TooltipTrigger>
                  <TooltipContent side="right">{item.label}</TooltipContent>
                </Tooltip>
              );
            }
            return link;
          })}
        </nav>

        {/* Footer: logout + collapse */}
        <div className="border-t border-border p-3 space-y-1">
          {collapsed && !isMobile ? (
            <Tooltip delayDuration={0}>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={authApi.logout}
                  className="w-full justify-center text-muted-foreground hover:text-destructive"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">Sign out</TooltipContent>
            </Tooltip>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              onClick={authApi.logout}
              className="w-full justify-start gap-2 text-muted-foreground hover:text-destructive"
            >
              <LogOut className="h-4 w-4" />
              <span className="font-mono text-xs">Sign out</span>
            </Button>
          )}
          {!isMobile && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCollapsed(!collapsed)}
              className="w-full justify-center text-muted-foreground hover:text-foreground"
            >
              {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
            </Button>
          )}
          {/* Theme toggle */}
          {collapsed && !isMobile ? (
            <Tooltip delayDuration={0}>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleTheme}
                  className="w-full justify-center text-muted-foreground hover:text-foreground"
                  aria-label="Toggle theme"
                >
                  {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">{theme === 'dark' ? 'Light mode' : 'Dark mode'}</TooltipContent>
            </Tooltip>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleTheme}
              className="w-full justify-start gap-2 text-muted-foreground hover:text-foreground"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              {!collapsed && <span className="font-mono text-xs">{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>}
            </Button>
          )}
        </div>
      </aside>

      <main
        className={cn(
          "flex-1 min-w-0 transition-all duration-300 bg-muted/40",
          isMobile ? "ml-0" : collapsed ? "ml-16" : "ml-60"
        )}
      >
        {/* Mobile top bar */}
        {isMobile && (
          <div className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-border bg-sidebar/95 backdrop-blur px-4">
            <button
              onClick={() => setMobileOpen(true)}
              className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-sidebar-accent transition-colors"
              aria-label="Open navigation"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="flex h-7 w-7 items-center justify-center rounded-md gradient-primary">
              <Shield className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="text-sm font-bold text-foreground tracking-tight">
              FinSec<span className="text-gradient-primary">Guardian</span>
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleTheme}
              className="ml-auto p-1.5 text-muted-foreground hover:text-foreground"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
          </div>
        )}
        <div className="p-4 md:p-6">{children}</div>
      </main>
    </div>
  );
};

export default AppLayout;