import { useCallback, useEffect, useState } from "react";
import { api, formatApiError } from "@/lib/api";
import { PageHeader, StatusBadge, EmptyState } from "@/components/bits";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ClipboardCheck, CheckCircle2, Circle, UserPlus, Sparkles, Building2 } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";

export default function HROnboarding() {
  const { user } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [selectedEmp, setSelectedEmp] = useState(null);
  const [onboarding, setOnboarding] = useState(null);
  const [busy, setBusy] = useState(false);

  // New employee form
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("");
  const [dept, setDept] = useState("Sales");

  const loadEmployees = useCallback(async () => {
    try {
      const { data } = await api.get("/hr/employees");
      setEmployees(data);
      if (data.length > 0 && !selectedEmp) {
        setSelectedEmp(data[0]);
        loadOnboarding(data[0].id);
      }
    } catch (e) {
      toast.error("Failed to load employees");
    }
  }, [selectedEmp]);

  const loadOnboarding = async (empId) => {
    try {
      const { data } = await api.get(`/hr/employees/${empId}/onboarding`);
      setOnboarding(data);
    } catch (e) {
      setOnboarding(null);
    }
  };

  useEffect(() => { loadEmployees(); }, [loadEmployees]);

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!name || !email || !role) return toast.error("Please complete all fields");
    setBusy(true);
    try {
      const { data } = await api.post("/hr/employees", { name, email, role, department: dept });
      toast.success(`Registered new employee: ${data.name}`);
      setEmployees((prev) => [data, ...prev]);
      setSelectedEmp(data);
      setName(""); setEmail(""); setRole("");
      await triggerOnboarding(data.id);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail) || "Registration failed");
    } finally {
      setBusy(false);
    }
  };

  const triggerOnboarding = async (empId) => {
    setBusy(true);
    try {
      const { data } = await api.post(`/hr/employees/${empId}/onboard`);
      toast.success("AI Onboarding Agent generated department checklist");
      setOnboarding(data);
    } catch (e) {
      toast.error("Could not generate checklist");
    } finally {
      setBusy(false);
    }
  };

  const handleTaskComplete = async (taskId) => {
    try {
      const { data } = await api.post(`/hr/onboarding-tasks/${taskId}/complete`, {
        completed_by: user?.name || "HR User"
      });
      toast.success("Task verified and logged to audit trail");
      if (selectedEmp) loadOnboarding(selectedEmp.id);
    } catch (e) {
      toast.error("Failed to mark task complete");
    }
  };

  return (
    <div className="max-w-6xl mx-auto" data-testid="hr-onboarding-page">
      <PageHeader
        kicker="HR Automation Module"
        title="Employee Onboarding & Compliance"
        subtitle="When new hires are added, the Onboarding Agent auto-creates department-specific training plans (Sales, Warehouse, Finance), tracks completion percentage, and audits checkpoints."
      />

      <div className="grid grid-cols-12 gap-6">
        {/* Left Column: Register & Employee List */}
        <div className="col-span-12 lg:col-span-5 space-y-6">
          {/* Register Card */}
          <div className="rounded-2xl border border-border bg-card card-soft p-6">
            <h3 className="text-sm font-semibold flex items-center gap-2 mb-4">
              <UserPlus className="h-4 w-4 text-indigo-600" /> Onboard New Employee
            </h3>
            <form onSubmit={handleRegister} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Full Name</label>
                <Input placeholder="e.g., Priya Patel" value={name} onChange={(e) => setName(e.target.value)} className="mt-1 text-sm" />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Email Address</label>
                <Input placeholder="priya@pharma.bi" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1 text-sm" />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Job Title</label>
                  <Input placeholder="Territory Mgr" value={role} onChange={(e) => setRole(e.target.value)} className="mt-1 text-sm" />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Department</label>
                  <Select value={dept} onValueChange={setDept}>
                    <SelectTrigger className="mt-1 text-sm"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Sales">Sales</SelectItem>
                      <SelectItem value="Warehouse">Warehouse</SelectItem>
                      <SelectItem value="Finance">Finance</SelectItem>
                      <SelectItem value="Operations">Operations</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <Button type="submit" disabled={busy} className="w-full mt-2 gap-2 rounded-full">
                <Sparkles className="h-4 w-4" /> Start AI Onboarding
              </Button>
            </form>
          </div>

          {/* Active Employees List */}
          <div className="rounded-2xl border border-border bg-card p-5">
            <h3 className="text-sm font-semibold mb-3">Active Onboardings</h3>
            {employees.length === 0 ? (
              <p className="text-xs text-muted-foreground">No active onboarding records.</p>
            ) : (
              <div className="space-y-2">
                {employees.map((emp) => (
                  <div
                    key={emp.id}
                    onClick={() => { setSelectedEmp(emp); loadOnboarding(emp.id); }}
                    className={`cursor-pointer rounded-xl border px-4 py-3 flex items-center justify-between transition-all ${
                      selectedEmp?.id === emp.id ? "border-foreground bg-secondary" : "border-border bg-card/50 hover:bg-card"
                    }`}
                  >
                    <div className="min-w-0">
                      <p className="font-medium text-[13px] truncate">{emp.name}</p>
                      <p className="mono text-[11px] text-muted-foreground">{emp.role} · {emp.department}</p>
                    </div>
                    <StatusBadge status={emp.onboarding_status || "in_progress"} />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Interactive Checklist */}
        <div className="col-span-12 lg:col-span-7">
          <div className="rounded-2xl border border-border bg-card card-soft p-7 min-h-[500px]">
            {!selectedEmp ? (
              <EmptyState title="No Employee Selected" subtitle="Select an employee from the list on the left to view their onboarding trajectory." />
            ) : (
              <div>
                <div className="flex items-start justify-between pb-5 border-b border-border">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-lg font-semibold tracking-tight">{selectedEmp.name}</h2>
                      <span className="mono text-[11px] bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-full px-2.5 py-0.5 font-medium flex items-center gap-1">
                        <Building2 className="h-3 w-3" /> {selectedEmp.department}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">{selectedEmp.role} · {selectedEmp.email}</p>
                  </div>
                  <div className="text-right">
                    <p className="mono text-[10px] uppercase tracking-wider text-muted-foreground">Completion</p>
                    <p className="text-2xl font-bold font-mono mt-0.5">
                      {onboarding?.progress !== undefined ? Math.round(onboarding.progress) : 0}%
                    </p>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mt-5 h-2.5 rounded-full bg-secondary overflow-hidden border border-border/50">
                  <div
                    className="h-full rounded-full bg-indigo-600 transition-all duration-500 ease-out"
                    style={{ width: `${onboarding?.progress || 0}%` }}
                  />
                </div>

                {/* Tasks Header */}
                <div className="mt-8 flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold flex items-center gap-2">
                    <ClipboardCheck className="h-4 w-4 text-indigo-600" /> Department Action Plan
                  </h3>
                  {!onboarding && (
                    <Button size="sm" onClick={() => triggerOnboarding(selectedEmp.id)} className="rounded-full text-xs">
                      Generate AI Checklist
                    </Button>
                  )}
                </div>

                {!onboarding || !onboarding.tasks || onboarding.tasks.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground text-sm">
                    No onboarding checklist generated yet. Click above to trigger the Onboarding Agent.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {onboarding.tasks.map((task) => (
                      <div
                        key={task.id}
                        onClick={() => { if (task.status !== "completed") handleTaskComplete(task.id); }}
                        className={`group rounded-xl border p-4 transition-all flex items-start gap-4 ${
                          task.status === "completed"
                            ? "bg-secondary/40 border-border/40 opacity-70"
                            : "bg-card border-border hover:border-indigo-500/50 cursor-pointer shadow-2xs"
                        }`}
                      >
                        <div className="mt-0.5 shrink-0">
                          {task.status === "completed" ? (
                            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                          ) : (
                            <Circle className="h-5 w-5 text-muted-foreground group-hover:text-indigo-600 transition-colors" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <p className={`text-sm font-medium ${task.status === "completed" ? "line-through text-muted-foreground" : "text-foreground"}`}>
                              {task.title}
                            </p>
                            <span className="mono text-[10px] text-muted-foreground bg-secondary px-2 py-0.5 rounded-full uppercase">
                              {task.category || "General"}
                            </span>
                          </div>
                          {task.description && (
                            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{task.description}</p>
                          )}
                          <div className="flex items-center gap-3 mt-2 text-[11px] text-muted-foreground font-mono">
                            <span>Assignee: {task.assignee || "HR Agent"}</span>
                            <span>Due: {task.due_days_after ? `+${task.due_days_after}d` : "Immediate"}</span>
                            {task.completed_at && <span className="text-emerald-700 font-medium">Completed ✓</span>}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
