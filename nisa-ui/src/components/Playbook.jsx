import { useState, useEffect, useRef } from "react"
import { pushContext } from "../SessionContext"
import api, { NISA_API_KEY } from "../api"
import { Play, Plus, Trash2, Edit2, Save, X, ChevronUp, ChevronDown, CheckCircle, AlertTriangle, Clock, SkipForward, Loader } from "lucide-react"

const PB_API = "http://localhost:8096"

const OPERATIONS = [
  { value: "nmap_scan",         label: "Nmap Scan",            params: ["target", "scan_type"] },
  { value: "zap_scan",          label: "ZAP Web Scan",         params: ["target"] },
  { value: "adversarial_sim",   label: "Adversarial Simulation", params: ["threat_actor", "network_context"] },
  { value: "nisaba_query",      label: "Nisaba Query",         params: ["message"] },
  { value: "cve_lookup",        label: "CVE Lookup",           params: ["query"] },
  { value: "compliance_report", label: "Compliance Report",    params: [] },
  { value: "suricata_check",    label: "Suricata IDS Check",   params: [] },
  { value: "log_analysis",      label: "Log Analysis",         params: ["log_type"] },
]

const CONDITIONS = [
  { value: "always",     label: "Always run" },
  { value: "on_success", label: "Run if previous succeeded" },
  { value: "on_finding", label: "Run if previous found issues" },
]

const SCAN_TYPES = ["quick", "standard", "full", "vulnerability", "stealth"]
const THREAT_ACTORS = ["APT28", "APT29", "Lazarus", "APT41", "FIN7", "Ransomware", "Insider", "Custom"]

const uid = () => Math.random().toString(36).slice(2, 8)

const statusColor = (s) => ({
  success: "var(--success)",
  error: "var(--danger)",
  skipped: "var(--text-dim)",
  running: "var(--accent-gold)",
  completed: "var(--success)",
  completed_with_errors: "var(--warning, #f59e0b)",
})[s] || "var(--text-dim)"

const statusIcon = (s) => {
  if (s === "success" || s === "completed") return <CheckCircle size={14} color="var(--success)" />
  if (s === "error" || s === "completed_with_errors") return <AlertTriangle size={14} color="var(--danger)" />
  if (s === "skipped") return <SkipForward size={14} color="var(--text-dim)" />
  if (s === "running") return <Loader size={14} color="var(--accent-gold)" className="spin" />
  return <Clock size={14} color="var(--text-dim)" />
}

