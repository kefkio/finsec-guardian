import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Shield } from "lucide-react";
import { authApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

const Login = () => {
  const navigate = useNavigate();
  const [tab, setTab] = useState("login"); // "login" | "register"
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ username: "", email: "", password: "" });

  const handleChange = (e) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authApi.login(form.username, form.password);
      navigate("/", { replace: true });
    } catch (err) {
      toast.error(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authApi.register(form.username, form.email, form.password);
      toast.success("Account created — please log in.");
      setTab("login");
      setForm((prev) => ({ ...prev, password: "" }));
    } catch (err) {
      toast.error(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <div className="w-full max-w-sm space-y-6">
        {/* Branding */}
        <div className="flex flex-col items-center gap-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl gradient-primary">
            <Shield className="h-7 w-7 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">
            DeFi<span className="text-gradient-primary">Guard</span>
          </h1>
          <p className="text-sm text-muted-foreground font-mono">
            Smart contract security platform
          </p>
        </div>

        <Card className="border-border bg-card">
          <CardHeader className="pb-3">
            {/* Tab switcher */}
            <div className="flex gap-1 rounded-md bg-muted p-1 font-mono text-xs">
              {["login", "register"].map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`flex-1 rounded py-1.5 font-semibold capitalize transition-colors ${
                    tab === t
                      ? "bg-background text-foreground shadow"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
            <CardTitle className="sr-only">
              {tab === "login" ? "Sign in" : "Create account"}
            </CardTitle>
            <CardDescription className="text-xs text-muted-foreground pt-1">
              {tab === "login"
                ? "Sign in with your credentials to continue."
                : "Create a new account to get started."}
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form
              onSubmit={tab === "login" ? handleLogin : handleRegister}
              className="space-y-4"
            >
              <div className="space-y-1.5">
                <Label htmlFor="username" className="font-mono text-xs">
                  Username
                </Label>
                <Input
                  id="username"
                  name="username"
                  autoComplete="username"
                  required
                  value={form.username}
                  onChange={handleChange}
                  className="font-mono text-sm"
                  placeholder="your_username"
                />
              </div>

              {tab === "register" && (
                <div className="space-y-1.5">
                  <Label htmlFor="email" className="font-mono text-xs">
                    Email
                  </Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={form.email}
                    onChange={handleChange}
                    className="font-mono text-sm"
                    placeholder="you@example.com"
                  />
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="password" className="font-mono text-xs">
                  Password
                </Label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete={tab === "login" ? "current-password" : "new-password"}
                  required
                  value={form.password}
                  onChange={handleChange}
                  className="font-mono text-sm"
                  placeholder="••••••••"
                />
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full gradient-primary text-primary-foreground font-mono font-semibold"
              >
                {loading
                  ? tab === "login"
                    ? "Signing in…"
                    : "Creating account…"
                  : tab === "login"
                  ? "Sign in"
                  : "Create account"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Login;
