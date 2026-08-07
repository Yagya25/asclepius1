import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator } from "@/components/ui/command";
import { LayoutDashboard, Upload, Sparkles, Inbox, FileText, ScrollText, RotateCcw, LogOut, Search } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

const NAV = [
  { label: "Dashboard", icon: LayoutDashboard, to: "/app/dashboard" },
  { label: "Upload Data", icon: Upload, to: "/app/upload" },
  { label: "Insights", icon: Sparkles, to: "/app/insights" },
  { label: "Approvals", icon: Inbox, to: "/app/approvals" },
  { label: "Reports", icon: FileText, to: "/app/reports" },
  { label: "Audit Trail", icon: ScrollText, to: "/app/audit" },
];

const TYPE_ROUTE = { recommendation: "/app/approvals", upload: "/app/upload", anomaly: "/app/insights?tab=anomalies", report: "/app/reports" };

export function CommandPalette({ open, setOpen }) {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);

  useEffect(() => {
    if (!query || query.length < 2) { setResults([]); return; }
    const t = setTimeout(() => {
      api.get("/search", { params: { q: query } }).then((r) => setResults(r.data.results)).catch(() => {});
    }, 200);
    return () => clearTimeout(t);
  }, [query]);

  const run = (fn) => { setOpen(false); fn(); };

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Search or jump to…" value={query} onValueChange={setQuery} data-testid="command-palette-input" />
      <CommandList data-testid="command-palette-list">
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Navigate">
          {NAV.map((n) => (
            <CommandItem key={n.to} onSelect={() => run(() => navigate(n.to))} data-testid={`palette-nav-${n.label.toLowerCase().replace(/ /g, "-")}`}>
              <n.icon className="mr-2 h-4 w-4 text-muted-foreground" /> {n.label}
            </CommandItem>
          ))}
        </CommandGroup>
        {results.length > 0 && (
          <>
            <CommandSeparator />
            <CommandGroup heading="Records">
              {results.map((r) => (
                <CommandItem key={r.id} value={`${r.label} ${r.id}`} onSelect={() => run(() => navigate(TYPE_ROUTE[r.type] || "/app/dashboard"))}>
                  <Search className="mr-2 h-4 w-4 text-muted-foreground" />
                  <span className="truncate">{r.label}</span>
                  <span className="ml-auto mono text-[10px] uppercase text-muted-foreground">{r.type}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          </>
        )}
        <CommandSeparator />
        <CommandGroup heading="Actions">
          <CommandItem onSelect={() => run(async () => { await api.post("/demo/reset"); toast.success("Demo data restored"); window.location.reload(); })} data-testid="palette-reset-demo">
            <RotateCcw className="mr-2 h-4 w-4 text-muted-foreground" /> Reset Demo Data
          </CommandItem>
          <CommandItem onSelect={() => run(() => logout().then(() => navigate("/login")))} data-testid="palette-logout">
            <LogOut className="mr-2 h-4 w-4 text-muted-foreground" /> Log out
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
