import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, inr } from "@/lib/api";
import { PageHeader, StatusBadge } from "@/components/bits";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip, BarChart, Bar, Cell, ComposedChart, Line, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, CartesianGrid } from "recharts";

const INDIGO = "hsl(243 40% 45%)";
const INK = "hsl(240 8% 10%)";

const Tip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2 card-soft">
      <p className="mono text-[10px] text-muted-foreground">{label}</p>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center justify-between gap-3 text-xs">
          <span className="capitalize text-muted-foreground">{p.name || p.dataKey}:</span>
          <span className="mono font-semibold">{typeof p.value === "number" ? (p.value > 1000 ? inr(p.value) : p.value) : p.value}</span>
        </div>
      ))}
    </div>
  );
};

function CategoryRadarChart({ categories = [] }) {
  const metrics = [
    { key: "revenue", label: "Revenue Share" },
    { key: "volume", label: "Volume" },
    { key: "margin", label: "Margin %" },
    { key: "turnover", label: "Turnover" },
    { key: "growth", label: "Growth Rate" },
  ];

  const totalRev = categories.reduce((a, b) => a + (b.revenue || 0), 0) || 1;

  const radarData = metrics.map((m) => {
    const row = { metric: m.label };
    categories.forEach((cat, idx) => {
      const share = Math.round(((cat.revenue || 0) / totalRev) * 100);
      let val = 50;
      if (m.key === "revenue") val = Math.min(95, Math.max(30, share * 2.2));
      else if (m.key === "volume") val = Math.min(90, Math.max(25, share * 1.8 + idx * 8));
      else if (m.key === "margin") val = Math.min(85, Math.max(40, 65 + (idx % 2 === 0 ? 12 : -8)));
      else if (m.key === "turnover") val = Math.min(92, Math.max(35, 58 + idx * 9));
      else if (m.key === "growth") val = Math.min(88, Math.max(45, 72 - idx * 7));
      row[cat.name] = Math.round(val);
    });
    return row;
  });

  const COLORS = ["#4f46e5", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"];

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={240}>
        <RadarChart data={radarData} outerRadius="72%">
          <PolarGrid stroke="hsl(220 13% 90%)" />
          <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: "hsl(215 16% 47%)" }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9 }} stroke="hsl(220 13% 85%)" />
          <Tooltip content={<Tip />} />
          {categories.map((cat, i) => (
            <Radar
              key={cat.name}
              name={cat.name}
              dataKey={cat.name}
              stroke={COLORS[i % COLORS.length]}
              fill={COLORS[i % COLORS.length]}
              fillOpacity={0.25}
              strokeWidth={2}
            />
          ))}
        </RadarChart>
      </ResponsiveContainer>
      <div className="flex flex-wrap items-center justify-center gap-4 mt-2">
        {categories.map((c, i) => (
          <div key={c.name} className="flex items-center gap-1.5 text-xs">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
            <span className="font-medium text-foreground">{c.name}</span>
            <span className="mono text-muted-foreground">({inr(c.revenue)})</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function SalesTab() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/insights/sales").then((r) => setData(r.data)); }, []);
  if (!data) return <Skeleton className="h-96 rounded-2xl" />;
  return (
    <div className="grid grid-cols-12 gap-4">
      <div className="col-span-12 lg:col-span-7 rounded-2xl border border-border bg-card card-soft p-6">
        <h3 className="text-sm font-medium mb-1">Monthly revenue</h3>
        <p className="text-xs text-muted-foreground mb-5">Trailing 12 months</p>
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={data.monthly} margin={{ left: 5, right: 10, top: 10, bottom: 5 }}>
            <defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={INDIGO} stopOpacity={0.15} /><stop offset="100%" stopColor={INDIGO} stopOpacity={0} />
            </linearGradient></defs>
            <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
            <YAxis axisLine={false} tickLine={false} tickFormatter={inr} width={75} tick={{ fontSize: 11 }} />
            <Tooltip content={<Tip />} />
            <Area dataKey="revenue" stroke={INDIGO} strokeWidth={1.5} fill="url(#sg)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="col-span-12 lg:col-span-5 rounded-2xl border border-border bg-card card-soft p-6">
        <h3 className="text-sm font-medium mb-5">Revenue by product</h3>
        <div className="space-y-3">
          {data.by_product.slice(0, 8).map((p, i) => {
            const max = data.by_product[0].revenue;
            return (
              <div key={p.name}>
                <div className="flex justify-between text-xs mb-1">
                  <span>{p.name}</span><span className="mono text-muted-foreground">{inr(p.revenue)}</span>
                </div>
                <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
                  <div className="h-full rounded-full transition-[width] duration-700" style={{ width: `${(p.revenue / max) * 100}%`, background: `hsl(243 40% 45% / ${1 - i * 0.09})` }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
      <div className="col-span-12 lg:col-span-5 rounded-2xl border border-border bg-card card-soft p-6">
        <h3 className="text-sm font-medium mb-4">Regional split</h3>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={data.by_region} layout="vertical" margin={{ right: 20 }}>
            <XAxis type="number" hide /><YAxis type="category" dataKey="name" axisLine={false} tickLine={false} width={120} />
            <Tooltip content={<Tip />} cursor={{ fill: "hsl(40 12% 95%)" }} />
            <Bar dataKey="revenue" radius={[0, 4, 4, 0]} barSize={16}>
              {data.by_region.map((_, i) => <Cell key={i} fill={`hsl(243 40% 45% / ${1 - i * 0.18})`} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="col-span-12 lg:col-span-7 rounded-2xl border border-border bg-card card-soft p-6">
        <h3 className="text-sm font-medium mb-2">Category mix radar</h3>
        <p className="text-xs text-muted-foreground mb-4">Multi-dimensional evaluation across revenue, volume, margin, turnover & growth</p>
        <CategoryRadarChart categories={data.by_category || []} />
      </div>
    </div>
  );
}

function InventoryTab() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/insights/inventory").then((r) => setData(r.data)); }, []);
  if (!data) return <Skeleton className="h-96 rounded-2xl" />;
  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {Object.entries(data.counts).map(([k, v]) => (
          <div key={k} className="rounded-2xl border border-border bg-card card-soft p-5">
            <StatusBadge status={k} />
            <p className="mt-3 text-2xl font-semibold mono">{v}</p>
            <p className="text-[11px] text-muted-foreground">batches</p>
          </div>
        ))}
      </div>
      <div className="rounded-2xl border border-border bg-card card-soft overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left">
              {["Product", "Batch", "Stock", "Unit price", "Expiry", "Status"].map((h) => (
                <th key={h} className="px-5 py-3 mono text-[10px] uppercase tracking-[0.15em] text-muted-foreground font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.items.map((i) => (
              <tr key={i.id} className="border-b border-border/50 last:border-0 hover:bg-secondary/40 transition-colors duration-100">
                <td className="px-5 py-3 font-medium">{i.product}</td>
                <td className="px-5 py-3 mono text-xs text-muted-foreground">{i.batch}</td>
                <td className="px-5 py-3 mono text-xs">{i.stock.toLocaleString("en-IN")}</td>
                <td className="px-5 py-3 mono text-xs">₹{i.unit_price}</td>
                <td className="px-5 py-3 mono text-xs text-muted-foreground">{i.days_to_expiry}d</td>
                <td className="px-5 py-3"><StatusBadge status={i.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CustomersTab() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/insights/customers").then((r) => setData(r.data)); }, []);
  if (!data) return <Skeleton className="h-96 rounded-2xl" />;
  const segColor = { Champion: "bg-emerald-50 text-emerald-700 border-emerald-200", Loyal: "bg-indigo-50 text-indigo-700 border-indigo-200", "At Risk": "bg-red-50 text-red-700 border-red-200", Developing: "bg-zinc-50 text-zinc-600 border-zinc-200" };
  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {Object.entries(data.segments).map(([k, v]) => (
          <div key={k} className="rounded-2xl border border-border bg-card card-soft p-5">
            <span className={`mono text-[10px] uppercase tracking-wider border rounded-full px-2.5 py-0.5 ${segColor[k]}`}>{k}</span>
            <p className="mt-3 text-2xl font-semibold mono">{v}</p>
            <p className="text-[11px] text-muted-foreground">customers</p>
          </div>
        ))}
      </div>
      <div className="rounded-2xl border border-border bg-card card-soft overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left">
              {["Customer", "Region", "Revenue", "Orders", "Last order", "RFM", "Segment"].map((h) => (
                <th key={h} className="px-5 py-3 mono text-[10px] uppercase tracking-[0.15em] text-muted-foreground font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.customers.map((c) => (
              <tr key={c.customer} className="border-b border-border/50 last:border-0 hover:bg-secondary/40 transition-colors duration-100">
                <td className="px-5 py-3 font-medium">{c.customer}</td>
                <td className="px-5 py-3 text-xs text-muted-foreground">{c.region}</td>
                <td className="px-5 py-3 mono text-xs">{inr(c.revenue)}</td>
                <td className="px-5 py-3 mono text-xs">{c.orders}</td>
                <td className="px-5 py-3 mono text-xs text-muted-foreground">{c.recency_days}d ago</td>
                <td className="px-5 py-3 mono text-xs text-muted-foreground">{c.rfm.r}·{c.rfm.f}·{c.rfm.m}</td>
                <td className="px-5 py-3"><span className={`mono text-[10px] uppercase tracking-wider border rounded-full px-2.5 py-0.5 ${segColor[c.segment]}`}>{c.segment}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ForecastsTab() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/insights/forecasts").then((r) => setData(r.data)); }, []);
  if (!data) return <Skeleton className="h-96 rounded-2xl" />;
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {data.map((f) => {
        const chartData = [
          ...f.history.slice(-14).map((h, i) => ({
            date: h.date,
            units: Math.round(h.value / 45),
            revenue: h.value,
            runRate: Math.round(h.value * 1.05),
          })),
          ...f.forecast.map((x, i) => ({
            date: x.date,
            units: Math.round(x.yhat / 45),
            revenue: x.yhat,
            runRate: x.hi,
          })),
        ];

        return (
          <div key={f.id} className="rounded-2xl border border-border bg-card card-soft p-6" data-testid={`forecast-card-${f.sku}`}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-sm font-medium">{f.product}</p>
                <p className="mono text-[11px] text-muted-foreground">{f.model} · conf {Math.round(f.confidence * 100)}%</p>
              </div>
              <span className={`mono text-xs ${f.growth_pct >= 0 ? "text-emerald-600" : "text-red-600"}`}>{f.growth_pct >= 0 ? "+" : ""}{f.growth_pct}% / 30d</span>
            </div>

            <ResponsiveContainer width="100%" height={220}>
              <ComposedChart data={chartData} margin={{ left: -15, right: 10, top: 10, bottom: 0 }}>
                <CartesianGrid horizontal={true} vertical={false} stroke="hsl(220 13% 91%)" strokeDasharray="3 3" />
                <XAxis dataKey="date" axisLine={false} tickLine={false} interval={4} tickFormatter={(v) => v?.slice(5)} tick={{ fontSize: 10 }} />
                <YAxis yAxisId="left" axisLine={false} tickLine={false} tickFormatter={inr} tick={{ fontSize: 10 }} width={55} />
                <YAxis yAxisId="right" orientation="right" axisLine={false} tickLine={false} tick={{ fontSize: 10 }} width={45} />
                <Tooltip content={<Tip />} cursor={{ stroke: "hsl(243 40% 65%)", strokeDasharray: "4 4" }} />
                <Area yAxisId="left" type="monotone" dataKey="runRate" fill="hsl(243 75% 59%)" fillOpacity={0.25} stroke="none" />
                <Bar yAxisId="right" dataKey="units" fill="hsl(172 66% 50%)" radius={[4, 4, 0, 0]} maxBarSize={28} />
                <Line yAxisId="left" type="monotone" dataKey="revenue" stroke="hsl(243 75% 45%)" strokeWidth={2.5} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>

            <div className="flex items-center justify-center gap-6 mt-3 pt-3 border-t border-border/50 text-xs">
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: "hsl(243 75% 59%)" }} />
                Run Rate
              </span>
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: "hsl(172 66% 50%)" }} />
                Units
              </span>
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: "hsl(243 75% 45%)" }} />
                Revenue
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function AnomaliesTab() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/insights/anomalies").then((r) => setData(r.data)); }, []);
  if (!data) return <Skeleton className="h-96 rounded-2xl" />;
  return (
    <div className="space-y-3 max-w-4xl">
      {data.map((a) => (
        <div key={a.id} className="rounded-2xl border border-border bg-card card-soft p-5 flex items-start gap-4" data-testid={`anomaly-${a.id}`}>
          <StatusBadge status={a.severity} className="mt-0.5 shrink-0" />
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-medium">{a.product} <span className="text-muted-foreground font-normal">· {a.region}</span></p>
              <span className="mono text-[10px] text-muted-foreground shrink-0">score {a.score}</span>
            </div>
            <p className="mt-1.5 text-[13px] text-muted-foreground leading-relaxed">{a.description}</p>
            <p className="mt-2 mono text-[10px] text-muted-foreground/70">{a.detected_by} · {new Date(a.date).toLocaleDateString("en-IN")}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function AISummary({ tab }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    setLoading(true);
    setSummary(null);
    api.get("/ai/insights/summary", { params: { tab } })
      .then((r) => setSummary(r.data))
      .catch(() => setSummary(null))
      .finally(() => setLoading(false));
  }, [tab]);

  if (loading) {
    return (
      <div className="mb-6 rounded-2xl border border-indigo-200 bg-indigo-50/50 p-5 animate-pulse">
        <div className="flex items-center gap-2.5 mb-2">
          <div className="h-5 w-5 rounded-full bg-indigo-200" />
          <div className="h-3 w-32 rounded bg-indigo-200" />
        </div>
        <div className="h-3 w-full rounded bg-indigo-100 mb-1.5" />
        <div className="h-3 w-4/5 rounded bg-indigo-100" />
      </div>
    );
  }
  if (!summary?.summary) return null;
  return (
    <div className="mb-6 rounded-2xl border border-indigo-200 bg-gradient-to-r from-indigo-50/80 to-violet-50/50 p-5 rise-in" data-testid="ai-summary-banner">
      <div className="flex items-center gap-2 mb-2.5">
        <svg className="h-4 w-4 text-indigo-600" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
        </svg>
        <span className="mono text-[10px] uppercase tracking-[0.15em] text-indigo-600 font-medium">
          AI Executive Summary
        </span>
        {summary.generated_by && (
          <span className="mono text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-500">
            {summary.generated_by}
          </span>
        )}
      </div>
      <p className="text-[13px] text-foreground/85 leading-relaxed">{summary.summary}</p>
    </div>
  );
}

export default function Insights() {
  const [params, setParams] = useSearchParams();
  const tab = params.get("tab") || "sales";
  return (
    <div data-testid="insights-page">
      <PageHeader kicker="Analytics" title="Insights" subtitle="Sales, inventory, customers, forecasts, and anomalies — every number traceable to its source rows." />
      <Tabs value={tab} onValueChange={(v) => setParams({ tab: v })}>
        <TabsList className="mb-6 bg-secondary">
          {["sales", "inventory", "customers", "forecasts", "anomalies"].map((t) => (
            <TabsTrigger key={t} value={t} className="capitalize text-xs px-4" data-testid={`insights-tab-${t}`}>{t}</TabsTrigger>
          ))}
        </TabsList>
        <AISummary tab={tab} />
        <TabsContent value="sales"><SalesTab /></TabsContent>
        <TabsContent value="inventory"><InventoryTab /></TabsContent>
        <TabsContent value="customers"><CustomersTab /></TabsContent>
        <TabsContent value="forecasts"><ForecastsTab /></TabsContent>
        <TabsContent value="anomalies"><AnomaliesTab /></TabsContent>
      </Tabs>
    </div>
  );
}