export default function Playbook() {
  const [playbooks, setPlaybooks] = useState([])
  const [selected, setSelected] = useState(null)
  const [editing, setEditing] = useState(false)
  const [editData, setEditData] = useState(null)
  const [running, setRunning] = useState(false)
  const [runResult, setRunResult] = useState(null)
  const [error, setError] = useState("")
  const [creating, setCreating] = useState(false)

  useEffect(() => { fetchPlaybooks() }, [])

  const fetchPlaybooks = async () => {
    try {
      const res = await api.get(`${PB_API}/playbooks`)
      setPlaybooks(res.data.playbooks || [])
    } catch(e) { setError("Failed to load playbooks") }
  }

  const selectPlaybook = (pb) => {
    setSelected(pb)
    setEditing(false)
    setRunResult(null)
    setError("")
  }

  const startCreate = () => {
    setEditData({
      name: "New Playbook",
      description: "",
      steps: []
    })
    setCreating(true)
    setEditing(true)
    setSelected(null)
    setRunResult(null)
  }

  const startEdit = () => {
    setEditData({
      name: selected.name,
      description: selected.description || "",
      steps: typeof selected.steps === "string" ? JSON.parse(selected.steps) : selected.steps
    })
    setEditing(true)
    setCreating(false)
  }

  const cancelEdit = () => {
    setEditing(false)
    setCreating(false)
    setEditData(null)
  }

  const savePlaybook = async () => {
    try {
      if (creating) {
        const res = await api.post(`${PB_API}/playbooks`, editData)
        await fetchPlaybooks()
        setCreating(false)
        setEditing(false)
        setEditData(null)
      } else {
        await api.put(`${PB_API}/playbooks/${selected.id}`, editData)
        await fetchPlaybooks()
        setEditing(false)
        setEditData(null)
      }
    } catch(e) { setError("Save failed: " + e.message) }
  }

  const deletePlaybook = async (id) => {
    if (!window.confirm("Delete this playbook?")) return
    try {
      await api.delete(`${PB_API}/playbooks/${id}`)
      setSelected(null)
      await fetchPlaybooks()
    } catch(e) { setError("Delete failed") }
  }

  const runPlaybook = async () => {
    if (!selected) return
    setRunning(true)
    setRunResult(null)
    setError("")
    try {
      const res = await api.post(`${PB_API}/playbooks/${selected.id}/run`)
      setRunResult(res.data)
      pushContext({
        tab: "Playbook",
        operation: `Playbook: ${selected.name}`,
        summary: `Playbook "${selected.name}" complete - ${res.data.steps_success}/${res.data.steps_total} steps succeeded. Status: ${res.data.status}`,
        detail: null
      })
      await fetchPlaybooks()
    } catch(e) { setError("Run failed: " + e.message) }
    setRunning(false)
  }

  return (
    <div style={{ display: "flex", gap: "20px", height: "calc(100vh - 120px)" }}>
      {/* ── Left Panel: Playbook Library ── */}
      <div style={{
        width: "260px", flexShrink: 0,
        background: "var(--bg-secondary)",
        border: "1px solid var(--border)",
        borderRadius: "4px",
        display: "flex", flexDirection: "column",
      }}>
        <div style={{
          padding: "14px 16px",
          borderBottom: "1px solid var(--border)",
          display: "flex", alignItems: "center", justifyContent: "space-between"
        }}>
          <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "13px", letterSpacing: "0.15em", color: "var(--accent-gold)" }}>
            PLAYBOOK LIBRARY
          </span>
          <button onClick={startCreate} style={{
            background: "transparent", border: "1px solid var(--accent-gold)",
            color: "var(--accent-gold)", borderRadius: "3px",
            padding: "3px 8px", cursor: "pointer", display: "flex", alignItems: "center", gap: "4px",
            fontFamily: "JetBrains Mono, monospace", fontSize: "10px"
          }}>
            <Plus size={10} /> NEW
          </button>
        </div>
        <div style={{ flex: 1, overflowY: "auto", padding: "8px" }}>
          {playbooks.length === 0 && (
            <div style={{ color: "var(--text-dim)", fontFamily: "JetBrains Mono, monospace", fontSize: "11px", padding: "12px", textAlign: "center" }}>
              No playbooks yet.<br />Click NEW to create one.
            </div>
          )}
          {playbooks.map(pb => (
            <div key={pb.id} onClick={() => selectPlaybook(pb)} style={{
              padding: "10px 12px", borderRadius: "3px", cursor: "pointer", marginBottom: "4px",
              background: selected?.id === pb.id ? "var(--accent-gold-glow)" : "transparent",
              border: selected?.id === pb.id ? "1px solid var(--accent-gold)" : "1px solid transparent",
              transition: "all 0.15s ease",
            }}>
              <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 600, fontSize: "13px", color: selected?.id === pb.id ? "var(--accent-gold)" : "var(--text-primary)" }}>
                {pb.name}
              </div>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", marginTop: "3px" }}>
                {(typeof pb.steps === "string" ? JSON.parse(pb.steps) : pb.steps).length} steps
                {pb.run_count > 0 && ` · ${pb.run_count} runs`}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Right Panel ── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "16px", overflowY: "auto" }}>
        {error && (
          <div style={{ background: "rgba(239,68,68,0.1)", border: "1px solid var(--danger)", borderRadius: "4px", padding: "10px 14px", color: "var(--danger)", fontFamily: "JetBrains Mono, monospace", fontSize: "11px" }}>
            {error}
          </div>
        )}

        {/* Editor */}
        {editing && editData && (
          <PlaybookEditor
            data={editData}
            onChange={setEditData}
            onSave={savePlaybook}
            onCancel={cancelEdit}
            creating={creating}
          />
        )}

        {/* Viewer */}
        {!editing && selected && (
          <>
            <PlaybookViewer
              pb={selected}
              onEdit={startEdit}
              onDelete={() => deletePlaybook(selected.id)}
              onRun={runPlaybook}
              running={running}
            />
            {runResult && <RunResults result={runResult} />}
          </>
        )}

        {/* Empty state */}
        {!editing && !selected && (
          <div style={{
            flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
            color: "var(--text-dim)", gap: "12px"
          }}>
            <Play size={40} color="var(--text-dim)" />
            <div style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "16px", letterSpacing: "0.1em" }}>SELECT A PLAYBOOK OR CREATE ONE</div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px" }}>Automated response workflows for NISA operations</div>
          </div>
        )}
      </div>
    </div>
  )
}

