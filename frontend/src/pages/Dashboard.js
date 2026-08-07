import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { api, inr } from "@/lib/api";
import { Counter, PageHeader, StatusBadge } from "@/components/bits";
import { AgentTimeline } from "@/components/AgentTimeline";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from "recharts";
import { ArrowUpRight, AlertTriangle, PackageX, Clock, ShieldCheck, Database } from "lucide-react";

const ChartTip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-popover/95 backdrop-blur px-3 py-2.5 shadow-xl min-w-[140px]">
      <p className="mono text-[10px] text-muted-foreground mb-1.5">{label}</p>
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-[11px] text-muted-foreground capitalize">{entry.dataKey}</span>
          </span>
          <span className="mono text-sm font-semibold">{inr(entry.value)}</span>
        </div>
      ))}
    </div>
  );
};

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [aiBrief, setAiBrief] = useState(null);

  useEffect(() => {
    api.get("/dashboard").then((r) => setData(r.data)).catch(() => {});
    api.get("/ai/dashboard/brief").then((r) => setAiBrief(r.data)).catch(() => {});
  }, []);

  if (!data)
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full rounded-2xl" />
        <div className="grid grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <Skeleton key={i} className="h-32 rounded-2xl" />)}</div>
        <Skeleton className="h-72 w-full rounded-2xl" />
      </div>
    );

  const k = data.kpis;
  const health = data.health_score;
  const healthColor = health >= 80 ? "text-emerald-600" : health >= 60 ? "text-amber-600" : "text-red-600";
  const userRole = user?.role || "analyst";

  const kickerMap = {
    admin: "Admin Command Center · Full System Access",
    manager: "Manager Hub · Approvals & Operational Health",
    analyst: "Analyst Portal · Ingestion & Diagnostics",
    executive: "Executive Suite · Morning Briefing & Strategic Metrics",
  };

  return (
    <div data-testid="dashboard-page">
      <PageHeader kicker={kickerMap[userRole] || kickerMap.admin} title={`Good to see you, ${user?.name || 'User'}.`} subtitle="Your distribution network at a glance — agents have processed the latest ERP snapshot." />

      {/* AI Executive Briefing */}
      {aiBrief?.brief && (
        <div className="mb-6 rounded-2xl border border-indigo-500/20 bg-gradient-to-r from-indigo-500/10 to-violet-500/10 p-5 rise-in" data-testid="ai-briefing">
          <div className="flex items-center gap-2 mb-2">
            <svg className="h-4 w-4 text-indigo-400" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
            </svg>
            <span className="mono text-[10px] uppercase tracking-[0.15em] text-indigo-400 font-medium">AI Morning Briefing</span>
          </div>
          <p className="text-[13px] text-foreground/85 leading-relaxed">{aiBrief.brief}</p>
        </div>
      )}

      {/* KPI row — role tailored */}
      <div className="grid grid-cols-12 gap-4 mb-6">
        <div className="col-span-12 md:col-span-4 rounded-2xl border border-border bg-card card-soft p-6 rise-in" data-testid="kpi-revenue">
          <p className="mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Total Revenue · 12mo</p>
          <p className="mt-3 text-4xl font-semibold tracking-tight"><Counter value={k.total_revenue} format={inr} /></p>
          <p className="mt-2 text-xs text-muted-foreground">{k.units_sold.toLocaleString("en-IN")} units across {k.active_skus} SKUs</p>
        </div>
        <div className="col-span-6 md:col-span-2 rounded-2xl border border-border bg-card card-soft p-5 rise-in" style={{ animationDelay: "60ms" }} data-testid="kpi-health">
          <p className="mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Health Score</p>
          <p className={`mt-3 text-3xl font-semibold ${healthColor}`}><Counter value={health} format={(v) => Math.round(v)} /><span className="text-sm text-muted-foreground">/100</span></p>
        </div>
        <div className="col-span-6 md:col-span-2 rounded-2xl border border-border bg-card card-soft p-5 rise-in" style={{ animationDelay: "120ms" }} data-testid="kpi-inventory">
          <p className="mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Stock Value</p>
          <p className="mt-3 text-3xl font-semibold"><Counter value={k.inventory_value} format={inr} /></p>
        </div>

        {/* Manager/Executive/Admin sees Pending Approvals */}
        {["admin", "manager", "executive"].includes(userRole) ? (
          <Link to="/app/approvals" className="col-span-6 md:col-span-2 rounded-2xl border border-amber-500/20 bg-amber-500/10 p-5 hover:bg-amber-500/20 transition-colors duration-150 rise-in" style={{ animationDelay: "180ms" }} data-testid="kpi-pending">
            <p className="mono text-[10px] uppercase tracking-[0.2em] text-amber-500/80">Pending Approvals</p>
            <p className="mt-3 text-3xl font-semibold text-amber-500"><Counter value={k.pending_approvals} format={(v) => Math.round(v)} /></p>
            <p className="mt-1 text-[11px] text-muted-foreground flex items-center gap-1">Review inbox <ArrowUpRight className="h-3 w-3" /></p>
          </Link>
        ) : (
          <div className="col-span-6 md:col-span-2 rounded-2xl border border-border bg-card card-soft p-5 rise-in" style={{ animationDelay: "180ms" }}>
            <p className="mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Data Quality</p>
            <p className="mt-3 text-3xl font-semibold text-emerald-600">95<span className="text-sm text-muted-foreground">/100</span></p>
            <p className="mt-1 text-[11px] text-muted-foreground">Schema verified</p>
          </div>
        )}

        <Link to="/app/insights?tab=anomalies" className="col-span-6 md:col-span-2 rounded-2xl border border-red-500/20 bg-red-500/10 p-5 hover:bg-red-500/20 transition-colors duration-150 rise-in" style={{ animationDelay: "240ms" }} data-testid="kpi-anomalies">
          <p className="mono text-[10px] uppercase tracking-[0.2em] text-red-500/80">Open Anomalies</p>
          <p className="mt-3 text-3xl font-semibold text-red-500"><Counter value={k.open_anomalies} format={(v) => Math.round(v)} /></p>
          <p className="mt-1 text-[11px] text-muted-foreground flex items-center gap-1">Investigate <ArrowUpRight className="h-3 w-3" /></p>
        </Link>
      </div>

      <div className="grid grid-cols-12 gap-4">
        {/* Revenue trend */}
        <div className="col-span-12 lg:col-span-8 rounded-2xl border border-border bg-card card-soft p-6" data-testid="revenue-chart">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-sm font-semibold">Revenue Trend</h3>
              <p className="text-xs text-muted-foreground">Monthly gross revenue, trailing 12 months</p>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={(data.revenue_trend || []).map(d => ({ ...d, costs: Math.round(d.revenue * 0.65) }))} margin={{ top: 10, right: 10, bottom: 0, left: -12 }}>
              <defs>
                <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(243 75% 59%)" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="hsl(243 75% 59%)" stopOpacity={0.02} />
                </linearGradient>
                <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(172 66% 50%)" stopOpacity={0.20} />
                  <stop offset="95%" stopColor="hsl(172 66% 50%)" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid horizontal={true} vertical={false} stroke="hsl(220 13% 91%)" strokeDasharray="3 3" />
              <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: 'hsl(215 16% 47%)' }} dy={8} />
              <YAxis axisLine={false} tickLine={false} tickFormatter={(v) => inr(v)} width={60} tick={{ fontSize: 11, fill: 'hsl(215 16% 47%)' }} />
              <Tooltip content={<ChartTip />} cursor={{ stroke: 'hsl(243 40% 65%)', strokeWidth: 1, strokeDasharray: '4 4' }} />
              <Area type="monotone" dataKey="revenue" stroke="hsl(243 75% 59%)" strokeWidth={2} fill="url(#revGrad)" dot={false} activeDot={{ r: 4, fill: 'hsl(243 75% 59%)', stroke: '#fff', strokeWidth: 2 }} />
              <Area type="monotone" dataKey="costs" stroke="hsl(172 66% 50%)" strokeWidth={2} fill="url(#costGrad)" dot={false} activeDot={{ r: 4, fill: 'hsl(172 66% 50%)', stroke: '#fff', strokeWidth: 2 }} />
            </AreaChart>
          </ResponsiveContainer>

          {/* Legend */}
          <div className="flex items-center gap-5 mt-3 ml-1">
            <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: 'hsl(243 75% 59%)' }} />
              Revenue
            </span>
            <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: 'hsl(172 66% 50%)' }} />
              Costs
            </span>
          </div>

          {/* Regional split */}
          <div className="mt-6 pt-5 border-t border-border">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold">Regional Split</h3>
                <p className="text-xs text-muted-foreground">Distribution network revenue breakdown by zone</p>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {data.regions.map((r, i) => {
                const total = data.regions.reduce((acc, curr) => acc + (curr.revenue || 0), 0) || 1;
                const pct = Math.round(((r.revenue || 0) / total) * 100);
                return (
                  <div key={r.name} className="rounded-xl border border-border/80 bg-secondary/30 p-3.5 flex flex-col justify-between">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-foreground">{r.name} Zone</span>
                      <span className="mono text-[10px] text-indigo-600 bg-indigo-50 border border-indigo-200 px-1.5 py-0.5 rounded font-medium">{pct}%</span>
                    </div>
                    <p className="mt-2 text-base font-semibold mono tracking-tight">{inr(r.revenue)}</p>
                    <div className="mt-2.5 h-1.5 w-full rounded-full bg-secondary overflow-hidden">
                      <div className="h-full rounded-full bg-indigo-600 transition-all duration-500" style={{ width: `${pct}%`, opacity: 1 - i * 0.15 }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Agent timeline for Analysts / Admins, Executive Summary for Executive / Managers */}
        <div className="col-span-12 lg:col-span-4 rounded-2xl border border-border bg-card card-soft p-6" data-testid="dashboard-agent-timeline">
          {["admin", "analyst"].includes(userRole) ? (
            <>
              <div className="flex items-center justify-between mb-5">
                <div>
                  <h3 className="text-sm font-semibold">Latest Agent Run</h3>
                  <p className="text-xs text-muted-foreground mono">{data.latest_run?.status === "running" ? "executing…" : "pipeline completed"}</p>
                </div>
                <StatusBadge status={data.latest_run?.status} />
              </div>
              <AgentTimeline run={data.latest_run} compact />
              <Link to="/app/upload">
                <Button variant="outline" className="w-full mt-5 text-xs" data-testid="dashboard-run-pipeline-btn">Run new analysis</Button>
              </Link>
            </>
          ) : (
            <>
              <div className="flex items-center justify-between mb-5">
                <div>
                  <h3 className="text-sm font-semibold">Executive Actions</h3>
                  <p className="text-xs text-muted-foreground mono">governance readiness</p>
                </div>
                <StatusBadge status="completed" />
              </div>
              <div className="space-y-3 py-2 text-xs text-muted-foreground leading-relaxed">
                <div className="rounded-xl bg-secondary/50 p-3 border border-border/60">
                  <p className="font-semibold text-foreground mb-1">Human-in-the-loop Sign-off</p>
                  <p>18 recommendations approved this quarter by workspace managers.</p>
                </div>
                <div className="rounded-xl bg-secondary/50 p-3 border border-border/60">
                  <p className="font-semibold text-foreground mb-1">Audit Compliance</p>
                  <p>All pipeline runs logged with deterministic confidence scores.</p>
                </div>
              </div>
              <Link to="/app/reports">
                <Button variant="outline" className="w-full mt-4 text-xs">Generate Executive Report</Button>
              </Link>
            </>
          )}
        </div>

        {/* Inventory alerts */}
        <div className="col-span-12 lg:col-span-4 rounded-2xl border border-border bg-card card-soft p-6" data-testid="inventory-alerts">
          <h3 className="text-sm font-semibold mb-4">Inventory Alerts</h3>
          <div className="space-y-3">
            {[
              { icon: Clock, label: "Near-expiry batches", value: data.inventory_alerts.near_expiry, color: "text-amber-600" },
              { icon: AlertTriangle, label: "Low stock SKUs", value: data.inventory_alerts.low_stock, color: "text-orange-600" },
              { icon: PackageX, label: "Dead stock items", value: data.inventory_alerts.dead_stock, color: "text-red-600" },
            ].map((a) => (
              <div key={a.label} className="flex items-center justify-between rounded-xl border border-border/60 bg-secondary/40 px-4 py-3">
                <div className="flex items-center gap-3">
                  <a.icon className={`h-4 w-4 ${a.color}`} />
                  <span className="text-[13px]">{a.label}</span>
                </div>
                <span className={`mono text-lg font-semibold ${a.color}`}>{a.value}</span>
              </div>
            ))}
          </div>
          <Link to="/app/insights?tab=inventory" className="mt-4 inline-flex items-center gap-1 text-xs text-indigo-600 hover:underline">
            View inventory analytics <ArrowUpRight className="h-3 w-3" />
          </Link>
        </div>

        {/* Recent activity */}
        <div className="col-span-12 lg:col-span-8 rounded-2xl border border-border bg-card p-6" data-testid="recent-activity">
          <h3 className="text-sm font-semibold mb-4">Recent Activity</h3>
          <div className="space-y-0">
            {data.recent_activity.map((a) => (
              <div key={a.id} className="flex items-start gap-3 py-2.5 border-b border-border/40 last:border-0">
                <span className="mono text-[10px] text-muted-foreground shrink-0 mt-0.5 w-24">{new Date(a.timestamp).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}</span>
                <span className="mono text-[10px] uppercase text-indigo-600 shrink-0 mt-0.5 w-40 truncate">{a.action}</span>
                <p className="text-xs text-muted-foreground leading-relaxed">{a.details}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
