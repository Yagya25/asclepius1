import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { LayoutDashboard, Upload, Sparkles, Inbox, FileText, ScrollText, Command, Bell, LogOut, PanelLeftClose, PanelLeft, RotateCcw, Users, ClipboardCheck } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { CommandPalette } from "@/components/CommandPalette";
import { AICopilot } from "@/components/AICopilot";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { toast } from "sonner";

const NAV = [
  { label: "Dashboard", icon: LayoutDashboard, to: "/app/dashboard", roles: ["admin", "manager", "analyst", "executive", "hr_manager"] },
  { label: "Upload", icon: Upload, to: "/app/upload", roles: ["admin", "analyst"] },
  { label: "Insights", icon: Sparkles, to: "/app/insights", roles: ["admin", "analyst", "manager"] },
  { label: "HR Screening", icon: Users, to: "/app/hr-screening", roles: ["admin", "hr_manager"] },
  { label: "Onboarding", icon: ClipboardCheck, to: "/app/hr-onboarding", roles: ["admin", "hr_manager"] },
  { label: "Approvals", icon: Inbox, to: "/app/approvals", roles: ["admin", "manager", "executive", "hr_manager"] },
  { label: "Reports", icon: FileText, to: "/app/reports", roles: ["admin", "executive"] },
  { label: "Audit", icon: ScrollText, to: "/app/audit", roles: ["admin", "manager", "analyst", "hr_manager"] },
];

const LEVEL_DOT = { critical: "bg-red-400", warning: "bg-amber-400", info: "bg-indigo-400" };

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [notifs, setNotifs] = useState([]);

  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  useEffect(() => {
    api.get("/notifications").then((r) => setNotifs(r.data)).catch(() => {});
  }, []);

  const unread = notifs.filter((n) => !n.read).length;

  const resetDemo = async () => {
    await api.post("/demo/reset");
    toast.success("Demo data restored to seeded state");
    setTimeout(() => window.location.reload(), 600);
  };

  return (
    <div className="min-h-screen bg-background">
      <CommandPalette open={paletteOpen} setOpen={setPaletteOpen} />
      {/* Floating sidebar */}
      <aside className={`fixed left-4 top-4 bottom-4 z-40 flex flex-col rounded-2xl border border-border bg-card card-soft transition-[width] duration-300 ${collapsed ? "w-[64px]" : "w-[224px]"}`} data-testid="app-sidebar">
        <div className={`flex items-center gap-2.5 px-4 pt-5 pb-6 ${collapsed ? "justify-center px-0" : ""}`}>
          <div className="h-8 w-8 shrink-0 rounded-full flex items-center justify-center shadow-sm overflow-hidden ring-1 ring-border/50">
            <img src="/logo.jpg" alt="Asclepius Logo" className="h-full w-full object-cover" />
          </div>
          {!collapsed && <span className="font-medium tracking-tight text-[15px]">Asclepius</span>}
        </div>
        <nav className="flex-1 px-2.5 space-y-1">
          {NAV.filter((n) => !n.roles || n.roles.includes(user.role)).map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              data-testid={`nav-${n.label.toLowerCase()}`}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors ${collapsed ? "justify-center px-0" : ""} ${
                  isActive ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground hover:bg-accent"}`}
            >
              <n.icon className="h-[18px] w-[18px] shrink-0" />
              {!collapsed && n.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-2.5 pb-4 space-y-1">
          <button onClick={() => setPaletteOpen(true)} data-testid="sidebar-command-btn"
            className={`w-full flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] text-muted-foreground hover:text-foreground hover:bg-accent transition-colors ${collapsed ? "justify-center px-0" : ""}`}>
            <Command className="h-[18px] w-[18px] shrink-0" />
            {!collapsed && <span className="flex-1 text-left">Command</span>}
            {!collapsed && <kbd className="mono text-[10px] px-1.5 py-0.5 rounded bg-secondary border border-border">⌘K</kbd>}
          </button>
          <button onClick={() => setCollapsed(!collapsed)} data-testid="sidebar-collapse-btn"
            className={`w-full flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] text-muted-foreground hover:text-foreground hover:bg-accent transition-colors ${collapsed ? "justify-center px-0" : ""}`}>
            {collapsed ? <PanelLeft className="h-[18px] w-[18px]" /> : <PanelLeftClose className="h-[18px] w-[18px] shrink-0" />}
            {!collapsed && "Collapse"}
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className={`transition-[padding] duration-300 ${collapsed ? "pl-[96px]" : "pl-[256px]"} pr-6`}>
        <header className="sticky top-0 z-30 flex items-center justify-end gap-2 py-4 bg-background/80 backdrop-blur-md">
          <Button variant="ghost" size="sm" onClick={resetDemo} className="text-muted-foreground text-xs gap-1.5" data-testid="reset-demo-btn">
            <RotateCcw className="h-3.5 w-3.5" /> Reset Demo
          </Button>
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="ghost" size="icon" className="relative" data-testid="notifications-btn">
                <Bell className="h-4 w-4" />
                {unread > 0 && <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-indigo-500 pulse-ring" />}
              </Button>
            </PopoverTrigger>
            <PopoverContent align="end" className="w-96 p-0 border-border card-soft" data-testid="notifications-panel">
              <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                <p className="text-sm font-semibold">Notifications</p>
                <button className="text-xs text-indigo-600 hover:underline" data-testid="notifications-read-all"
                  onClick={() => api.post("/notifications/read-all").then(() => setNotifs(notifs.map((n) => ({ ...n, read: true }))))}>
                  Mark all read
                </button>
              </div>
              <div className="max-h-80 overflow-auto">
                {notifs.map((n) => (
                  <div key={n.id} className="flex gap-3 px-4 py-3 border-b border-border/50 last:border-0 hover:bg-accent/50">
                    <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${LEVEL_DOT[n.level] || "bg-zinc-400"} ${n.read ? "opacity-30" : ""}`} />
                    <div>
                      <p className="text-[13px] font-medium">{n.title}</p>
                      <p className="text-xs text-muted-foreground">{n.body}</p>
                    </div>
                  </div>
                ))}
              </div>
            </PopoverContent>
          </Popover>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="flex items-center gap-2.5 rounded-full border border-border bg-card pl-1 pr-3 py-1 hover:bg-accent transition-colors" data-testid="user-menu-btn">
                <div className="h-7 w-7 rounded-full bg-secondary border border-border flex items-center justify-center">
                  <span className="text-xs font-medium">{user.name?.[0]}</span>
                </div>
                <div className="text-left">
                  <p className="text-xs font-medium leading-none">{user.name}</p>
                  <p className="mono text-[10px] uppercase text-muted-foreground mt-0.5">{user.role}</p>
                </div>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 card-soft">
              <DropdownMenuLabel className="text-xs text-muted-foreground">{user.email}</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => logout().then(() => navigate("/login"))} data-testid="logout-btn">
                <LogOut className="mr-2 h-4 w-4" /> Log out
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => logout(true).then(() => navigate("/login"))} data-testid="logout-all-btn">
                <LogOut className="mr-2 h-4 w-4" /> Log out all devices
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>
        <main className="relative z-10 pb-16 pt-2">
          <Outlet />
        </main>
      </div>
      <AICopilot />
    </div>
  );
}
