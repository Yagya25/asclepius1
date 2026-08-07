import { useCallback, useEffect, useState } from "react";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { PageHeader, StatusBadge, EmptyState } from "@/components/bits";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Check, X, MessageSquarePlus, Sparkles } from "lucide-react";
import { toast } from "sonner";

const FILTERS = ["all", "pending", "approved", "rejected", "changes_requested"];

export default function Approvals() {
  const { user } = useAuth();
  const [recs, setRecs] = useState([]);
  const [filter, setFilter] = useState("pending");
  const [selectedId, setSelectedId] = useState(null);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [flash, setFlash] = useState(null);
  const canDecide = ["manager", "admin", "executive", "hr_manager"].includes(user.role);

  const load = useCallback(() => api.get("/recommendations").then((r) => setRecs(r.data)), []);
  useEffect(() => { load(); }, [load]);

  const filtered = recs.filter((r) => filter === "all" || r.status === filter);
  const selected = recs.find((r) => r.id === selectedId) || filtered[0];

  useEffect(() => {
    const handler = (e) => {
      if (["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName)) return;
      const idx = filtered.findIndex((r) => r.id === selected?.id);
      if (e.key === "j" && idx < filtered.length - 1) setSelectedId(filtered[idx + 1].id);
      if (e.key === "k" && idx > 0) setSelectedId(filtered[idx - 1].id);
      if (e.key === "a" && canDecide && selected?.status === "pending") decide("approve");
      if (e.key === "r" && canDecide && selected?.status === "pending") decide("reject");
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  });

  const decide = async (action) => {
    if (!selected) return;
    setBusy(true);
    try {
      const endpoint = action === "approve" ? `/recommendations/${selected.id}/approve` : `/recommendations/${selected.id}/reject`;
      const { data } = await api.post(endpoint, { approved_by: user.name, note: comment });
      
      // Update local state
      setRecs((prev) => prev.map((r) => (r.id === selected.id ? { ...r, status: data.status, approved_by: data.approved_by } : r)));
      setComment("");
      setFlash(selected.id);
      setTimeout(() => setFlash(null), 1200);
      toast.success(`Recommendation ${data.status.replace("_", " ")}`);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || "Action failed");
    } finally {
      setBusy(false);
    }
  };

  const addComment = async () => {
    if (!comment.trim() || !selected) return;
    toast.info("Comments are stored as notes when rejecting.");
  };

  return (
    <div data-testid="approvals-page">
      <PageHeader kicker="Governance" title="Approval inbox"
        subtitle="AI recommendations awaiting human judgment. Navigate with j / k, approve with a, reject with r." />

      <div className="flex gap-2 mb-6">
        {FILTERS.map((f) => (
          <button key={f} onClick={() => { setFilter(f); setSelectedId(null); }} data-testid={`filter-${f}`}
            className={`rounded-full px-4 py-1.5 text-xs capitalize transition-colors duration-150 ${
              filter === f ? "bg-foreground text-background" : "bg-secondary text-muted-foreground hover:text-foreground"}`}>
            {f.replace("_", " ")} {f !== "all" && <span className="mono ml-1">{recs.filter((r) => r.status === f).length}</span>}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyState title="Inbox zero" subtitle="No recommendations match this filter. The agents will file new ones after the next pipeline run." />
      ) : (
        <div className="grid grid-cols-12 gap-5">
          {/* List */}
          <div className="col-span-12 lg:col-span-5 space-y-1.5" data-testid="approvals-list">
            {filtered.map((r) => (
              <button key={r.id} onClick={() => setSelectedId(r.id)} data-testid={`rec-item-${r.id}`}
                className={`w-full text-left rounded-xl border px-4 py-3.5 transition-colors duration-150 ${flash === r.id ? "flash-success" : ""} ${
                  selected?.id === r.id ? "border-foreground/40 bg-card card-soft" : "border-border bg-card/50 hover:bg-card"}`}>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[13px] font-medium truncate">{r.title}</p>
                  <StatusBadge status={r.status} className="shrink-0" />
                </div>
                <div className="mt-1.5 flex items-center gap-3">
                  <StatusBadge status={r.severity || "info"} />
                  <span className="mono text-[10px] text-muted-foreground">{r.action_type || "insight"}</span>
                </div>
              </button>
            ))}
          </div>

          {/* Detail */}
          {selected && (
            <div className="col-span-12 lg:col-span-7 rounded-2xl border border-border bg-card card-soft p-7 h-fit sticky top-20" data-testid="rec-detail">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-2.5">
                  <Sparkles className="h-4 w-4 text-indigo-600 mt-1 shrink-0" />
                  <h2 className="text-lg font-medium leading-snug tracking-tight">{selected.title}</h2>
                </div>
                <StatusBadge status={selected.status} className="shrink-0 mt-1" />
              </div>
              <p className="mt-4 text-sm text-muted-foreground leading-relaxed">{selected.description}</p>
              <div className="mt-4 flex flex-wrap items-center gap-3">
                {selected.estimated_impact && (
                  <span className="mono text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-3 py-1">{selected.estimated_impact}</span>
                )}
                <span className="mono text-[11px] text-muted-foreground">{selected.agent_name}</span>
              </div>

              <div className="mt-6 border-t border-border pt-5 space-y-3">
                <Textarea placeholder="Add a note for the audit trail (optional)…" value={comment} onChange={(e) => setComment(e.target.value)}
                  rows={2} className="text-sm resize-none" data-testid="rec-comment-input" />
                <div className="flex flex-wrap gap-2.5">
                  {canDecide && selected.status === "pending" && (
                    <>
                      <Button onClick={() => decide("approve")} disabled={busy} className="rounded-full gap-2" data-testid="approve-btn">
                        <Check className="h-4 w-4" /> Approve
                      </Button>
                      {user.role !== "executive" && (
                        <Button onClick={() => decide("reject")} disabled={busy} variant="outline" className="rounded-full gap-2 text-red-600 border-red-200 hover:bg-red-50" data-testid="reject-btn">
                          <X className="h-4 w-4" /> Reject
                        </Button>
                      )}
                    </>
                  )}
                </div>
                {!canDecide && <p className="text-[11px] text-muted-foreground">Approvals require Manager, Executive, or Admin role.</p>}
                {selected.approved_by && (
                  <p className="mono text-[10px] text-muted-foreground/70">decided by {selected.approved_by} {selected.approved_at && `· ${new Date(selected.approved_at).toLocaleString("en-IN")}`}</p>
                )}
                {selected.modified_note && (
                  <div className="mt-4 rounded-xl bg-secondary/60 px-4 py-3">
                    <p className="text-xs font-medium">Rejection Note</p>
                    <p className="mt-1 text-[13px] text-muted-foreground">{selected.modified_note}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
