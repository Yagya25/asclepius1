import { useEffect, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";

export function Counter({ value, format = (v) => v.toLocaleString("en-IN"), duration = 900 }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef();
  useEffect(() => {
    const start = performance.now();
    const step = (t) => {
      const p = Math.min((t - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplay(value * eased);
      if (p < 1) ref.current = requestAnimationFrame(step);
    };
    ref.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(ref.current);
  }, [value, duration]);
  return <span className="mono tabular-nums">{format(display)}</span>;
}

const STATUS_STYLES = {
  pending: "bg-amber-50 text-amber-700 border-amber-200",
  approved: "bg-emerald-50 text-emerald-700 border-emerald-200",
  rejected: "bg-red-50 text-red-700 border-red-200",
  changes_requested: "bg-sky-50 text-sky-700 border-sky-200",
  running: "bg-indigo-50 text-indigo-700 border-indigo-200",
  completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  failed: "bg-red-50 text-red-700 border-red-200",
  queued: "bg-zinc-50 text-zinc-500 border-zinc-200",
  critical: "bg-red-50 text-red-700 border-red-200",
  high: "bg-orange-50 text-orange-700 border-orange-200",
  medium: "bg-amber-50 text-amber-700 border-amber-200",
  low: "bg-zinc-50 text-zinc-500 border-zinc-200",
  healthy: "bg-emerald-50 text-emerald-700 border-emerald-200",
  near_expiry: "bg-amber-50 text-amber-700 border-amber-200",
  low_stock: "bg-orange-50 text-orange-700 border-orange-200",
  dead_stock: "bg-red-50 text-red-700 border-red-200",
  validated: "bg-emerald-50 text-emerald-700 border-emerald-200",
  analyzed: "bg-indigo-50 text-indigo-700 border-indigo-200",
  needs_cleaning: "bg-amber-50 text-amber-700 border-amber-200",
  uploaded: "bg-zinc-50 text-zinc-500 border-zinc-200",
  ready: "bg-emerald-50 text-emerald-700 border-emerald-200",
  open: "bg-red-50 text-red-700 border-red-200",
};

export function StatusBadge({ status, className = "" }) {
  return (
    <Badge variant="outline" className={`mono text-[10px] font-medium uppercase tracking-wider ${STATUS_STYLES[status] || "bg-zinc-50 text-zinc-500 border-zinc-200"} ${className}`}>
      {String(status || "").replace(/_/g, " ")}
    </Badge>
  );
}

export function EmptyState({ title, subtitle, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center" data-testid="empty-state">
      <svg width="72" height="72" viewBox="0 0 88 88" fill="none" className="mb-8 opacity-70">
        <rect x="12" y="20" width="40" height="40" rx="8" stroke="hsl(240 8% 10%)" strokeWidth="1.2" />
        <rect x="34" y="34" width="40" height="40" rx="8" stroke="hsl(240 4% 70%)" strokeWidth="1.2" strokeDasharray="4 5" />
        <circle cx="32" cy="40" r="2.5" fill="hsl(243 40% 45%)" />
      </svg>
      <p className="text-base font-medium">{title}</p>
      <p className="mt-2 text-sm text-muted-foreground max-w-sm leading-relaxed">{subtitle}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}

export function PageHeader({ kicker, title, subtitle, actions }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-6 mb-12">
      <div>
        {kicker && <p className="mono text-[10px] uppercase tracking-[0.28em] text-muted-foreground mb-3">{kicker}</p>}
        <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-3 text-sm text-muted-foreground max-w-2xl leading-relaxed">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
