import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader, EmptyState } from "@/components/bits";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const ROLE_COLOR = {
  system: "text-indigo-600", admin: "text-red-600", manager: "text-amber-600",
  analyst: "text-emerald-600", executive: "text-sky-600",
};

export default function Audit() {
  const [logs, setLogs] = useState(null);
  const [q, setQ] = useState("");
  const [role, setRole] = useState("all");

  useEffect(() => {
    const t = setTimeout(() => {
      api.get("/audit", { params: { q, role: role === "all" ? "" : role } }).then((r) => setLogs(r.data));
    }, 250);
    return () => clearTimeout(t);
  }, [q, role]);

  return (
    <div data-testid="audit-page">
      <PageHeader kicker="Governance" title="Audit trail"
        subtitle="Immutable log of every agent action, approval, and export. Who, what, when — always answerable." />

      <div className="flex flex-wrap gap-3 mb-6">
        <Input placeholder="Search details…" value={q} onChange={(e) => setQ(e.target.value)} className="max-w-xs text-sm" data-testid="audit-search-input" />
        <Select value={role} onValueChange={setRole}>
          <SelectTrigger className="w-40 text-sm" data-testid="audit-role-filter"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All actors</SelectItem>
            {["system", "admin", "manager", "analyst", "executive"].map((r) => (
              <SelectItem key={r} value={r} className="capitalize">{r}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {logs && logs.length === 0 ? (
        <EmptyState title="No matching entries" subtitle="Adjust the search or actor filter to widen the window." />
      ) : (
        <div className="rounded-2xl border border-border bg-card card-soft overflow-hidden mono text-xs" data-testid="audit-log-list">
          {(logs || []).map((l) => (
            <div key={l.id} className="grid grid-cols-12 gap-3 px-5 py-3 border-b border-border/50 last:border-0 hover:bg-secondary/40 transition-colors duration-100 items-baseline">
              <span className="col-span-3 md:col-span-2 text-muted-foreground text-[11px]">
                {new Date(l.timestamp).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}
              </span>
              <span className={`col-span-3 md:col-span-2 text-[11px] uppercase tracking-wide truncate ${ROLE_COLOR[l.actor_role] || "text-muted-foreground"}`}>
                {l.actor}
              </span>
              <span className="col-span-6 md:col-span-3 text-[11px] text-foreground/80 truncate">{l.action}</span>
              <span className="col-span-12 md:col-span-5 text-[11px] text-muted-foreground leading-relaxed">{l.details}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
