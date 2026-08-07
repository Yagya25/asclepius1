import { motion } from "framer-motion";
import { Check, Loader2, Circle, AlertTriangle } from "lucide-react";

function StepDot({ status }) {
  if (status === "completed")
    return <div className="h-7 w-7 rounded-full bg-emerald-50 border border-emerald-300 flex items-center justify-center"><Check className="h-3.5 w-3.5 text-emerald-600" /></div>;
  if (status === "running")
    return <div className="h-7 w-7 rounded-full bg-indigo-50 border border-indigo-300 flex items-center justify-center pulse-ring"><Loader2 className="h-3.5 w-3.5 text-indigo-600 animate-spin" /></div>;
  if (status === "failed")
    return <div className="h-7 w-7 rounded-full bg-red-50 border border-red-300 flex items-center justify-center"><AlertTriangle className="h-3.5 w-3.5 text-red-600" /></div>;
  return <div className="h-7 w-7 rounded-full bg-secondary border border-border flex items-center justify-center"><Circle className="h-2 w-2 text-muted-foreground/60" /></div>;
}

export function AgentTimeline({ run, compact = false }) {
  if (!run) return null;
  return (
    <div className="relative" data-testid="agent-timeline">
      {run.steps.map((step, i) => (
        <motion.div
          key={step.agent}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.06, duration: 0.3 }}
          className="relative flex gap-4 pb-7 last:pb-0"
          data-testid={`agent-step-${i}`}
        >
          {i < run.steps.length - 1 && (
            <div className={`absolute left-[13px] top-8 bottom-0 w-px ${step.status === "completed" ? "bg-emerald-300" : "bg-border"}`} />
          )}
          <div className="relative z-10 shrink-0 mt-0.5"><StepDot status={step.status} /></div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between gap-2">
              <p className={`text-sm font-medium ${step.status === "queued" ? "text-muted-foreground/70" : ""}`}>{step.agent}</p>
              <div className="flex items-center gap-3 shrink-0">
                {step.confidence != null && (
                  <span className="mono text-[10px] text-muted-foreground">conf {Math.round(step.confidence * 100)}%</span>
                )}
                <span className={`mono text-[10px] uppercase tracking-wider ${
                  step.status === "running" ? "text-indigo-600" : step.status === "completed" ? "text-emerald-600" : "text-muted-foreground/60"}`}>
                  {step.status}
                </span>
              </div>
            </div>
            {!compact && step.summary && (
              <p className="mt-1.5 text-xs text-muted-foreground leading-relaxed">{step.summary}</p>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
