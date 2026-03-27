import { Shield, Lock, Key, Bell, Database } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";

const SettingsPage = () => {
  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          <span className="text-gradient-primary">Settings</span>
        </h1>
        <p className="text-sm text-muted-foreground font-mono mt-1">
          Security configuration and preferences
        </p>
      </div>

      {/* Security Settings */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
            <Lock className="h-4 w-4" /> Authentication
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Multi-Factor Authentication</Label>
              <p className="text-xs text-muted-foreground">Require TOTP for all logins</p>
            </div>
            <Switch defaultChecked />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Session Timeout</Label>
              <p className="text-xs text-muted-foreground">Auto-logout after inactivity</p>
            </div>
            <Input defaultValue="30" className="w-20 font-mono text-sm bg-secondary/30" />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">IP Whitelisting</Label>
              <p className="text-xs text-muted-foreground">Restrict access to approved IPs</p>
            </div>
            <Switch />
          </div>
        </CardContent>
      </Card>

      {/* Scanner Settings */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
            <Shield className="h-4 w-4" /> Scanner Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Auto-scan on Upload</Label>
              <p className="text-xs text-muted-foreground">Automatically scan uploaded contracts</p>
            </div>
            <Switch defaultChecked />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Include Gas Optimizations</Label>
              <p className="text-xs text-muted-foreground">Flag gas inefficiency patterns</p>
            </div>
            <Switch defaultChecked />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Severity Threshold</Label>
              <p className="text-xs text-muted-foreground">Minimum severity to report</p>
            </div>
            <Input defaultValue="low" className="w-24 font-mono text-sm bg-secondary/30" />
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-sm font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
            <Bell className="h-4 w-4" /> Alerts & Notifications
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Critical Vulnerability Alerts</Label>
              <p className="text-xs text-muted-foreground">Notify on critical findings</p>
            </div>
            <Switch defaultChecked />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Failed Login Alerts</Label>
              <p className="text-xs text-muted-foreground">Notify on suspicious login attempts</p>
            </div>
            <Switch defaultChecked />
          </div>
        </CardContent>
      </Card>

      <Button className="gradient-primary text-primary-foreground font-mono font-semibold">
        Save Settings
      </Button>
    </div>
  );
};

export default SettingsPage;
