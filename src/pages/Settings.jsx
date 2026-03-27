import { Shield, Lock, Bell } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
const SettingsPage = () => {
  return /*#__PURE__*/_jsxs("div", {
    className: "space-y-6 max-w-2xl",
    children: [/*#__PURE__*/_jsxs("div", {
      children: [/*#__PURE__*/_jsx("h1", {
        className: "text-2xl font-bold tracking-tight",
        children: /*#__PURE__*/_jsx("span", {
          className: "text-gradient-primary",
          children: "Settings"
        })
      }), /*#__PURE__*/_jsx("p", {
        className: "text-sm text-muted-foreground font-mono mt-1",
        children: "Security configuration and preferences"
      })]
    }), /*#__PURE__*/_jsxs(Card, {
      className: "border-border bg-card",
      children: [/*#__PURE__*/_jsx(CardHeader, {
        children: /*#__PURE__*/_jsxs(CardTitle, {
          className: "text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2",
          children: [/*#__PURE__*/_jsx(Lock, {
            className: "h-4 w-4"
          }), " Authentication"]
        })
      }), /*#__PURE__*/_jsxs(CardContent, {
        className: "space-y-4",
        children: [/*#__PURE__*/_jsxs("div", {
          className: "flex items-center justify-between",
          children: [/*#__PURE__*/_jsxs("div", {
            children: [/*#__PURE__*/_jsx(Label, {
              className: "text-sm font-medium",
              children: "Multi-Factor Authentication"
            }), /*#__PURE__*/_jsx("p", {
              className: "text-xs text-muted-foreground",
              children: "Require TOTP for all logins"
            })]
          }), /*#__PURE__*/_jsx(Switch, {
            defaultChecked: true
          })]
        }), /*#__PURE__*/_jsx(Separator, {}), /*#__PURE__*/_jsxs("div", {
          className: "flex items-center justify-between",
          children: [/*#__PURE__*/_jsxs("div", {
            children: [/*#__PURE__*/_jsx(Label, {
              className: "text-sm font-medium",
              children: "Session Timeout"
            }), /*#__PURE__*/_jsx("p", {
              className: "text-xs text-muted-foreground",
              children: "Auto-logout after inactivity"
            })]
          }), /*#__PURE__*/_jsx(Input, {
            defaultValue: "30",
            className: "w-20 font-mono text-sm bg-secondary/30"
          })]
        }), /*#__PURE__*/_jsx(Separator, {}), /*#__PURE__*/_jsxs("div", {
          className: "flex items-center justify-between",
          children: [/*#__PURE__*/_jsxs("div", {
            children: [/*#__PURE__*/_jsx(Label, {
              className: "text-sm font-medium",
              children: "IP Whitelisting"
            }), /*#__PURE__*/_jsx("p", {
              className: "text-xs text-muted-foreground",
              children: "Restrict access to approved IPs"
            })]
          }), /*#__PURE__*/_jsx(Switch, {})]
        })]
      })]
    }), /*#__PURE__*/_jsxs(Card, {
      className: "border-border bg-card",
      children: [/*#__PURE__*/_jsx(CardHeader, {
        children: /*#__PURE__*/_jsxs(CardTitle, {
          className: "text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2",
          children: [/*#__PURE__*/_jsx(Shield, {
            className: "h-4 w-4"
          }), " Scanner Configuration"]
        })
      }), /*#__PURE__*/_jsxs(CardContent, {
        className: "space-y-4",
        children: [/*#__PURE__*/_jsxs("div", {
          className: "flex items-center justify-between",
          children: [/*#__PURE__*/_jsxs("div", {
            children: [/*#__PURE__*/_jsx(Label, {
              className: "text-sm font-medium",
              children: "Auto-scan on Upload"
            }), /*#__PURE__*/_jsx("p", {
              className: "text-xs text-muted-foreground",
              children: "Automatically scan uploaded contracts"
            })]
          }), /*#__PURE__*/_jsx(Switch, {
            defaultChecked: true
          })]
        }), /*#__PURE__*/_jsx(Separator, {}), /*#__PURE__*/_jsxs("div", {
          className: "flex items-center justify-between",
          children: [/*#__PURE__*/_jsxs("div", {
            children: [/*#__PURE__*/_jsx(Label, {
              className: "text-sm font-medium",
              children: "Include Gas Optimizations"
            }), /*#__PURE__*/_jsx("p", {
              className: "text-xs text-muted-foreground",
              children: "Flag gas inefficiency patterns"
            })]
          }), /*#__PURE__*/_jsx(Switch, {
            defaultChecked: true
          })]
        }), /*#__PURE__*/_jsx(Separator, {}), /*#__PURE__*/_jsxs("div", {
          className: "flex items-center justify-between",
          children: [/*#__PURE__*/_jsxs("div", {
            children: [/*#__PURE__*/_jsx(Label, {
              className: "text-sm font-medium",
              children: "Severity Threshold"
            }), /*#__PURE__*/_jsx("p", {
              className: "text-xs text-muted-foreground",
              children: "Minimum severity to report"
            })]
          }), /*#__PURE__*/_jsx(Input, {
            defaultValue: "low",
            className: "w-24 font-mono text-sm bg-secondary/30"
          })]
        })]
      })]
    }), /*#__PURE__*/_jsxs(Card, {
      className: "border-border bg-card",
      children: [/*#__PURE__*/_jsx(CardHeader, {
        children: /*#__PURE__*/_jsxs(CardTitle, {
          className: "text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2",
          children: [/*#__PURE__*/_jsx(Bell, {
            className: "h-4 w-4"
          }), " Alerts & Notifications"]
        })
      }), /*#__PURE__*/_jsxs(CardContent, {
        className: "space-y-4",
        children: [/*#__PURE__*/_jsxs("div", {
          className: "flex items-center justify-between",
          children: [/*#__PURE__*/_jsxs("div", {
            children: [/*#__PURE__*/_jsx(Label, {
              className: "text-sm font-medium",
              children: "Critical Vulnerability Alerts"
            }), /*#__PURE__*/_jsx("p", {
              className: "text-xs text-muted-foreground",
              children: "Notify on critical findings"
            })]
          }), /*#__PURE__*/_jsx(Switch, {
            defaultChecked: true
          })]
        }), /*#__PURE__*/_jsx(Separator, {}), /*#__PURE__*/_jsxs("div", {
          className: "flex items-center justify-between",
          children: [/*#__PURE__*/_jsxs("div", {
            children: [/*#__PURE__*/_jsx(Label, {
              className: "text-sm font-medium",
              children: "Failed Login Alerts"
            }), /*#__PURE__*/_jsx("p", {
              className: "text-xs text-muted-foreground",
              children: "Notify on suspicious login attempts"
            })]
          }), /*#__PURE__*/_jsx(Switch, {
            defaultChecked: true
          })]
        })]
      })]
    }), /*#__PURE__*/_jsx(Button, {
      className: "gradient-primary text-primary-foreground font-mono font-semibold",
      children: "Save Settings"
    })]
  });
};
export default SettingsPage;