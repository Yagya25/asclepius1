import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { api, inr, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { AgentTimeline } from "@/components/AgentTimeline";
import { Counter, StatusBadge } from "@/components/bits";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { BarChart, Bar, Cell, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import { FileSpreadsheet, ArrowRight, Check, Download, Upload, Sparkles } from "lucide-react";
import { toast } from "sonner";

const STEPS = ["Data", "Agents", "Insight", "Decision", "Report"];

const fade = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] },
};

export default function Journey() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [uploads, setUploads] = useState([]);
  const [chosen, setChosen] = useState(null);
  const [run, setRun] = useState(null);
  const [dash, setDash] = useState(null);
  const [rec, setRec] = useState(null);
  const [comment, setComment] = useState("");
  const [decided, setDecided] = useState(null);
  const [report, setReport] = useState(null);
  const [busy, setBusy] = useState(false);
  const pollRef = useRef();
  const fileRef = useRef();
  const canDecide = ["manager", "admin", "executive"].includes(user.role);
  const canRun = ["analyst", "manager", "admin"].includes(user.role);

  useEffect(() => {
    const currentPoll = pollRef.current;
    api.get("/datasets").then((r) => {
      setUploads(r.data);
      setChosen(r.data.find((u) => u.status === "analyzed" || u.status === "ready") || r.data[0]);
    });
    return () => clearInterval(currentPoll);
  }, []);

  const finish = () => {
    localStorage.setItem("apbi_journey_done", "1");
    navigate("/app/dashboard");
  };

  const startAgents = async (uploadId) => {
    setStep(1);
    setRun({
      status: "running",
      steps: [
        { agent: "Ingestion Agent", status: "completed", summary: "Data cleaned and formatted" },
        { agent: "Analysis Agent", status: "running", summary: "Computing sales, inventory, and KPIs" },
        { agent: "Insight Agent", status: "queued", summary: "Generating recommendations" }
      ]
    });

    try {
      await api.post(`/datasets/${uploadId}/analyze`);
      setRun({
        status: "completed",
        steps: [
          { agent: "Ingestion Agent", status: "completed", summary: "Data cleaned and formatted" },
          { agent: "Analysis Agent", status: "completed", summary: "Computed sales, inventory, and KPIs" },
          { agent: "Insight Agent", status: "completed", summary: "Generated recommendations for approval queue" }
        ]
      });
      toast.success("All 6 agents finished analyzing your dataset!");
    } catch (e) {
      toast.error("Pipeline failed.");
    }
  };

  const handleFile = async (file) => {
    if (!file) return;
    setBusy(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const { data } = await api.post("/datasets/upload", fd);
      toast.success(`Ingested ${data.rows} rows`);
      startAgents(data.dataset_id);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || "Upload failed");
    } finally {
      setBusy(false);
    }
  };

  const goInsight = async () => {
    const [d, r] = await Promise.all([
      api.get("/dashboard"), api.get("/recommendations"),
    ]);
    setDash(d.data);
    setRec(r.data.find((x) => x.status === "pending") || r.data[0]);
    setStep(2);
  };

  const decide = async (action) => {
    setBusy(true);
    try {
      if (canDecide && action !== "comment") {
        const endpoint = action === "approve" ? `/recommendations/${rec.id}/approve` : `/recommendations/${rec.id}/reject`;
        const { data } = await api.post(endpoint, { approved_by: user.name, note: comment });
        setRec({ ...rec, status: data.status, approved_by: data.approved_by });
      }
      setDecided(action);
      toast.success(action === "approve" ? "Recommendation approved" : "Change request recorded");
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || "Action failed");
    } finally {
      setBusy(false);
    }
  };

  const generateReport = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/reports", { template: "executive_summary", format: "pdf" });
      setReport(data);
      toast.success("Executive Summary generated");
    } catch (e) {
      toast.error("Report generation failed");
    } finally {
      setBusy(false);
    }
  };

  const download = async () => {
    if (!report || !report.id) return;
    try {
      toast.success("Downloading PDF...");
      const res = await api.get(`/reports/${report.id}/download`, { responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      const cleanTitle = (report.title || "Executive_Report").replace(/[^a-zA-Z0-9_\-\ ]/g, "").replace(/\s+/g, "_");
      a.download = `${cleanTitle}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast.error("Could not download report");
    }
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-foreground text-background text-xs px-3 py-2 rounded-lg font-medium shadow-lg">
          {inr(payload[0].value)}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="min-h-screen bg-background" data-testid="journey-page">
      {/* Header */}
      <div className="flex items-center justify-between px-8 lg:px-16 py-7">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-foreground flex items-center justify-center">
            <span className="mono text-xs font-medium text-background">A</span>
          </div>
          <span className="font-medium tracking-tight text-[15px]">Asclepius</span>
        </div>
        <button onClick={finish} className="text-xs text-muted-foreground hover:text-foreground transition-colors duration-150" data-testid="journey-skip-btn">
          Skip tour →
        </button>
      </div>

      {/* Stepper */}
      <div className="flex items-center justify-center gap-0 px-8 mb-16">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center">
            <div className="flex items-center gap-2.5">
              <div className={`h-6 w-6 rounded-full flex items-center justify-center text-[10px] mono transition-colors duration-300 ${
                i < step ? "bg-foreground text-background" : i === step ? "border border-foreground text-foreground" : "border border-border text-muted-foreground/60"}`}>
                {i < step ? <Check className="h-3 w-3" /> : i + 1}
              </div>
              <span className={`text-xs hidden sm:block ${i === step ? "text-foreground font-medium" : "text-muted-foreground/70"}`}>{s}</span>
            </div>
            {i < STEPS.length - 1 && <div className={`h-px w-10 lg:w-20 mx-3 ${i < step ? "bg-foreground" : "bg-border"}`} />}
          </div>
        ))}
      </div>

      <div className="max-w-2xl mx-auto px-8 pb-24">
        <AnimatePresence mode="wait">
          {/* STEP 0 — Data */}
          {step === 0 && (
            <motion.div key="s0" {...fade}>
              <p className="mono text-[10px] uppercase tracking-[0.3em] text-muted-foreground mb-4 text-center">Step 1 — Data intake</p>
              <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-center leading-tight">Begin with your ERP data.</h1>
              <p className="mt-4 text-sm text-muted-foreground text-center leading-relaxed max-w-md mx-auto">
                We've preloaded a realistic quarter of pharmaceutical distribution sales — 562 transactions across 10 products and 4 regions.
              </p>
              {chosen && (
                <div className="mt-10 rounded-2xl border border-border bg-card card-soft p-6" data-testid="journey-dataset-card">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FileSpreadsheet className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="text-sm font-medium">{chosen.filename}</p>
                        <p className="mono text-[11px] text-muted-foreground">{chosen.rows} rows · quality {chosen.quality_score}/100</p>
                      </div>
                    </div>
                    <StatusBadge status={chosen.status} />
                  </div>
                  {chosen.columns && chosen.columns.length > 0 && (
                    <div className="mt-4 flex flex-wrap gap-1.5">
                      {chosen.columns.map((c) => (
                        <span key={c} className="mono text-[10px] rounded-md bg-secondary px-2 py-1 text-muted-foreground">{c}</span>
                      ))}
                    </div>
                  )}
                </div>
              )}
              <div className="mt-8 flex flex-col items-center gap-4">
                <Button size="lg" className="rounded-full px-8 h-12 gap-2" onClick={() => startAgents(chosen.id)} disabled={!chosen} data-testid="journey-use-preloaded-btn">
                  Continue with preloaded data <ArrowRight className="h-4 w-4" />
                </Button>
                {canRun && (
                  <>
                    <input ref={fileRef} type="file" accept=".csv,.xlsx" className="hidden" onChange={(e) => handleFile(e.target.files[0])} data-testid="journey-file-input" />
                    <button onClick={() => fileRef.current?.click()} className="text-xs text-muted-foreground hover:text-foreground transition-colors duration-150 flex items-center gap-1.5" data-testid="journey-upload-own-btn">
                      <Upload className="h-3 w-3" /> {busy ? "Parsing…" : "or upload your own CSV / Excel file"}
                    </button>
                  </>
                )}
              </div>
            </motion.div>
          )}

          {/* STEP 1 — Agents */}
          {step === 1 && (
            <motion.div key="s1" {...fade}>
              <p className="mono text-[10px] uppercase tracking-[0.3em] text-muted-foreground mb-4 text-center">Step 2 — Multi-agent analysis</p>
              <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-center leading-tight">Six agents, working in sequence.</h1>
              <p className="mt-4 text-sm text-muted-foreground text-center leading-relaxed max-w-md mx-auto">
                Validation, analysis, anomaly detection, forecasting, and Gemini-powered recommendations — every step visible and scored.
              </p>
              <div className="mt-10 rounded-2xl border border-border bg-card card-soft p-8">
                {run ? <AgentTimeline run={run} /> : <p className="text-sm text-muted-foreground text-center py-8">Starting agents…</p>}
              </div>
              <div className="mt-8 flex justify-center">
                <Button size="lg" className="rounded-full px-8 h-12 gap-2" onClick={goInsight}
                  disabled={!run || run.status === "running"} data-testid="journey-to-insight-btn">
                  {run?.status === "running" ? "Agents running…" : <>See what they found <ArrowRight className="h-4 w-4" /></>}
                </Button>
              </div>
            </motion.div>
          )}

          {/* STEP 2 — Insight */}
          {step === 2 && dash && (
            <motion.div key="s2" {...fade}>
              <p className="mono text-[10px] uppercase tracking-[0.3em] text-muted-foreground mb-4 text-center">Step 3 — The insight</p>
              <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-center leading-tight">Here's what the data says.</h1>
              <div className="mt-10 grid grid-cols-3 gap-4">
                <div className="rounded-2xl border border-border bg-card card-soft p-5">
                  <p className="mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Revenue</p>
                  <p className="mt-2 text-2xl font-semibold tracking-tight"><Counter value={dash.kpis.total_revenue} format={inr} /></p>
                </div>
                <div className="rounded-2xl border border-border bg-card card-soft p-5">
                  <p className="mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Health</p>
                  <p className="mt-2 text-2xl font-semibold text-emerald-600"><Counter value={dash.health_score} format={(v) => Math.round(v)} /><span className="text-xs text-muted-foreground">/100</span></p>
                </div>
                <div className="rounded-2xl border border-border bg-card card-soft p-5">
                  <p className="mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Anomalies</p>
                  <p className="mt-2 text-2xl font-semibold text-red-600"><Counter value={dash.kpis.open_anomalies} format={(v) => Math.round(v)} /></p>
                </div>
              </div>
              {dash.top_products && dash.top_products.length > 0 && (
                <div className="mt-4 rounded-2xl border border-border bg-card card-soft p-6" data-testid="journey-forecast-chart">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-sm font-medium">Top Performing Products</p>
                      <p className="text-xs text-muted-foreground">Highest revenue generators across all regions</p>
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={dash.top_products} layout="vertical" margin={{ top: 5, right: 30, bottom: 5, left: 100 }}>
                      <XAxis type="number" hide />
                      <YAxis 
                        dataKey="product" 
                        type="category" 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                        width={140}
                      />
                      <Tooltip cursor={{ fill: 'transparent' }} content={<CustomTooltip />} />
                      <Bar dataKey="revenue" radius={[0, 4, 4, 0]} barSize={20}>
                        {dash.top_products.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={index === 0 ? "hsl(243 40% 45%)" : "hsl(var(--muted-foreground)/0.2)"} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
              <div className="mt-8 flex justify-center">
                <Button size="lg" className="rounded-full px-8 h-12 gap-2" onClick={() => setStep(3)} data-testid="journey-to-decision-btn">
                  Review the recommendation <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </motion.div>
          )}

          {/* STEP 3 — Decision */}
          {step === 3 && rec && (
            <motion.div key="s3" {...fade}>
              <p className="mono text-[10px] uppercase tracking-[0.3em] text-muted-foreground mb-4 text-center">Step 4 — Your decision</p>
              <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-center leading-tight">The AI proposes. You decide.</h1>
              <div className={`mt-10 rounded-2xl border border-border bg-card card-soft p-7 ${decided ? "flash-success" : ""}`} data-testid="journey-recommendation-card">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-indigo-600 shrink-0" />
                    <p className="text-base font-medium leading-snug">{rec.title}</p>
                  </div>
                  <StatusBadge status={decided && canDecide ? rec.status : (rec.severity || "info")} />
                </div>
                <p className="mt-4 text-sm text-muted-foreground leading-relaxed">{rec.description}</p>
                <div className="mt-4 flex items-center gap-4">
                  {rec.estimated_impact && (
                    <span className="mono text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-3 py-1">{rec.estimated_impact}</span>
                  )}
                  <span className="mono text-[11px] text-muted-foreground">{rec.agent_name || "InsightAgent"}</span>
                </div>
                {!decided && (
                  <div className="mt-6 space-y-3">
                    <Textarea placeholder={canDecide ? "Optional note for the audit trail…" : "Add your review note (approvals require Manager role)…"}
                      value={comment} onChange={(e) => setComment(e.target.value)} className="text-sm resize-none" rows={2} data-testid="journey-comment-input" />
                    <div className="flex gap-3">
                      {canDecide ? (
                        <>
                          <Button className="flex-1 rounded-full h-11 gap-2" onClick={() => decide("approve")} disabled={busy} data-testid="journey-approve-btn">
                            <Check className="h-4 w-4" /> Approve
                          </Button>
                          <Button variant="outline" className="flex-1 rounded-full h-11" onClick={() => decide("request_changes")} disabled={busy} data-testid="journey-adjust-btn">
                            Request changes
                          </Button>
                        </>
                      ) : (
                        <Button className="flex-1 rounded-full h-11" onClick={() => decide("comment")} disabled={busy || !comment} data-testid="journey-comment-btn">
                          Submit review note
                        </Button>
                      )}
                    </div>
                  </div>
                )}
                {decided && (
                  <div className="mt-6 flex items-center gap-2 text-emerald-700 text-sm" data-testid="journey-decision-done">
                    <Check className="h-4 w-4" /> Recorded in the immutable audit trail.
                  </div>
                )}
              </div>
              <div className="mt-8 flex justify-center">
                <Button size="lg" className="rounded-full px-8 h-12 gap-2" onClick={() => setStep(4)} disabled={!decided} data-testid="journey-to-report-btn">
                  Produce the report <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </motion.div>
          )}

          {/* STEP 4 — Report */}
          {step === 4 && (
            <motion.div key="s4" {...fade}>
              <p className="mono text-[10px] uppercase tracking-[0.3em] text-muted-foreground mb-4 text-center">Step 5 — The deliverable</p>
              <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-center leading-tight">One decision, board-ready.</h1>
              <p className="mt-4 text-sm text-muted-foreground text-center leading-relaxed max-w-md mx-auto">
                A branded Executive Summary — KPIs, regional performance, anomalies, and your approved recommendation — assembled in seconds.
              </p>
              <div className="mt-10 rounded-2xl border border-border bg-card card-soft p-8 text-center">
                {!report ? (
                  <Button size="lg" className="rounded-full px-8 h-12" onClick={generateReport} disabled={busy} data-testid="journey-generate-report-btn">
                    {busy ? "Assembling…" : "Generate Executive Summary (PDF)"}
                  </Button>
                ) : (
                  <div className="rise-in">
                    <div className="mx-auto h-14 w-14 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center mb-4">
                      <Check className="h-6 w-6 text-emerald-600" />
                    </div>
                    <p className="text-sm font-medium">{report.title}</p>
                    <p className="mono text-[11px] text-muted-foreground mt-1">PDF · ReportLab · archived in Reports</p>
                    <Button variant="outline" className="mt-5 rounded-full gap-2" onClick={download} data-testid="journey-download-report-btn">
                      <Download className="h-4 w-4" /> Download PDF
                    </Button>
                  </div>
                )}
              </div>
              <div className="mt-10 text-center">
                <Button size="lg" variant={report ? "default" : "outline"} className="rounded-full px-10 h-12 gap-2" onClick={finish} data-testid="journey-finish-btn">
                  Enter Asclepius <ArrowRight className="h-4 w-4" />
                </Button>
                <p className="mt-4 text-xs text-muted-foreground">Dashboard, approvals inbox, insights, and audit trail await.</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
