import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { 
  ArrowRight, 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  Activity, 
  ShieldCheck, 
  FileSpreadsheet,
  Check
} from "lucide-react";

const AGENTS = ["Ingestion", "Validation", "Analysis", "Anomaly", "Forecast", "Recommendation"];

const FEATURES = [
  { n: "01", title: "Multi-agent pipeline", desc: "Six specialised agents validate, analyse, detect anomalies, forecast, and recommend — each step visible, timed, and scored." },
  { n: "02", title: "Human-in-the-loop", desc: "Every AI recommendation passes through a governed approval inbox before it becomes a decision." },
  { n: "03", title: "Explainable by default", desc: "Reasoning chains, confidence scores, and data lineage accompany every insight. No black boxes." },
  { n: "04", title: "Demand forecasting", desc: "Thirty-day SKU-level forecasts with confidence bands surface stockouts and dead stock early." },
  { n: "05", title: "Board-ready reports", desc: "One click produces branded PDF and formatted Excel exports, archived with full delivery history." },
  { n: "06", title: "Immutable audit trail", desc: "Every agent action, approval, and export is logged. Compliance-ready from day one." },
];

export default function Landing() {
  const [approved, setApproved] = useState(false);
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % AGENTS.length);
    }, 2800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#09090b] text-[#fafafa] overflow-x-hidden selection:bg-white/20 selection:text-white">
      {/* Precision Header */}
      <nav className="flex items-center justify-between px-8 lg:px-16 h-20 border-b border-white/[0.08] backdrop-blur-md sticky top-0 bg-[#09090b]/90 z-50">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg flex items-center justify-center overflow-hidden ring-1 ring-white/20">
            <img src="/logo.jpg" alt="Asclepius Logo" className="h-full w-full object-cover" />
          </div>
          <span className="font-semibold tracking-tight text-sm text-white flex items-center gap-2.5">
            Asclepius
          </span>
        </div>
        <div className="flex items-center gap-5">
          <Link to="/login">
            <Button variant="outline" className="rounded-full text-xs font-medium px-5 bg-white/5 border-white/15 hover:bg-white/10 hover:text-white text-zinc-200 transition-all h-9" data-testid="landing-signin-btn">
              Sign in
            </Button>
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="px-8 lg:px-16 pt-20 pb-28 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 xl:gap-16 items-center">
          
          <motion.div 
            initial={{ opacity: 0, y: 16 }} 
            animate={{ opacity: 1, y: 0 }} 
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="lg:col-span-6 xl:col-span-5 flex flex-col items-start"
          >
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-white/[0.06] border border-white/10 mb-6 text-zinc-300 text-xs font-mono">
              <Sparkles className="h-3.5 w-3.5 text-zinc-400" />
              <span>ENTERPRISE DECISION AUTOMATION</span>
            </div>
            <p className="mono text-[11px] uppercase tracking-[0.25em] text-zinc-400 mb-3 font-medium">
              It all starts with a spreadsheet
            </p>
            <h1 className="text-4xl sm:text-5xl lg:text-[56px] font-bold tracking-tight leading-[1.08] text-white">
              Then comes the <span className="text-zinc-400 font-normal italic">decision.</span>
            </h1>
            <p className="mt-6 text-base text-zinc-400 leading-relaxed font-normal">
              Asclepius transforms raw pharmaceutical & enterprise ERP exports into validated diagnostic narratives, demand forecasts, and board-ready management reports through a transparent multi-agent workflow, governed by you.
            </p>
            <div className="mt-9 flex flex-col sm:flex-row sm:items-center gap-4 w-full sm:w-auto">
              <Link to="/login" className="w-full sm:w-auto">
                <Button size="lg" className="rounded-full px-7 gap-2.5 h-12 bg-white text-black hover:bg-zinc-200 font-medium tracking-tight shadow-lg shadow-white/5 transition-all duration-200 w-full sm:w-auto" data-testid="landing-cta-btn">
                  See it decide in 2 minutes <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <span className="mono text-[11px] text-zinc-500 text-center sm:text-left">
                Guided demo · seeded pharma data
              </span>
            </div>

            {/* Live Pipeline Stepper */}
            <div className="mt-14 pt-8 border-t border-white/[0.08] w-full">
              <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-4 flex items-center gap-2 font-mono">
                <Activity className="h-3.5 w-3.5 text-zinc-300" /> Live Autonomous Agents
              </p>
              <div className="flex flex-wrap items-center gap-2">
                {AGENTS.map((a, i) => {
                  const isCurrent = i === activeStep;
                  return (
                    <motion.div 
                      key={a} 
                      animate={isCurrent ? { scale: [1, 1.02, 1] } : { scale: 1 }}
                      className={`flex items-center gap-1.5 mono text-[11px] px-3 py-1.5 rounded-md transition-all duration-500 ${
                        isCurrent 
                          ? "bg-white/[0.08] text-white font-medium ring-1 ring-white/[0.15]" 
                          : "bg-transparent text-zinc-500 border border-transparent"
                      }`}
                    >
                      <span className={`h-1.5 w-1.5 rounded-full ${isCurrent ? "bg-zinc-300" : "bg-zinc-700"}`} />
                      {String(i + 1).padStart(2, "0")} — {a}
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </motion.div>

          {/* Right Column: Linear-grade Executive AI Monitor */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.98 }} 
            animate={{ opacity: 1, scale: 1 }} 
            transition={{ delay: 0.15, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            className="lg:col-span-6 xl:col-span-7"
          >
            <div className="rounded-2xl p-6 sm:p-7 relative overflow-hidden bg-gradient-to-b from-zinc-900/40 to-zinc-950/40 border border-white/[0.04] shadow-2xl shadow-black">
              {/* Window Header */}
              <div className="flex items-center justify-between pb-5 border-b border-white/[0.04] mb-6">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs text-zinc-500 font-medium tracking-tight">
                    asclepius-ai // runtime-engine
                  </span>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 text-zinc-400 text-[11px] font-mono font-medium">
                  <span className="h-1.5 w-1.5 rounded-full bg-zinc-500" />
                  LIVE SYNC
                </div>
              </div>

              {/* KPI Ticker Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                <div className="rounded-xl bg-white/[0.02] border border-white/[0.04] p-3.5">
                  <span className="text-[11px] font-mono text-zinc-500 block">Health Score</span>
                  <div className="mt-1 flex items-baseline gap-1.5">
                    <span className="text-xl font-bold text-zinc-100 tracking-tight">88.4</span>
                  </div>
                  <div className="w-full bg-zinc-800 h-0.5 rounded-full mt-2.5 overflow-hidden">
                    <div className="bg-zinc-400 h-full rounded-full w-[88%]" />
                  </div>
                </div>

                <div className="rounded-xl bg-white/[0.02] border border-white/[0.04] p-3.5">
                  <span className="text-[11px] font-mono text-zinc-500 block">YTD Revenue</span>
                  <div className="mt-1 flex items-baseline gap-1.5">
                    <span className="text-xl font-bold text-zinc-100 tracking-tight">₹14.25Cr</span>
                  </div>
                  <p className="text-[10px] text-zinc-500 mt-2.5 font-mono">128 SKUs</p>
                </div>

                <div className="rounded-xl bg-white/[0.02] border border-white/[0.04] p-3.5">
                  <span className="text-[11px] font-mono text-zinc-500 block">Open Anomalies</span>
                  <div className="mt-1 flex items-baseline gap-1.5">
                    <span className="text-xl font-bold text-zinc-100 tracking-tight">02</span>
                  </div>
                  <p className="text-[10px] text-zinc-500 mt-2.5 font-mono flex items-center gap-1">
                    Action req.
                  </p>
                </div>

                <div className="rounded-xl bg-white/[0.02] border border-white/[0.04] p-3.5">
                  <span className="text-[11px] font-mono text-zinc-500 block">Export Status</span>
                  <div className="mt-1 flex items-center gap-2">
                    <span className="text-xl font-bold text-zinc-100 tracking-tight">Ready</span>
                  </div>
                  <p className="text-[10px] text-zinc-500 mt-2.5 font-mono">XLSX / PDF</p>
                </div>
              </div>

              {/* Agent Reasoning Stream Feed */}
              <div className="space-y-3">
                <div className="p-3.5 rounded-xl bg-zinc-900/60 border border-white/[0.06] flex items-start gap-3">
                  <div className="h-7 w-7 rounded-lg bg-white/5 border border-white/10 text-zinc-300 flex items-center justify-center shrink-0 mt-0.5">
                    <FileSpreadsheet className="h-3.5 w-3.5" />
                  </div>
                  <div className="text-xs">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-zinc-200 font-mono">Ingestion & Schema Agent</span>
                      <span className="font-mono text-[10px] text-zinc-500">22ms ago</span>
                    </div>
                    <p className="text-zinc-400 leading-relaxed font-normal">
                      Ingested <span className="font-mono text-zinc-300 bg-white/5 px-1.5 py-0.5 rounded border border-white/10">pharma_distributor_sales.xlsx</span>. Validated 14,200 transactions across 128 active product lines. Zero structural schema mismatches.
                    </p>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.04] flex items-start gap-3">
                  <div className="h-7 w-7 rounded-lg bg-white/5 border border-white/10 text-zinc-300 flex items-center justify-center shrink-0 mt-0.5">
                    <AlertTriangle className="h-3.5 w-3.5" />
                  </div>
                  <div className="text-xs w-full">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="font-semibold text-zinc-300 font-mono">Anomaly Detection Engine</span>
                      <span className="font-mono text-[10px] bg-white/[0.04] text-zinc-400 border border-white/[0.06] px-2 py-0.5 rounded">Z-SCORE 3.8</span>
                    </div>
                    <p className="text-zinc-400 leading-relaxed font-normal">
                      Unexplained 82% order volume surge detected across Punjab distributors for <strong className="text-zinc-200 font-medium">Ciprofloxacin 500mg</strong> without matching retail prescription spikes.
                    </p>
                  </div>
                </div>

                {/* Interactive Decision Proposal Card */}
                <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.08] shadow-lg">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <div className="h-7 w-7 rounded-lg bg-white/10 text-white flex items-center justify-center shrink-0 mt-0.5">
                        <Sparkles className="h-3.5 w-3.5" />
                      </div>
                      <div className="text-xs">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold text-white font-mono">Inventory Recommendation Agent</span>
                          <span className="font-mono text-[10px] text-zinc-300 bg-white/[0.04] border border-white/[0.08] px-1.5 py-0.5 rounded">₹18.5L IMPACT</span>
                        </div>
                        <p className="text-zinc-400 font-normal leading-relaxed">
                          Reorder <strong className="text-white font-medium">Amoxicillin 500mg</strong> immediately (28 days to projected stockout in North distributor buffer).
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3.5 pt-3.5 border-t border-white/[0.04] flex items-center justify-between">
                    <span className="text-[11px] font-mono text-zinc-500 flex items-center gap-1.5">
                      <ShieldCheck className="h-3.5 w-3.5 text-zinc-400" /> Requires Governance Sign-off
                    </span>
                    <button
                      onClick={() => setApproved(true)}
                      className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 flex items-center gap-1.5 ${
                        approved 
                          ? "bg-zinc-800 text-white font-semibold ring-1 ring-white/[0.15]" 
                          : "bg-white text-black hover:bg-zinc-200 font-semibold shadow"
                      }`}
                    >
                      {approved ? (
                        <>
                          <Check className="h-3.5 w-3.5 stroke-[3]" /> Approved by Executive
                        </>
                      ) : (
                        <>
                          Approve Decision &rarr;
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Bottom System Footer in Card */}
              <div className="mt-5 pt-4 border-t border-white/[0.08] flex flex-wrap items-center justify-between text-[11px] font-mono text-zinc-500">
                <span>MODEL: GEMINI 3 FLASH HYBRID</span>
                <span className="flex items-center gap-1 text-zinc-400">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> Immutable AUDIT LOG RECORDED
                </span>
              </div>
            </div>
          </motion.div>

        </div>
      </section>

      {/* Features Grid */}
      <section className="px-8 lg:px-16 pb-28 max-w-7xl mx-auto">
        <div className="border-t border-white/[0.08] pt-12">
          <p className="mono text-xs uppercase tracking-[0.25em] text-zinc-400 font-semibold mb-2">Engineered for Reliability</p>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-10 text-white">How Asclepius eliminates black-box analytics.</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f, i) => (
              <motion.div 
                key={f.n} 
                initial={{ opacity: 0, y: 12 }} 
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }} 
                transition={{ delay: i * 0.05, duration: 0.4 }}
                className="linear-card p-6 rounded-2xl flex flex-col justify-between group"
              >
                <div>
                  <span className="mono text-xs text-zinc-400 font-mono font-semibold block mb-3">{f.n}</span>
                  <h3 className="text-base font-semibold tracking-tight mb-2 text-white group-hover:text-zinc-200 transition-colors">{f.title}</h3>
                  <p className="text-xs text-zinc-400 leading-relaxed font-normal">{f.desc}</p>
                </div>
                <div className="mt-6 pt-4 border-t border-white/[0.06] flex items-center justify-between text-[11px] font-mono text-zinc-500">
                  <span>SYSTEM FEATURE</span>
                  <span className="text-zinc-300 group-hover:translate-x-1 transition-transform duration-200">&rarr;</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <footer className="px-8 lg:px-16 py-10 border-t border-white/[0.08] flex flex-wrap items-center justify-between gap-4 max-w-7xl mx-auto text-xs font-mono text-zinc-500">
        <p>Asclepius — 2026 Enterprise Edition</p>
        <div className="flex items-center gap-6">
          <span>FastAPI</span>
          <span>•</span>
          <span>React + Tailwind</span>
          <span>•</span>
          <span>Gemini 3 Flash &amp; NVIDIA</span>
        </div>
      </footer>
    </div>
  );
}
