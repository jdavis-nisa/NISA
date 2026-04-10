import { useState, useEffect } from "react"
import { pushContext } from "../SessionContext"
import api from "../api"

const ADV_API = "http://localhost:8094"
const GOLD = "var(--accent-gold, #c9a84c)"
const BORDER = "var(--border, #1e2d4a)"
const BG2 = "var(--bg-secondary, #0d1526)"
const BG3 = "var(--bg-tertiary, #111827)"
const DIM = "var(--text-dim, #4a5568)"

const SEVERITY_COLORS = {
  CRITICAL: "#ff2244", HIGH: "#ff6600", MEDIUM: "#c9a84c", LOW: "#44aaff"
}

const PHASE_ICONS = {
  "Reconnaissance": "👁", "Resource Development": "🔧",
  "Initial Access": "🚪", "Execution": "⚡", "Persistence": "🔒",
  "Privilege Escalation": "⬆", "Defense Evasion": "🥷",
  "Credential Access": "🔑", "Discovery": "🔍", "Lateral Movement": "↔",
  "Collection": "📦", "Command and Control": "📡",
  "Exfiltration": "📤", "Impact": "💥"
}

export default function AdversarialSim() {
  const [actors, setActors] = useState([])
  const [selectedActor, setSelectedActor] = useState("apt28")
  const [target, setTarget] = useState("")
  const [networkContext, setNetworkContext] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState("")
  const [activeStep, setActiveStep] = useState(null)
  const [activeTab, setActiveTab] = useState("simulation")

  useEffect(() => {
    api.get(`${ADV_API}/threat_actors`).then(r => setActors(r.data.actors)).catch(() => {})
  }, [])

  const runSimulation = async () => {
    if (!target.trim()) { setError("Target description required"); return }
    setLoading(true); setError(""); setResult(null); setActiveStep(null)
    try {
      const res = await api.post(`${ADV_API}/simulate`, {
        target_description: target,
        threat_actor: selectedActor,
        network_context: networkContext,
        simulation_depth: "standard"
      })
      setResult(res.data)
      pushContext({ tab: 'Adversarial', operation: `${selectedActor} Kill Chain Simulation`, summary: `${selectedActor} simulation complete - ${res.data.steps?.length ?? 6} steps generated. ${res.data.coverage?.blind_spots ?? 0} blind spots identified.`, detail: null })
    } catch(e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  const selectedActorData = actors.find(a => a.id === selectedActor)

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "20px",
            fontWeight: 700, letterSpacing: "0.15em", color: GOLD, margin: 0 }}>
            ADVERSARIAL SIMULATION ENGINE
          </h2>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
            color: DIM, marginTop: "2px" }}>
            AI-Powered Red Team / Blue Team Kill Chain Generator
          </div>
        </div>
        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
          color: "#44ffaa", textAlign: "right" }}>
          <div>SIMULATION ONLY</div>
          <div style={{ color: DIM }}>No packets sent</div>
        </div>
      </div>

      <div style={{ background: BG2, border: `1px solid ${BORDER}`,
        borderRadius: "4px", padding: "12px", fontFamily: "JetBrains Mono, monospace",
        fontSize: "10px", color: DIM, lineHeight: 1.6 }}>
        AUTHORIZED USE ONLY — This tool generates threat models for defensive planning.
        No attacks are executed. Use only for systems you are authorized to assess.
      </div>

      {/* Tab switcher */}
      <div style={{ display: "flex", gap: "0", borderBottom: `1px solid ${BORDER}` }}>
        {[
          { key: "simulation", label: "KILL CHAIN SIMULATOR" },
          { key: "coverage", label: "ATT&CK COVERAGE MATRIX" },
        ].map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)} style={{
            background: "transparent", border: "none",
            borderBottom: activeTab === t.key ? `2px solid ${GOLD}` : "2px solid transparent",
            color: activeTab === t.key ? GOLD : DIM,
            padding: "8px 16px", cursor: "pointer",
            fontFamily: "Rajdhani, sans-serif", fontWeight: 700,
            fontSize: "12px", letterSpacing: "0.15em"
          }}>{t.label}</button>
        ))}
      </div>

      {activeTab === "coverage" && <CoverageMatrix lastResult={result} />}
      {activeTab === "simulation" && (
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
              color: DIM, letterSpacing: "0.1em", marginBottom: "6px" }}>
              TARGET ENVIRONMENT DESCRIPTION
            </div>
            <textarea value={target} onChange={e => setTarget(e.target.value)}
              placeholder="Describe the target environment...&#10;e.g. Windows Active Directory environment, 50 workstations, web server running Apache 2.4, PostgreSQL database, VPN gateway, no EDR deployed"
              rows={5}
              style={{ width: "100%", background: BG3, border: `1px solid ${BORDER}`,
                borderRadius: "4px", padding: "10px 12px",
                color: "var(--text-primary, #e2e8f0)",
                fontFamily: "JetBrains Mono, monospace", fontSize: "11px",
                outline: "none", resize: "vertical", boxSizing: "border-box",
                lineHeight: 1.6 }} />
          </div>
          <div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
              color: DIM, letterSpacing: "0.1em", marginBottom: "6px" }}>
              ADDITIONAL CONTEXT (optional)
            </div>
            <textarea value={networkContext} onChange={e => setNetworkContext(e.target.value)}
              placeholder="Security controls, compliance requirements, previous incidents..."
              rows={3}
              style={{ width: "100%", background: BG3, border: `1px solid ${BORDER}`,
                borderRadius: "4px", padding: "10px 12px",
                color: "var(--text-primary, #e2e8f0)",
                fontFamily: "JetBrains Mono, monospace", fontSize: "11px",
                outline: "none", resize: "vertical", boxSizing: "border-box" }} />
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
              color: DIM, letterSpacing: "0.1em", marginBottom: "6px" }}>
              THREAT ACTOR
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px" }}>
              {actors.map(a => (
                <div key={a.id} onClick={() => setSelectedActor(a.id)}
                  style={{
                    padding: "8px 10px", borderRadius: "4px", cursor: "pointer",
                    background: selectedActor === a.id ? a.color + "22" : BG3,
                    border: `1px solid ${selectedActor === a.id ? a.color : BORDER}`,
                    borderLeft: `3px solid ${a.color}`
                  }}>
                  <div style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "11px",
                    fontWeight: 600, color: selectedActor === a.id ? a.color : "var(--text-primary, #e2e8f0)" }}>
                    {a.name}
                  </div>
                  <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                    color: DIM, marginTop: "2px" }}>{a.targets}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <button onClick={runSimulation} disabled={loading || !target.trim()} style={{
        padding: "12px 24px", background: loading ? "transparent" : "var(--accent-gold-glow, #c9a84c22)",
        border: `1px solid ${loading ? DIM : GOLD}`, borderRadius: "4px",
        cursor: loading ? "not-allowed" : "pointer",
        fontFamily: "Rajdhani, sans-serif", fontWeight: 700,
        fontSize: "14px", letterSpacing: "0.2em",
        color: loading ? DIM : GOLD, width: "100%" }}>
        {loading ? "NISABA IS ANALYZING — GENERATING KILL CHAIN..." : "RUN ADVERSARIAL SIMULATION"}
      </button>

      {error && <div style={{ color: "var(--danger, #ff4444)",
        fontFamily: "JetBrains Mono, monospace", fontSize: "11px",
        background: "#ff222222", border: "1px solid #ff222244",
        borderRadius: "4px", padding: "10px" }}>{error}</div>}

      {result && <SimulationResults result={result} activeStep={activeStep} setActiveStep={setActiveStep} />}
      </div>
      )}
    </div>
  )
}

