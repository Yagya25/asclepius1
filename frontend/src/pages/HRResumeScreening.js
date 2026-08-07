import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "@/lib/api";
import { PageHeader, StatusBadge, EmptyState } from "@/components/bits";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { UploadCloud, FileSpreadsheet, Sparkles, UserCheck, Plus, ArrowUpRight, X } from "lucide-react";
import { toast } from "sonner";

export default function HRResumeScreening() {
  const [jds, setJds] = useState([]);
  const [selectedJd, setSelectedJd] = useState(null);
  const [results, setResults] = useState(null);
  const [busy, setBusy] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef();

  // JD Builder State
  const [showForm, setShowForm] = useState(false);
  const [newJdTitle, setNewJdTitle] = useState("");
  const [newJdDept, setNewJdDept] = useState("Sales");
  const [newJdExp, setNewJdExp] = useState(0);
  const [newJdDesc, setNewJdDesc] = useState("");
  const [newJdSkills, setNewJdSkills] = useState([]);
  const [skillInput, setSkillInput] = useState("");

  const loadJds = useCallback(async () => {
    try {
      const { data } = await api.get("/hr/job-descriptions");
      setJds(data);
      if (data.length > 0 && !selectedJd) setSelectedJd(data[0]);
    } catch (e) {
      toast.error("Could not load job descriptions");
    }
  }, [selectedJd]);

  useEffect(() => { loadJds(); }, [loadJds]);

  const createSampleJd = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/hr/job-descriptions", {
        title: "Senior Pharma Sales Rep",
        department: "Sales & Territory",
        required_skills: ["pharma sales", "hospital distribution", "b2b relationship", "regulatory knowledge"],
        min_experience_years: 3,
        description: "Seeking experienced sales executive for retail pharmacy and hospital distribution networks."
      });
      toast.success("Job Description created successfully");
      setJds((prev) => [data, ...prev]);
      setSelectedJd(data);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || "Failed to create JD");
    } finally {
      setBusy(false);
    }
  };
  const submitNewJd = async (e) => {
    e.preventDefault();
    if (!newJdTitle || newJdSkills.length === 0) return toast.error("Title and at least one skill are required");
    setBusy(true);
    try {
      const { data } = await api.post("/hr/job-descriptions", {
        title: newJdTitle,
        department: newJdDept,
        required_skills: newJdSkills,
        min_experience_years: parseInt(newJdExp, 10) || 0,
        description: newJdDesc
      });
      toast.success("Job Description created successfully");
      setJds((prev) => [data, ...prev]);
      setSelectedJd(data);
      setShowForm(false);
      // Reset form
      setNewJdTitle(""); setNewJdExp(0); setNewJdDesc(""); setNewJdSkills([]);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || "Failed to create JD");
    } finally {
      setBusy(false);
    }
  };

  const handleAddSkill = (e) => {
    if (e.key === "Enter" && skillInput.trim()) {
      e.preventDefault();
      if (!newJdSkills.includes(skillInput.trim())) {
        setNewJdSkills([...newJdSkills, skillInput.trim()]);
      }
      setSkillInput("");
    }
  };

  const removeSkill = (skill) => {
    setNewJdSkills(newJdSkills.filter(s => s !== skill));
  };
  const handleFileUpload = async (file) => {
    if (!file || !selectedJd) {
      if (!selectedJd) toast.error("Please select or create a Job Description first");
      return;
    }
    setBusy(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const { data: summary } = await api.post(`/hr/screen-resumes?jd_id=${selectedJd.id}`, fd);
      const { data: resultsData } = await api.get(`/hr/screenings/${summary.dataset_id}/results`);
      resultsData.job_title = selectedJd.title;
      toast.success(`Screening Complete: ${resultsData.total_candidates} resumes analyzed!`);
      setResults(resultsData);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail) || "Resume screening failed");
    } finally {
      setBusy(false);
    }
  };

  const getFitStyle = (score) => {
    if (score >= 80) return "text-emerald-700 bg-emerald-50 border-emerald-200";
    if (score >= 60) return "text-amber-700 bg-amber-50 border-amber-200";
    return "text-red-700 bg-red-50 border-red-200";
  };

  return (
    <div className="max-w-5xl mx-auto" data-testid="hr-screening-page">
      <PageHeader
        kicker="HR Automation Module"
        title="AI Resume Screening & Shortlisting"
        subtitle="Upload candidate CSV archives against job descriptions. The screening agent extracts domain skills, calculates deterministic fit scores, and cues human manager approval."
      />

      {/* JD Selection Row */}
      <div className="mb-8 rounded-2xl border border-border bg-card card-soft p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <UserCheck className="h-4 w-4 text-indigo-600" /> Target Job Description
            </h3>
            <p className="text-xs text-muted-foreground">Select the position criteria to match candidates against</p>
          </div>
          <div className="flex gap-2">
            <Button size="sm" onClick={() => setShowForm(!showForm)} variant={showForm ? "secondary" : "default"} className="text-xs gap-1.5 rounded-full">
              {showForm ? <X className="h-3.5 w-3.5" /> : <Plus className="h-3.5 w-3.5" />}
              {showForm ? "Cancel" : "Add Job Description"}
            </Button>
            <Button size="sm" onClick={createSampleJd} disabled={busy} variant="outline" className="text-xs gap-1.5 rounded-full">
              <Sparkles className="h-3.5 w-3.5" /> New Sample JD
            </Button>
          </div>
        </div>

        {showForm && (
          <form onSubmit={submitNewJd} className="mb-6 p-5 rounded-xl border border-border bg-secondary/20 space-y-4 rise-in">
            <h4 className="text-sm font-semibold mb-1">Create Job Description</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <label className="text-xs font-medium text-muted-foreground">Job Title</label>
                <Input placeholder="e.g. Clinical Research Associate" value={newJdTitle} onChange={(e) => setNewJdTitle(e.target.value)} className="mt-1 text-sm h-9" />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Department</label>
                <Select value={newJdDept} onValueChange={setNewJdDept}>
                  <SelectTrigger className="mt-1 text-sm h-9"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Sales">Sales</SelectItem>
                    <SelectItem value="Warehouse">Warehouse</SelectItem>
                    <SelectItem value="Finance">Finance</SelectItem>
                    <SelectItem value="Operations">Operations</SelectItem>
                    <SelectItem value="R&D">R&D</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="md:col-span-3">
                <label className="text-xs font-medium text-muted-foreground">Required Skills (Type and press Enter)</label>
                <div className="mt-1 rounded-md border border-input bg-transparent px-3 py-1 flex flex-wrap gap-2 items-center min-h-9 focus-within:ring-1 focus-within:ring-ring">
                  {newJdSkills.map((sk) => (
                    <span key={sk} className="flex items-center gap-1 bg-secondary text-secondary-foreground px-2 py-0.5 rounded text-xs">
                      {sk} <X className="h-3 w-3 cursor-pointer opacity-70 hover:opacity-100" onClick={() => removeSkill(sk)} />
                    </span>
                  ))}
                  <input
                    type="text"
                    value={skillInput}
                    onChange={(e) => setSkillInput(e.target.value)}
                    onKeyDown={handleAddSkill}
                    placeholder={newJdSkills.length === 0 ? "e.g. territory management..." : ""}
                    className="flex-1 bg-transparent outline-none min-w-[120px] text-sm h-7"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Min. Experience (Years)</label>
                <Input type="number" min="0" value={newJdExp} onChange={(e) => setNewJdExp(e.target.value)} className="mt-1 text-sm h-9" />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground">Description (Optional)</label>
              <textarea 
                placeholder="Brief role summary..." 
                value={newJdDesc} 
                onChange={(e) => setNewJdDesc(e.target.value)} 
                className="mt-1 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring min-h-[60px]" 
              />
            </div>
            <div className="flex justify-end pt-2">
              <Button type="submit" disabled={busy || !newJdTitle || newJdSkills.length === 0} className="rounded-full text-xs h-8 px-4">
                Save Job Description
              </Button>
            </div>
          </form>
        )}

        {jds.length === 0 ? (
          <EmptyState title="No Job Descriptions found" subtitle="Click 'New Sample JD' above to generate a pharmaceutical sales position." />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {jds.map((jd) => (
              <div
                key={jd.id}
                onClick={() => { setSelectedJd(jd); setResults(null); }}
                className={`cursor-pointer rounded-xl border p-4 transition-all ${
                  selectedJd?.id === jd.id ? "border-foreground bg-secondary/80 shadow-sm" : "border-border bg-card hover:bg-accent/40"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[13px] truncate">{jd.title}</span>
                  <StatusBadge status={selectedJd?.id === jd.id ? "active" : "inactive"} />
                </div>
                <p className="mono text-[11px] text-muted-foreground mt-1">{jd.department} · {jd.min_years_exp}yr+ exp</p>
                <div className="flex flex-wrap gap-1 mt-2.5">
                  {(jd.required_skills || []).slice(0, 3).map((sk, i) => (
                    <span key={i} className="mono text-[10px] rounded px-1.5 py-0.5 bg-background border border-border text-muted-foreground">
                      {sk}
                    </span>
                  ))}
                  {(jd.required_skills?.length || 0) > 3 && <span className="mono text-[10px] px-1 text-muted-foreground">+{jd.required_skills.length - 3}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upload Dropzone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFileUpload(e.dataTransfer.files[0]); }}
        onClick={() => fileRef.current?.click()}
        className={`cursor-pointer rounded-2xl border-2 border-dashed p-10 text-center transition-all ${
          dragOver ? "border-indigo-500 bg-indigo-50/20" : "border-border bg-card/50 hover:border-indigo-400"
        }`}
      >
        <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={(e) => handleFileUpload(e.target.files[0])} />
        <UploadCloud className={`mx-auto h-10 w-10 mb-3 ${dragOver ? "text-indigo-600" : "text-muted-foreground"}`} />
        <p className="text-sm font-medium">{busy ? "AI Agent screening resumes…" : "Drop candidate resumes CSV here, or click to browse"}</p>
        <p className="mt-1 mono text-xs text-muted-foreground">Requires columns: Name, Email, Experience, Skills, Education</p>
      </div>

      {/* Screening Results Table */}
      {results && (
        <div className="mt-8 rounded-2xl border border-border bg-card card-soft overflow-hidden rise-in">
          <div className="px-6 py-5 border-b border-border flex items-center justify-between bg-secondary/30">
            <div>
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-indigo-600" /> Ranked Candidate Shortlist
              </h3>
              <p className="text-xs text-muted-foreground">Screening complete against {results.job_title}</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="mono text-xs text-muted-foreground">{results.total_candidates} candidates screened</span>
              <Link to="/app/approvals">
                <Button size="sm" className="rounded-full text-xs gap-1.5">
                  Go to Approval Center <ArrowUpRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  {["Rank", "Candidate", "Experience", "Matched Skills", "Fit Score", "Tier", "Action"].map((h) => (
                    <th key={h} className="px-5 py-3.5 mono text-[10px] uppercase tracking-[0.15em] text-muted-foreground font-semibold">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(results.candidates || []).map((c, i) => (
                  <tr key={c.email || i} className="border-b border-border/40 last:border-0 hover:bg-secondary/40 transition-colors">
                    <td className="px-5 py-3.5 mono font-semibold text-muted-foreground">#{i + 1}</td>
                    <td className="px-5 py-3.5">
                      <p className="font-medium text-[13px]">{c.name}</p>
                      <p className="mono text-[11px] text-muted-foreground">{c.email}</p>
                    </td>
                    <td className="px-5 py-3.5 mono text-xs">{c.experience_years || 0} yrs</td>
                    <td className="px-5 py-3.5">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {(c.matched_skills || c.skills || []).slice(0, 3).map((s, idx) => (
                          <span key={idx} className="mono text-[10px] px-2 py-0.5 rounded bg-indigo-50/50 text-indigo-700 border border-indigo-200/60">
                            {s}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className={`mono text-xs font-bold border rounded-full px-2.5 py-1 ${getFitStyle(c.fit_score)}`}>
                        {c.fit_score}%
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="mono text-[11px] uppercase tracking-wider text-muted-foreground font-medium">
                        {c.tier || (c.fit_score >= 80 ? "Strong Fit" : c.fit_score >= 60 ? "Moderate" : "Weak Fit")}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <Link to="/app/approvals">
                        <Button variant="ghost" size="sm" className="text-xs text-indigo-600 hover:text-indigo-700">
                          Review
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