function PlaybookViewer({ pb, onEdit, onDelete, onRun, running }) {
  const steps = typeof pb.steps === "string" ? JSON.parse(pb.steps) : pb.steps
  return (
    <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "4px" }}>
      <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "20px", letterSpacing: "0.1em", color: "var(--text-primary)" }}>{pb.name}</div>
          {pb.description && <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "12px", color: "var(--text-dim)", marginTop: "4px" }}>{pb.description}</div>}
          <div style={{ display: "flex", gap: "16px", marginTop: "8px" }}>
            <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)" }}>{steps.length} STEPS</span>
            <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)" }}>{pb.run_count} RUNS</span>
            {pb.last_run && <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)" }}>LAST: {new Date(pb.last_run).toLocaleDateString()}</span>}
          </div>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <button onClick={onEdit} style={iconBtn("var(--accent-cyan, #00d4ff)")}><Edit2 size={13} /></button>
          <button onClick={onDelete} style={iconBtn("var(--danger)")}><Trash2 size={13} /></button>
          <button onClick={onRun} disabled={running || steps.length === 0} style={{
            background: running ? "transparent" : "var(--accent-gold)",
            border: "1px solid var(--accent-gold)",
            color: running ? "var(--accent-gold)" : "var(--bg-primary)",
            borderRadius: "3px", padding: "7px 16px", cursor: running ? "not-allowed" : "pointer",
            fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "13px", letterSpacing: "0.1em",
            display: "flex", alignItems: "center", gap: "6px"
          }}>
            {running ? <><Loader size={13} /> RUNNING...</> : <><Play size={13} /> RUN PLAYBOOK</>}
          </button>
        </div>
      </div>
      <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: "8px" }}>
        {steps.map((step, i) => (
          <StepCard key={step.id} step={step} index={i} readonly />
        ))}
        {steps.length === 0 && (
          <div style={{ color: "var(--text-dim)", fontFamily: "JetBrains Mono, monospace", fontSize: "11px", padding: "8px" }}>No steps defined. Click edit to add steps.</div>
        )}
      </div>
    </div>
  )
}