function SimulationResults({ result, activeStep, setActiveStep }) {
  const coverage = result.mitre_coverage || {}

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ background: BG2, border: `1px solid ${BORDER}`,
        borderRadius: "4px", padding: "16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start",
          marginBottom: "12px" }}>
          <div>
            <div style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "16px",
              fontWeight: 700, color: GOLD }}>{result.simulation_title}</div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
              color: DIM, marginTop: "4px" }}>{result.target_summary}</div>
          </div>
          <div style={{ padding: "4px 12px", borderRadius: "4px",
            background: (SEVERITY_COLORS[result.risk_level] || "#666") + "22",
            border: `1px solid ${SEVERITY_COLORS[result.risk_level] || "#666"}`,
            fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "13px",
            color: SEVERITY_COLORS[result.risk_level] || DIM }}>
            {result.risk_level}
          </div>
        </div>
        <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "12px",
          color: "var(--text-secondary, #8899bb)", lineHeight: 1.6,
          borderLeft: `3px solid ${GOLD}`, paddingLeft: "12px" }}>
          {result.executive_summary}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "8px" }}>
        {[
          { label: "DETECTED", value: coverage.detected || 0, color: "#44ffaa" },
          { label: "PARTIAL", value: coverage.partial || 0, color: GOLD },
          { label: "BLIND SPOTS", value: coverage.blind || 0, color: "#ff2244" },
        ].map(s => (
          <div key={s.label} style={{ background: BG2, border: `1px solid ${BORDER}`,
            borderRadius: "4px", padding: "12px", textAlign: "center" }}>
            <div style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "28px",
              fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
              color: DIM, letterSpacing: "0.1em" }}>{s.label}</div>
          </div>
        ))}
      </div>

      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
        color: DIM, letterSpacing: "0.1em" }}>
        KILL CHAIN — Click any step to expand
      </div>

      {(result.kill_chain || []).map((step, i) => (
        <div key={i} onClick={() => setActiveStep(activeStep === i ? null : i)}
          style={{
            background: activeStep === i ? BG2 : BG3,
            border: `1px solid ${activeStep === i ? SEVERITY_COLORS[step.severity] || BORDER : BORDER}`,
            borderLeft: `4px solid ${SEVERITY_COLORS[step.severity] || GOLD}`,
            borderRadius: "4px", cursor: "pointer", overflow: "hidden"
          }}>
          <div style={{ padding: "12px 16px", display: "flex",
            alignItems: "center", gap: "12px" }}>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px",
              color: SEVERITY_COLORS[step.severity] || GOLD,
              minWidth: "28px", textAlign: "center" }}>
              {String(step.step).padStart(2, "0")}
            </div>
            <div style={{ fontSize: "16px" }}>
              {PHASE_ICONS[step.phase] || "•"}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                <span style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "13px",
                  fontWeight: 700, color: "var(--text-primary, #e2e8f0)" }}>
                  {step.technique}
                </span>
                <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                  color: DIM }}>{step.technique_id}</span>
              </div>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                color: DIM, marginTop: "2px" }}>{step.phase} — {step.tactic_id}</div>
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              {step.blue_team?.gap ? (
                <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                  padding: "2px 6px", borderRadius: "2px",
                  background: "#ff224422", color: "#ff2244",
                  border: "1px solid #ff224444" }}>BLIND SPOT</span>
              ) : (
                <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                  padding: "2px 6px", borderRadius: "2px",
                  background: "#44ffaa22", color: "#44ffaa",
                  border: "1px solid #44ffaa44" }}>DETECTABLE</span>
              )}
              <span style={{ color: DIM, fontSize: "12px" }}>
                {activeStep === i ? "▲" : "▼"}
              </span>
            </div>
          </div>

          {activeStep === i && (
            <div style={{ padding: "0 16px 16px", display: "grid",
              gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div style={{ background: "#ff222211", border: "1px solid #ff222233",
                borderRadius: "4px", padding: "12px" }}>
                <div style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "11px",
                  fontWeight: 700, color: "#ff4444", letterSpacing: "0.1em",
                  marginBottom: "8px" }}>RED TEAM — ATTACK</div>
                <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "11px",
                  color: "var(--text-secondary, #8899bb)", lineHeight: 1.6,
                  marginBottom: "8px" }}>
                  {step.red_team?.action}
                </div>
                {step.red_team?.tools?.length > 0 && (
                  <div style={{ marginBottom: "6px" }}>
                    <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                      color: DIM, marginBottom: "4px" }}>TOOLS:</div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                      {step.red_team.tools.map((t, i) => (
                        <span key={i} style={{ fontFamily: "JetBrains Mono, monospace",
                          fontSize: "9px", padding: "2px 6px", borderRadius: "2px",
                          background: "#ff222222", color: "#ff6666",
                          border: "1px solid #ff222244" }}>{t}</span>
                      ))}
                    </div>
                  </div>
                )}
                {step.red_team?.commands && (
                  <div>
                    <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                      color: DIM, marginBottom: "4px" }}>INDICATOR:</div>
                    <code style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
                      color: "#ff8888", background: "#ff222211",
                      padding: "4px 8px", borderRadius: "2px", display: "block",
                      wordBreak: "break-all" }}>{step.red_team.commands}</code>
                  </div>
                )}
              </div>

              <div style={{ background: "#44ffaa11", border: "1px solid #44ffaa33",
                borderRadius: "4px", padding: "12px" }}>
                <div style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "11px",
                  fontWeight: 700, color: "#44ffaa", letterSpacing: "0.1em",
                  marginBottom: "8px" }}>BLUE TEAM — DEFENSE</div>
                <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "11px",
                  color: "var(--text-secondary, #8899bb)", lineHeight: 1.6,
                  marginBottom: "8px" }}>
                  {step.blue_team?.detection}
                </div>
                {step.blue_team?.log_source && (
                  <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                    color: "#44aaff", marginBottom: "8px" }}>
                    LOG SOURCE: {step.blue_team.log_source}
                  </div>
                )}
                {step.blue_team?.detection_query && (
                  <div style={{ marginBottom: "8px" }}>
                    <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                      color: DIM, marginBottom: "4px" }}>DETECTION QUERY:</div>
                    <code style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
                      color: "#44ffaa", background: "#44ffaa11",
                      padding: "4px 8px", borderRadius: "2px", display: "block",
                      wordBreak: "break-all" }}>{step.blue_team.detection_query}</code>
                  </div>
                )}
                {step.blue_team?.gap && (
                  <div style={{ background: "#ff222222", border: "1px solid #ff222244",
                    borderRadius: "4px", padding: "8px",
                    fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
                    color: "#ff6666" }}>
                    GAP: {step.blue_team.gap}
                  </div>
                )}
                {step.blue_team?.response && (
                  <div style={{ marginTop: "8px", fontFamily: "Outfit, sans-serif",
                    fontSize: "11px", color: "#44ffaa", lineHeight: 1.5 }}>
                    RESPONSE: {step.blue_team.response}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ))}

      {result.defensive_gaps?.length > 0 && (
        <div style={{ background: "#ff222211", border: "1px solid #ff222233",
          borderRadius: "4px", padding: "16px" }}>
          <div style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "13px",
            fontWeight: 700, color: "#ff4444", letterSpacing: "0.1em",
            marginBottom: "10px" }}>DEFENSIVE GAPS IDENTIFIED</div>
          {result.defensive_gaps.map((gap, i) => (
            <div key={i} style={{ fontFamily: "Outfit, sans-serif", fontSize: "11px",
              color: "var(--text-secondary, #8899bb)", padding: "4px 0",
              borderBottom: `1px solid ${BORDER}`, lineHeight: 1.5 }}>
              {i + 1}. {gap}
            </div>
          ))}
        </div>
      )}

      {result.immediate_recommendations?.length > 0 && (
        <div style={{ background: "#44ffaa11", border: "1px solid #44ffaa33",
          borderRadius: "4px", padding: "16px" }}>
          <div style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "13px",
            fontWeight: 700, color: "#44ffaa", letterSpacing: "0.1em",
            marginBottom: "10px" }}>IMMEDIATE RECOMMENDATIONS</div>
          {result.immediate_recommendations.map((rec, i) => (
            <div key={i} style={{ fontFamily: "Outfit, sans-serif", fontSize: "11px",
              color: "var(--text-secondary, #8899bb)", padding: "4px 0",
              borderBottom: `1px solid ${BORDER}`, lineHeight: 1.5 }}>
              {i + 1}. {rec}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const TACTICS = [
  { id: "TA0001", name: "Recon" },
  { id: "TA0002", name: "Resource Dev" },
  { id: "TA0003", name: "Initial Access" },
  { id: "TA0004", name: "Execution" },
  { id: "TA0005", name: "Persistence" },
  { id: "TA0006", name: "Priv Escalation" },
  { id: "TA0007", name: "Defense Evasion" },
  { id: "TA0008", name: "Credential Access" },
  { id: "TA0009", name: "Discovery" },
  { id: "TA0010", name: "Lateral Movement" },
  { id: "TA0011", name: "Collection" },
  { id: "TA0040", name: "Impact" },
  { id: "TA0042", name: "C2" },
  { id: "TA0043", name: "Exfiltration" },
]

function CoverageMatrix({ lastResult }) {
  const [coverage, setCoverage] = useState({})
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    if (!lastResult) return
    const map = {}
    const steps = lastResult.steps || []
    for (const step of steps) {
      const tacticId = step.mitre_tactic_id || ""
      const detected = step.blue_team && step.blue_team.detection_method && step.blue_team.detection_method !== "Unknown"
      const partial = step.blue_team && step.blue_team.gap_identified
      const status = detected ? (partial ? "partial" : "detected") : "blind"
      if (tacticId) map[tacticId] = { status, step }
    }
    setCoverage(map)
  }, [lastResult])

  const cellColor = (status) => ({
    detected: "var(--success)",
    partial: "#f59e0b",
    blind: "var(--danger)",
    untested: "var(--border)"
  })[status] || "var(--border)"

  const cellBg = (status) => ({
    detected: "rgba(34,197,94,0.15)",
    partial: "rgba(245,158,11,0.15)",
    blind: "rgba(239,68,68,0.15)",
    untested: "transparent"
  })[status] || "transparent"

  const detected = Object.values(coverage).filter(v => v.status === "detected").length
  const partial = Object.values(coverage).filter(v => v.status === "partial").length
  const blind = Object.values(coverage).filter(v => v.status === "blind").length
  const total = Object.keys(coverage).length

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {!lastResult && (
        <div style={{ background: BG2, border: `1px solid ${BORDER}`, borderRadius: "4px", padding: "24px", textAlign: "center", color: DIM, fontFamily: "JetBrains Mono, monospace", fontSize: "11px" }}>
          Run a simulation first to populate the coverage matrix.
        </div>
      )}
      {lastResult && (
        <>
          {/* Stats */}
          <div style={{ display: "flex", gap: "10px" }}>
            {[
              { label: "DETECTED", value: detected, color: "var(--success)" },
              { label: "PARTIAL", value: partial, color: "#f59e0b" },
              { label: "BLIND SPOTS", value: blind, color: "var(--danger)" },
              { label: "TOTAL MAPPED", value: total, color: GOLD },
            ].map(s => (
              <div key={s.label} style={{ flex: 1, background: BG2, border: `1px solid ${BORDER}`, borderRadius: "4px", padding: "10px", textAlign: "center" }}>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "22px", fontWeight: 700, color: s.color }}>{s.value}</div>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: DIM, marginTop: "2px", letterSpacing: "0.1em" }}>{s.label}</div>
              </div>
            ))}
          </div>
          {/* Matrix */}
          <div style={{ background: BG2, border: `1px solid ${BORDER}`, borderRadius: "4px", overflow: "hidden" }}>
            <div style={{ padding: "10px 14px", borderBottom: `1px solid ${BORDER}` }}>
              <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px", letterSpacing: "0.15em", color: GOLD }}>ATT&CK TACTIC COVERAGE</span>
            </div>
            <div style={{ padding: "14px", display: "flex", flexWrap: "wrap", gap: "6px" }}>
              {TACTICS.map(tactic => {
                const cov = coverage[tactic.id]
                const status = cov ? cov.status : "untested"
                return (
                  <div key={tactic.id} onClick={() => setSelected(cov ? { tactic, ...cov } : null)}
                    style={{ width: "120px", padding: "10px 8px", borderRadius: "3px", cursor: cov ? "pointer" : "default", border: `1px solid ${cellColor(status)}`, background: cellBg(status), transition: "all 0.15s ease" }}>
                    <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: cellColor(status), letterSpacing: "0.1em", marginBottom: "4px" }}>{tactic.id}</div>
                    <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 600, fontSize: "11px", color: cov ? "var(--text-primary)" : DIM }}>{tactic.name}</div>
                    <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: cellColor(status), marginTop: "4px", textTransform: "uppercase" }}>{status}</div>
                  </div>
                )
              })}
            </div>
          </div>
          {/* Legend */}
          <div style={{ display: "flex", gap: "16px", padding: "8px 0" }}>
            {[
              { status: "detected", label: "Detected" },
              { status: "partial", label: "Partial" },
              { status: "blind", label: "Blind Spot" },
              { status: "untested", label: "Not Tested" },
            ].map(l => (
              <div key={l.status} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <div style={{ width: "10px", height: "10px", borderRadius: "2px", background: cellColor(l.status), border: `1px solid ${cellColor(l.status)}` }} />
                <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: DIM }}>{l.label}</span>
              </div>
            ))}
          </div>
          {/* Detail panel */}
          {selected && (
            <div style={{ background: BG2, border: `1px solid ${cellColor(selected.status)}`, borderRadius: "4px", padding: "14px 16px" }}>
              <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "14px", letterSpacing: "0.1em", color: GOLD, marginBottom: "8px" }}>{selected.tactic.id} — {selected.tactic.name}</div>
              {selected.step && (
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-secondary)" }}><span style={{ color: DIM }}>Action: </span>{selected.step.red_team?.attack_action || "N/A"}</div>
                  <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-secondary)" }}><span style={{ color: DIM }}>Detection: </span>{selected.step.blue_team?.detection_method || "None"}</div>
                  <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-secondary)" }}><span style={{ color: DIM }}>Log Source: </span>{selected.step.blue_team?.log_source || "N/A"}</div>
                  <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-secondary)" }}><span style={{ color: DIM }}>Response: </span>{selected.step.blue_team?.response_action || "N/A"}</div>
                  {selected.step.blue_team?.gap_identified && <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "#f59e0b" }}><span style={{ color: DIM }}>Gap: </span>{selected.step.blue_team.gap_identified}</div>}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}