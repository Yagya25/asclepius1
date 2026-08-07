import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { formatApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";

const DEMO_ACCOUNTS = [
  { role: "Admin", email: "admin@asclepius.com", desc: "Full access" },
  { role: "Manager", email: "manager@asclepius.com", desc: "Approvals & reports" },
  { role: "Analyst", email: "analyst@asclepius.com", desc: "Uploads & pipeline" },
  { role: "Executive", email: "executive@asclepius.com", desc: "Read-only + approve" },
  { role: "HR", email: "hr@asclepius.com", desc: "HR screening & onboarding" },
];

export default function Login() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState("analyst");
  const [remember, setRemember] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      let u;
      if (mode === "login") u = await login(email, password, remember);
      else u = await register(name, email, password, role);
      toast.success("Welcome to Asclepius");
      
      if (u?.role === "hr_manager") {
        localStorage.setItem("apbi_journey_done", "1");
        navigate("/app/hr-screening");
      } else {
        localStorage.removeItem("apbi_journey_done");
        navigate("/app/journey");
      }
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setBusy(false);
    }
  };

  const quickFill = (em) => { setEmail(em); setPassword("Demo@123"); setMode("login"); };

  return (
    <div className="min-h-screen bg-[#09090b] text-[#fafafa] grid lg:grid-cols-[1fr_480px]">
      {/* Left panel */}
      <div className="relative hidden lg:flex flex-col justify-between p-16 border-r border-white/[0.08]">
        <Link to="/" className="flex items-center gap-3 w-fit" data-testid="login-home-link">
          <div className="h-8 w-8 rounded-lg flex items-center justify-center overflow-hidden ring-1 ring-white/20">
            <img src="/logo.jpg" alt="Asclepius Logo" className="h-full w-full object-cover" />
          </div>
          <span className="font-semibold tracking-tight text-sm text-white">Asclepius</span>
        </Link>
        <div className="max-w-md">
          <h2 className="text-3xl font-bold tracking-tight leading-snug text-white">Six agents. One approval inbox. Zero black boxes.</h2>
          <p className="mt-5 text-sm text-zinc-400 leading-relaxed font-normal">
            Sign in with a demo role to explore seeded pharmaceutical distribution data — forecasts, anomalies, recommendations, and audit trails included.
          </p>
        </div>
        <p className="mono text-[11px] text-zinc-500">All demo accounts · password Demo@123</p>
      </div>

      {/* Right form */}
      <div className="flex items-center justify-center p-8 bg-[#09090b]">
        <div className="w-full max-w-sm">
          <h1 className="text-2xl font-bold tracking-tight text-white">{mode === "login" ? "Sign in" : "Create account"}</h1>
          <p className="mt-1 text-sm text-zinc-400">{mode === "login" ? "Use a demo account or your credentials." : "Register a new workspace user."}</p>

          <form onSubmit={submit} className="mt-7 space-y-4">
            {mode === "register" && (
              <div className="space-y-1.5">
                <Label htmlFor="name" className="text-xs font-mono text-zinc-300">Full name</Label>
                <Input id="name" value={name} onChange={(e) => setName(e.target.value)} required data-testid="register-name-input" className="linear-input h-10 text-sm text-white" />
              </div>
            )}
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-xs font-mono text-zinc-300">Email</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required data-testid="login-email-input" className="linear-input h-10 text-sm text-white" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-xs font-mono text-zinc-300">Password</Label>
              <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required data-testid="login-password-input" className="linear-input h-10 text-sm text-white" />
            </div>
            {mode === "register" && (
              <div className="space-y-1.5">
                <Label className="text-xs font-mono text-zinc-300">Role</Label>
                <Select value={role} onValueChange={setRole}>
                  <SelectTrigger data-testid="register-role-select" className="linear-input h-10 text-sm text-white"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-white/10 text-white">
                    {["analyst", "manager", "executive", "admin"].map((r) => (
                      <SelectItem key={r} value={r} className="capitalize focus:bg-zinc-800">{r}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            {mode === "login" && (
              <div className="flex items-center gap-2.5 pt-1">
                <Checkbox id="remember" checked={remember} onCheckedChange={setRemember} data-testid="remember-me-checkbox" className="border-white/20 data-[state=checked]:bg-white data-[state=checked]:text-black" />
                <Label htmlFor="remember" className="text-xs text-zinc-400 font-normal">Remember me for 30 days</Label>
              </div>
            )}
            {error && <p className="text-xs text-red-400 font-mono" data-testid="login-error">{error}</p>}
            <Button type="submit" className="w-full h-11 bg-white text-black hover:bg-zinc-200 font-semibold tracking-tight shadow-md transition-all" disabled={busy} data-testid="login-submit-btn">
              {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
            </Button>
          </form>

          <button onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
            className="mt-4 text-xs text-zinc-400 hover:text-white transition-colors duration-150" data-testid="toggle-auth-mode">
            {mode === "login" ? "Need an account? Register" : "Have an account? Sign in"}
          </button>

          {mode === "login" && (
            <div className="mt-8 pt-6 border-t border-white/[0.08]">
              <p className="mono text-[10px] uppercase tracking-[0.2em] text-zinc-500 mb-3">Demo accounts · password Demo@123</p>
              <div className="grid grid-cols-2 gap-2">
                {DEMO_ACCOUNTS.map((a) => (
                  <button key={a.email} onClick={() => quickFill(a.email)} data-testid={`demo-account-${a.role.toLowerCase()}`}
                    className="linear-card rounded-xl p-3 text-left hover:border-white/20 transition-all">
                    <p className="text-xs font-semibold text-white">{a.role}</p>
                    <p className="text-[10px] text-zinc-400 mt-0.5">{a.desc}</p>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