function PlaybookEditor({ data, onChange, onSave, onCancel, creating }) {
  const addStep = () => {
    const newStep = { id: uid(), name: "New Step", operation: "nmap_scan", params: { target: "127.0.0.1", scan_type: "quick" }, condition: data.steps.length === 0 ? "always" : "on_finding" }
    onChange({ ...data, steps: [...data.steps, newStep] })
  }

  const updateStep = (idx, updated) => {
    const steps = [...data.steps]
    steps[idx] = updated
    onChange({ ...data, steps })
  }

  const removeStep = (idx) => {
    onChange({ ...data, steps: data.steps.filter((_, i) => i !== idx) })
  }

  const moveStep = (idx, dir) => {
    const steps = [...data.steps]
    const target = idx + dir
    if (target < 0 || target >= steps.length) return
    ;[steps[idx], steps[target]] = [steps[target], steps[idx]]
    onChange({ ...data, steps })
  }

  return (
    <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--accent-gold)", borderRadius: "4px" }}>
      <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "14px", letterSpacing: "0.15em", color: "var(--accent-gold)" }}>
          {creating ? "CREATE PLAYBOOK" : "EDIT PLAYBOOK"}
        </span>
        <div style={{ display: "flex", gap: "8px" }}>
          <button onClick={onCancel} style={iconBtn("var(--text-dim)")}><X size={13} /></button>
          <button onClick={onSave} style={{
            background: "var(--accent-gold)", border: "none", color: "var(--bg-primary)",
            borderRadius: "3px", padding: "6px 14px", cursor: "pointer",
            fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px", letterSpacing: "0.1em",
            display: "flex", alignItems: "center", gap: "5px"
          }}><Save size={12} /> SAVE</button>
        </div>
      </div>
      <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: "14px" }}>
        <div style={{ display: "flex", gap: "12px" }}>
          <div style={{ flex: 1 }}>
            <FieldLabel>NAME</FieldLabel>
            <input value={data.name} onChange={e => onChange({ ...data, name: e.target.value })} style={inputStyle} />
          </div>
        </div>
        <div>
          <FieldLabel>DESCRIPTION</FieldLabel>
          <input value={data.description} onChange={e => onChange({ ...data, description: e.target.value })} style={inputStyle} placeholder="Optional description..." />
        </div>
        <div style={{ borderTop: "1px solid var(--border)", paddingTop: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
            <FieldLabel>STEPS ({data.steps.length})</FieldLabel>
            <button onClick={addStep} style={{
              background: "transparent", border: "1px solid var(--border)", color: "var(--text-secondary)",
              borderRadius: "3px", padding: "4px 10px", cursor: "pointer",
              fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
              display: "flex", alignItems: "center", gap: "4px"
            }}><Plus size={10} /> ADD STEP</button>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {data.steps.map((step, i) => (
              <StepCard key={step.id} step={step} index={i}
                onUpdate={(u) => updateStep(i, u)}
                onRemove={() => removeStep(i)}
                onMoveUp={() => moveStep(i, -1)}
                onMoveDown={() => moveStep(i, 1)}
                isFirst={i === 0} isLast={i === data.steps.length - 1}
              />
            ))}
            {data.steps.length === 0 && (
              <div style={{ color: "var(--text-dim)", fontFamily: "JetBrains Mono, monospace", fontSize: "11px", padding: "12px", textAlign: "center", border: "1px dashed var(--border)", borderRadius: "3px" }}>
                No steps yet. Click ADD STEP to begin.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function StepCard({ step, index, readonly, onUpdate, onRemove, onMoveUp, onMoveDown, isFirst, isLast, liveStatus }) {
  const op = OPERATIONS.find(o => o.value === step.operation) || { label: step.operation, params: [] }

  const updateParam = (key, val) => {
    onUpdate({ ...step, params: { ...step.params, [key]: val } })
  }

  return (
    <div style={{
      border: `1px solid ${liveStatus ? statusColor(liveStatus) : "var(--border)"}`,
      borderRadius: "4px", background: "var(--bg-primary)", overflow: "hidden"
    }}>
      <div style={{
        padding: "10px 14px", display: "flex", alignItems: "center", gap: "10px",
        background: liveStatus ? `${statusColor(liveStatus)}11` : "transparent"
      }}>
        <div style={{
          width: "22px", height: "22px", borderRadius: "50%",
          background: "var(--bg-secondary)", border: "1px solid var(--border)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)", flexShrink: 0
        }}>{index + 1}</div>

        {readonly ? (
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 600, fontSize: "13px", color: "var(--text-primary)" }}>{step.name}</div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)" }}>
              {op.label} · {CONDITIONS.find(c => c.value === step.condition)?.label || step.condition}
            </div>
          </div>
        ) : (
          <div style={{ flex: 1, display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
            <input value={step.name} onChange={e => onUpdate({ ...step, name: e.target.value })}
              style={{ ...inputStyle, flex: 1, minWidth: "120px", padding: "4px 8px", fontSize: "12px" }} />
            <select value={step.operation} onChange={e => onUpdate({ ...step, operation: e.target.value, params: {} })}
              style={{ ...inputStyle, padding: "4px 8px", fontSize: "11px" }}>
              {OPERATIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <select value={step.condition} onChange={e => onUpdate({ ...step, condition: e.target.value })}
              style={{ ...inputStyle, padding: "4px 8px", fontSize: "11px" }}>
              {CONDITIONS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>
        )}

        {liveStatus && <div style={{ marginLeft: "auto" }}>{statusIcon(liveStatus)}</div>}

        {!readonly && (
          <div style={{ display: "flex", gap: "4px", marginLeft: "auto" }}>
            <button onClick={onMoveUp} disabled={isFirst} style={iconBtn("var(--text-dim)", isFirst)}><ChevronUp size={12} /></button>
            <button onClick={onMoveDown} disabled={isLast} style={iconBtn("var(--text-dim)", isLast)}><ChevronDown size={12} /></button>
            <button onClick={onRemove} style={iconBtn("var(--danger)")}><Trash2 size={12} /></button>
          </div>
        )}
      </div>

      {/* Params — editor only */}
      {!readonly && step.operation === "nmap_scan" && (
        <div style={{ padding: "8px 14px 12px 46px", display: "flex", gap: "8px", borderTop: "1px solid var(--border)" }}>
          <div><FieldLabel>TARGET</FieldLabel>
            <input value={step.params.target || ""} onChange={e => updateParam("target", e.target.value)} style={{ ...inputStyle, padding: "4px 8px", fontSize: "11px", width: "150px" }} /></div>
          <div><FieldLabel>SCAN TYPE</FieldLabel>
            <select value={step.params.scan_type || "quick"} onChange={e => updateParam("scan_type", e.target.value)} style={{ ...inputStyle, padding: "4px 8px", fontSize: "11px" }}>
              {SCAN_TYPES.map(s => <option key={s} value={s}>{s}</option>)}
            </select></div>
        </div>
      )}
      {!readonly && step.operation === "zap_scan" && (
        <div style={{ padding: "8px 14px 12px 46px", borderTop: "1px solid var(--border)" }}>
          <FieldLabel>TARGET URL</FieldLabel>
          <input value={step.params.target || ""} onChange={e => updateParam("target", e.target.value)} style={{ ...inputStyle, padding: "4px 8px", fontSize: "11px", width: "250px" }} />
        </div>
      )}
      {!readonly && step.operation === "adversarial_sim" && (
        <div style={{ padding: "8px 14px 12px 46px", display: "flex", gap: "8px", borderTop: "1px solid var(--border)" }}>
          <div><FieldLabel>THREAT ACTOR</FieldLabel>
            <select value={step.params.threat_actor || "APT28"} onChange={e => updateParam("threat_actor", e.target.value)} style={{ ...inputStyle, padding: "4px 8px", fontSize: "11px" }}>
              {THREAT_ACTORS.map(t => <option key={t} value={t}>{t}</option>)}
            </select></div>
          <div><FieldLabel>NETWORK CONTEXT</FieldLabel>
            <input value={step.params.network_context || "enterprise"} onChange={e => updateParam("network_context", e.target.value)} style={{ ...inputStyle, padding: "4px 8px", fontSize: "11px", width: "150px" }} /></div>
        </div>
      )}
      {!readonly && step.operation === "nisaba_query" && (
        <div style={{ padding: "8px 14px 12px 46px", borderTop: "1px solid var(--border)" }}>
          <FieldLabel>QUERY</FieldLabel>
          <input value={step.params.message || ""} onChange={e => updateParam("message", e.target.value)} style={{ ...inputStyle, padding: "4px 8px", fontSize: "11px", width: "100%" }} placeholder="Ask Nisaba something..." />
        </div>
      )}
      {!readonly && step.operation === "cve_lookup" && (
        <div style={{ padding: "8px 14px 12px 46px", borderTop: "1px solid var(--border)" }}>
          <FieldLabel>CVE QUERY</FieldLabel>
          <input value={step.params.query || ""} onChange={e => updateParam("query", e.target.value)} style={{ ...inputStyle, padding: "4px 8px", fontSize: "11px", width: "200px" }} placeholder="e.g. RDP exploit" />
        </div>
      )}
      {!readonly && step.operation === "log_analysis" && (
        <div style={{ padding: "8px 14px 12px 46px", borderTop: "1px solid var(--border)" }}>
          <FieldLabel>LOG TYPE</FieldLabel>
          <select value={step.params.log_type || "syslog"} onChange={e => updateParam("log_type", e.target.value)} style={{ ...inputStyle, padding: "4px 8px", fontSize: "11px" }}>
            {["syslog","auth","apache","nginx","windows","custom"].map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      )}

      {/* Live result summary */}
      {liveStatus && step.summary && (
        <div style={{ padding: "6px 14px 8px 46px", borderTop: "1px solid var(--border)", fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: statusColor(liveStatus) }}>
          {step.summary}
        </div>
      )}
    </div>
  )
}

function RunResults({ result }) {
  const steps = result.step_results || []
  return (
    <div style={{ background: "var(--bg-secondary)", border: `1px solid ${statusColor(result.status)}`, borderRadius: "4px" }}>
      <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {statusIcon(result.status)}
          <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "14px", letterSpacing: "0.15em", color: statusColor(result.status) }}>
            {result.status === "completed" ? "PLAYBOOK COMPLETE" : "COMPLETED WITH ERRORS"}
          </span>
        </div>
        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: "var(--text-dim)" }}>
          {result.steps_success}/{result.steps_total} steps succeeded
        </span>
      </div>
      <div style={{ padding: "14px 20px", display: "flex", flexDirection: "column", gap: "8px" }}>
        {steps.map((step, i) => (
          <StepCard key={step.step_id || i} step={step} index={i} readonly liveStatus={step.status} />
        ))}
      </div>
    </div>
  )
}

const inputStyle = {
  background: "var(--bg-primary)", border: "1px solid var(--border)", borderRadius: "3px",
  color: "var(--text-primary)", fontFamily: "JetBrains Mono, monospace", fontSize: "12px",
  padding: "7px 10px", width: "100%", outline: "none", boxSizing: "border-box"
}

const iconBtn = (color, disabled = false) => ({
  background: "transparent", border: `1px solid ${disabled ? "var(--border)" : color}`,
  color: disabled ? "var(--text-dim)" : color, borderRadius: "3px",
  padding: "5px 7px", cursor: disabled ? "not-allowed" : "pointer",
  display: "flex", alignItems: "center", justifyContent: "center", opacity: disabled ? 0.4 : 1
})

function FieldLabel({ children }) {
  return <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", letterSpacing: "0.15em", marginBottom: "4px" }}>{children}</div>
}
