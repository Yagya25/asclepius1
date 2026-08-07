import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { PageHeader, StatusBadge, EmptyState } from "@/components/bits";
import { Button } from "@/components/ui/button";
import { FileText, Sheet, Download } from "lucide-react";
import { toast } from "sonner";

const TEMPLATES = [
  { key: "executive_summary", title: "Executive Summary", desc: "KPIs, regional performance, anomalies, and recommendation status — one page for leadership." },
  { key: "inventory_health", title: "Inventory Health", desc: "Near-expiry batches, dead stock, low-stock alerts, and working-capital exposure." },
  { key: "sales_performance", title: "Sales Performance", desc: "Revenue trends, product mix, and top customer movement across regions." },
  { key: "anomaly_digest", title: "Anomaly Digest", desc: "All open anomalies with severity, detection method, and suggested follow-ups." },
];

export default function Reports() {
  const { user } = useAuth();
  const [reports, setReports] = useState([]);
  const [busyKey, setBusyKey] = useState(null);

  const load = useCallback(() => api.get("/reports").then((r) => setReports(r.data)), []);
  useEffect(() => { load(); }, [load]);

  const generate = async (template, format) => {
    setBusyKey(template + format);
    try {
      const { data } = await api.post("/reports", { template, format });
      toast.success(`${format.toUpperCase()} report generated — starting download`);
      load();
      download(data);
    } catch (e) {
      toast.error("Generation failed");
    } finally {
      setBusyKey(null);
    }
  };

  const download = async (r) => {
    try {
      const res = await api.get(`/reports/${r.id}/download`, { responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      const ext = (r.format || (r.id && r.id.includes("xlsx") ? "xlsx" : "pdf")).toLowerCase();
      const cleanTitle = (r.title || "Executive_Report").replace(/[^a-zA-Z0-9_\-\ ]/g, "").replace(/\s+/g, "_");
      a.download = `${cleanTitle}.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast.error("Could not download report");
    }
  };

  return (
    <div data-testid="reports-page">
      <PageHeader kicker="Deliverables" title="Reports"
        subtitle="Branded, print-ready documents assembled from live data. Generate on demand; every export is archived and audited." />

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-14">
        {TEMPLATES.map((t) => (
          <div key={t.key} className="rounded-2xl border border-border bg-card card-soft p-6 flex flex-col" data-testid={`template-${t.key}`}>
            <FileText className="h-5 w-5 text-muted-foreground mb-4" />
            <h3 className="text-sm font-medium">{t.title}</h3>
            <p className="mt-2 text-xs text-muted-foreground leading-relaxed flex-1">{t.desc}</p>
            <div className="mt-5 flex gap-2">
              <Button size="sm" variant="outline" className="rounded-full flex-1 text-xs" disabled={busyKey === t.key + "pdf"}
                onClick={() => generate(t.key, "pdf")} data-testid={`generate-pdf-${t.key}`}>
                {busyKey === t.key + "pdf" ? "…" : "PDF"}
              </Button>
              <Button size="sm" variant="outline" className="rounded-full flex-1 text-xs" disabled={busyKey === t.key + "xlsx"}
                onClick={() => generate(t.key, "xlsx")} data-testid={`generate-xlsx-${t.key}`}>
                {busyKey === t.key + "xlsx" ? "…" : "Excel"}
              </Button>
            </div>
          </div>
        ))}
      </div>

      <p className="mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground mb-4">Delivery history</p>
      {reports.length === 0 ? (
        <EmptyState title="No reports yet" subtitle="Generate your first report from a template above." />
      ) : (
        <div className="rounded-2xl border border-border bg-card card-soft overflow-hidden" data-testid="reports-history">
          {reports.map((r) => (
            <div key={r.id} className="flex items-center justify-between px-6 py-4 border-b border-border/50 last:border-0 hover:bg-secondary/30 transition-colors duration-100">
              <div className="flex items-center gap-4 min-w-0">
                {r.format === "pdf" ? <FileText className="h-4 w-4 text-muted-foreground shrink-0" /> : <Sheet className="h-4 w-4 text-muted-foreground shrink-0" />}
                <div className="min-w-0">
                  <p className="text-[13px] font-medium truncate">{r.title}</p>
                  <p className="mono text-[11px] text-muted-foreground">{r.created_by} · {new Date(r.created_at).toLocaleString("en-IN")}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className="mono text-[10px] uppercase text-muted-foreground">{r.format}</span>
                <StatusBadge status={r.status} />
                <Button size="sm" variant="ghost" className="rounded-full gap-1.5 text-xs" onClick={() => download(r)} data-testid={`download-${r.id}`}>
                  <Download className="h-3.5 w-3.5" /> Download
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
