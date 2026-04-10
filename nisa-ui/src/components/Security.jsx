import { useState, useEffect } from "react"
import { pushContext } from "../SessionContext"
import { Shield, Radar, Globe, ChevronRight, AlertTriangle, CheckCircle, Info, Activity } from "lucide-react"
import api from "../api"

const SEC_API = "http://localhost:8082"
const IDS_API = "http://localhost:8085"

export default function Security() {
  const [activeTab, setActiveTab] = useState("nmap")

  return (
    <div className="fade-in" style={{ maxWidth: "900px", margin: "0 auto" }}>
      <PageHeader
        icon={Shield}
        title="SECURITY DASHBOARD"
        subtitle="Network scanning and vulnerability assessment"
      />

      {/* Tabs */}
      <div style={{
        display: "flex",
        gap: "0",
        borderBottom: "1px solid var(--border)",
        marginBottom: "24px",
      }}>
        {[
          { id: "nmap", label: "NMAP SCAN", icon: Radar },
          { id: "zap", label: "ZAP SCAN", icon: Globe },
          { id: "ids", label: "SURICATA IDS", icon: Activity },
          { id: "burp", label: "BURP SUITE", icon: Shield },
        ].map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setActiveTab(id)} style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "10px 20px",
            background: "transparent",
            border: "none",
            borderBottom: activeTab === id ? "2px solid var(--accent-gold)" : "2px solid transparent",
            color: activeTab === id ? "var(--accent-gold)" : "var(--text-dim)",
            fontFamily: "Rajdhani, sans-serif",
            fontWeight: 600,
            fontSize: "12px",
            letterSpacing: "0.15em",
            cursor: "pointer",
            transition: "all 0.2s",
            marginBottom: "-1px",
          }}>
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {activeTab === "nmap" && <NmapPanel />}
      {activeTab === "zap" && <ZapPanel />}
      {activeTab === "ids" && <SuricataPanel />}
      {activeTab === "burp" && <BurpPanel />}
    </div>
  )
}

function NmapPanel() {
  const [target, setTarget] = useState("127.0.0.1")
  const [scanType, setScanType] = useState("quick")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const runScan = async () => {
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const tokenRes = await api.post(`${SEC_API}/token`, { tool: "nmap" })
      const token = tokenRes.data.token
      const scanRes = await api.post(
        `${SEC_API}/scan/nmap?token=${token}`,
        { target, scan_type: scanType }
      )
      setResult(scanRes.data)
      const d = scanRes.data
      pushContext({
        tab: "Security",
        operation: `Nmap ${scanType.toUpperCase()} Scan`,
        summary: `Target: ${d.target} - ${d.ports?.length ?? 0} open ports. ${d.summary || ""}`.trim(),
        detail: { target: d.target, ports: d.ports, scan_type: scanType }
      })
      // Auto-ingest into Asset Inventory
      try {
        await api.post("http://localhost:8097/assets/ingest/nmap", d)
      } catch(e) { console.warn("Asset ingest failed:", e) }
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <Panel title="SCAN CONFIGURATION">
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: "200px" }}>
            <FieldLabel>TARGET</FieldLabel>
            <input
              value={target}
              onChange={e => setTarget(e.target.value)}
              style={inputStyle}
              placeholder="127.0.0.1 or 192.168.x.x"
            />
          </div>
          <div>
            <FieldLabel>SCAN TYPE</FieldLabel>
            <select value={scanType} onChange={e => setScanType(e.target.value)} style={inputStyle}>
              <option value="quick">Quick (-F)</option>
              <option value="basic">Basic (-sV)</option>
              <option value="deep">Deep (-sV -sC)</option>
            </select>
          </div>
          <div style={{ display: "flex", alignItems: "flex-end" }}>
            <ScanButton onClick={runScan} loading={loading} label="RUN NMAP" />
          </div>
        </div>
      </Panel>

      {loading && <LoadingPanel label="Scanning with Nmap..." />}
      {error && <ErrorPanel message={error} />}
      {result && <NmapResult result={result} />}
    </div>
  )
}

function NmapResult({ result }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <Panel title="SCAN RESULTS">
        <div style={{ marginBottom: "12px" }}>
          <StatRow label="Target" value={result.target} />
          <StatRow label="Open Ports" value={result.ports.length} />
          <StatRow label="Summary" value={result.summary} />
        </div>
        {result.ports.length > 0 && (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {["PORT", "STATE", "SERVICE"].map(h => (
                  <th key={h} style={thStyle}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.ports.map((p, i) => (
                <tr key={i}>
                  <td style={tdStyle}>{p.port}</td>
                  <td style={{ ...tdStyle, color: "var(--success)" }}>{p.state}</td>
                  <td style={tdStyle}>{p.service}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
      {result.analysis && (
        <Panel title="REDSAGE ANALYSIS">
          <div style={{
            fontFamily: "Outfit, sans-serif",
            fontSize: "13px",
            lineHeight: "1.7",
            color: "var(--text-primary)",
            whiteSpace: "pre-wrap",
          }}>{result.analysis}</div>
        </Panel>
      )}
      <Panel title="RAW OUTPUT">
        <pre style={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "11px",
          color: "var(--text-secondary)",
          whiteSpace: "pre-wrap",
          lineHeight: "1.6",
        }}>{result.results}</pre>
      </Panel>
    </div>
  )
}

function ZapPanel() {
  const [target, setTarget] = useState("http://host.docker.internal:8081")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const runScan = async () => {
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const tokenRes = await api.post(`${SEC_API}/token`, { tool: "zap" })
      const token = tokenRes.data.token
      const scanRes = await api.post(
        `${SEC_API}/scan/zap?token=${token}`,
        { target }
      )
      setResult(scanRes.data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <Panel title="SCAN CONFIGURATION">
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: "200px" }}>
            <FieldLabel>TARGET URL</FieldLabel>
            <input
              value={target}
              onChange={e => setTarget(e.target.value)}
              style={inputStyle}
              placeholder="http://host.docker.internal:8081"
            />
          </div>
          <div style={{ display: "flex", alignItems: "flex-end" }}>
            <ScanButton onClick={runScan} loading={loading} label="RUN ZAP" />
          </div>
        </div>
      </Panel>

      {loading && <LoadingPanel label="Running OWASP ZAP scan... (this takes 1-2 minutes)" />}
      {error && <ErrorPanel message={error} />}
      {result && <ZapResult result={result} />}
    </div>
  )
}

function ZapResult({ result }) {
  const riskColors = {
    High: "var(--danger)",
    Medium: "var(--warning)",
    Low: "var(--accent-cyan)",
    Informational: "var(--text-dim)",
  }
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <Panel title="SCAN RESULTS">
        <div style={{ display: "flex", gap: "16px", marginBottom: "16px", flexWrap: "wrap" }}>
          {Object.entries(result.risk_counts).map(([risk, count]) => (
            <div key={risk} style={{
              padding: "8px 16px",
              border: `1px solid ${riskColors[risk] || "var(--border)"}`,
              borderRadius: "2px",
              background: "var(--bg-secondary)",
            }}>
              <div style={{
                fontFamily: "JetBrains Mono, monospace",
                fontSize: "20px",
                fontWeight: 500,
                color: riskColors[risk] || "var(--text-primary)",
              }}>{count}</div>
              <div style={{
                fontFamily: "Rajdhani, sans-serif",
                fontSize: "10px",
                letterSpacing: "0.15em",
                color: "var(--text-dim)",
              }}>{risk.toUpperCase()}</div>
            </div>
          ))}
        </div>
        <StatRow label="Target" value={result.target} />
        <StatRow label="Summary" value={result.summary} />
        {result.alerts.length === 0 && (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            marginTop: "12px",
            color: "var(--success)",
            fontFamily: "Outfit, sans-serif",
            fontSize: "13px",
          }}>
            <CheckCircle size={14} />
            No vulnerabilities detected
          </div>
        )}
      </Panel>
      {result.analysis && (
        <Panel title="REDSAGE ANALYSIS">
          <div style={{
            fontFamily: "Outfit, sans-serif",
            fontSize: "13px",
            lineHeight: "1.7",
            color: "var(--text-primary)",
            whiteSpace: "pre-wrap",
          }}>{result.analysis}</div>
        </Panel>
      )}
      {result.alerts.length > 0 && (
        <Panel title="ALERTS">
          {result.alerts.map((a, i) => (
            <div key={i} style={{
              padding: "10px 12px",
              borderLeft: `2px solid ${riskColors[a.risk] || "var(--border)"}`,
              background: "var(--bg-secondary)",
              marginBottom: "8px",
              borderRadius: "0 2px 2px 0",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                <span style={{
                  fontFamily: "Rajdhani, sans-serif",
                  fontWeight: 600,
                  fontSize: "13px",
                  color: "var(--text-primary)",
                }}>{a.name}</span>
                <span style={{
                  fontFamily: "JetBrains Mono, monospace",
                  fontSize: "10px",
                  color: riskColors[a.risk],
                }}>{a.risk}</span>
              </div>
              <div style={{
                fontFamily: "JetBrains Mono, monospace",
                fontSize: "10px",
                color: "var(--text-dim)",
                marginBottom: "4px",
              }}>{a.url}</div>
              <div style={{
                fontFamily: "Outfit, sans-serif",
                fontSize: "12px",
                color: "var(--text-secondary)",
              }}>{a.description}</div>
            </div>
          ))}
        </Panel>
      )}
    </div>
  )
}

// ── Shared Components ─────────────────────────────────────────────

function PageHeader({ icon: Icon, title, subtitle }) {
  return (
    <div style={{ marginBottom: "24px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
        <Icon size={18} color="var(--accent-gold)" />
        <h1 style={{
          fontFamily: "Rajdhani, sans-serif",
          fontWeight: 700,
          fontSize: "20px",
          letterSpacing: "0.15em",
          color: "var(--text-primary)",
        }}>{title}</h1>
      </div>
      <p style={{
        fontFamily: "Outfit, sans-serif",
        fontSize: "13px",
        color: "var(--text-dim)",
        marginLeft: "28px",
      }}>{subtitle}</p>
    </div>
  )
}

function Panel({ title, children }) {
  return (
    <div style={{
      border: "1px solid var(--border)",
      borderRadius: "4px",
      background: "var(--bg-panel)",
      overflow: "hidden",
    }}>
      <div style={{
        padding: "8px 14px",
        borderBottom: "1px solid var(--border)",
        background: "var(--bg-secondary)",
        fontFamily: "Rajdhani, sans-serif",
        fontWeight: 600,
        fontSize: "11px",
        letterSpacing: "0.15em",
        color: "var(--text-dim)",
      }}>{title}</div>
      <div style={{ padding: "14px" }}>{children}</div>
    </div>
  )
}

function FieldLabel({ children }) {
  return (
    <div style={{
      fontFamily: "JetBrains Mono, monospace",
      fontSize: "9px",
      letterSpacing: "0.15em",
      color: "var(--text-dim)",
      marginBottom: "6px",
    }}>{children}</div>
  )
}

function StatRow({ label, value }) {
  return (
    <div style={{
      display: "flex",
      gap: "12px",
      padding: "4px 0",
      borderBottom: "1px solid var(--border)",
      marginBottom: "4px",
    }}>
      <span style={{
        fontFamily: "JetBrains Mono, monospace",
        fontSize: "10px",
        color: "var(--text-dim)",
        minWidth: "100px",
        letterSpacing: "0.05em",
      }}>{label}</span>
      <span style={{
        fontFamily: "Outfit, sans-serif",
        fontSize: "12px",
        color: "var(--text-secondary)",
      }}>{value}</span>
    </div>
  )
}

function ScanButton({ onClick, loading, label }) {
  return (
    <button onClick={onClick} disabled={loading} style={{
      display: "flex",
      alignItems: "center",
      gap: "8px",
      padding: "8px 16px",
      background: loading ? "var(--bg-elevated)" : "var(--accent-gold-glow)",
      border: `1px solid ${loading ? "var(--border)" : "var(--accent-gold-dim)"}`,
      borderRadius: "2px",
      color: loading ? "var(--text-dim)" : "var(--accent-gold)",
      fontFamily: "Rajdhani, sans-serif",
      fontWeight: 600,
      fontSize: "12px",
      letterSpacing: "0.15em",
      cursor: loading ? "not-allowed" : "pointer",
      transition: "all 0.2s",
    }}>
      <ChevronRight size={14} />
      {loading ? "SCANNING..." : label}
    </button>
  )
}

function LoadingPanel({ label }) {
  return (
    <div style={{
      padding: "20px",
      border: "1px solid var(--border)",
      borderLeft: "2px solid var(--accent-gold-dim)",
      borderRadius: "4px",
      background: "var(--bg-panel)",
      display: "flex",
      alignItems: "center",
      gap: "12px",
    }}>
      <div style={{
        width: "16px", height: "16px",
        border: "2px solid var(--accent-gold-dim)",
        borderTop: "2px solid var(--accent-gold)",
        borderRadius: "50%",
        animation: "spin 0.8s linear infinite",
      }} />
      <span style={{
        fontFamily: "JetBrains Mono, monospace",
        fontSize: "11px",
        color: "var(--text-secondary)",
        letterSpacing: "0.1em",
      }}>{label}</span>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

function ErrorPanel({ message }) {
  return (
    <div style={{
      padding: "14px",
      border: "1px solid var(--danger)",
      borderRadius: "4px",
      background: "rgba(232, 64, 64, 0.05)",
      display: "flex",
      alignItems: "flex-start",
      gap: "10px",
    }}>
      <AlertTriangle size={14} color="var(--danger)" style={{ marginTop: "2px", flexShrink: 0 }} />
      <span style={{
        fontFamily: "JetBrains Mono, monospace",
        fontSize: "11px",
        color: "var(--danger)",
      }}>{message}</span>
    </div>
  )
}

const inputStyle = {
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: "2px",
  color: "var(--text-primary)",
  fontFamily: "JetBrains Mono, monospace",
  fontSize: "12px",
  padding: "8px 10px",
  outline: "none",
  width: "100%",
}

const thStyle = {
  fontFamily: "Rajdhani, sans-serif",
  fontWeight: 600,
  fontSize: "10px",
  letterSpacing: "0.15em",
  color: "var(--text-dim)",
  textAlign: "left",
  padding: "6px 8px",
  borderBottom: "1px solid var(--border)",
}

const tdStyle = {
  fontFamily: "JetBrains Mono, monospace",
  fontSize: "11px",
  color: "var(--text-secondary)",
  padding: "6px 8px",
  borderBottom: "1px solid var(--border)",
}

// ── Suricata IDS Panel ───────────────────────────────────────────
function SuricataPanel() {
  const [status, setStatus] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [analysis, setAnalysis] = useState("")
  const [analyzing, setAnalyzing] = useState(false)

  const fetchStatus = async () => {
    try { const r = await api.get(`${IDS_API}/status`); setStatus(r.data) } catch(e) {}
  }
  const fetchAlerts = async (analyze = false) => {
    if (analyze) setAnalyzing(true)
    try {
      const r = await api.get(`${IDS_API}/alerts?analyze=${analyze}&limit=20`)
      setAlerts(r.data.alerts || [])
      if (analyze) setAnalysis(r.data.analysis || "")
    } catch(e) {}
    if (analyze) setAnalyzing(false)
  }
  const runTest = async () => {
    try { await api.post(`${IDS_API}/test`); fetchAlerts(false) } catch(e) {}
  }

  useEffect(() => {
    fetchStatus(); fetchAlerts(false)
    const t = setInterval(() => { fetchStatus(); fetchAlerts(false) }, 10000)
    return () => clearInterval(t)
  }, [])

  const sevColor = { 1: "var(--danger)", 2: "var(--warning)", 3: "var(--accent-cyan)" }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <Panel title="IDS STATUS">
        <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "12px", flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: status?.running ? "var(--success)" : "var(--text-dim)", boxShadow: status?.running ? "0 0 6px var(--success)" : "none" }} />
            <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: "var(--text-secondary)" }}>{status?.running ? "MONITORING" : "STANDBY"}</span>
          </div>
          <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)" }}>{status?.rules_loaded?.toLocaleString() || "49,494"} rules</span>
          <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)" }}>{status?.total_alerts || 0} alerts</span>
        </div>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          <ScanButton onClick={() => fetchAlerts(true)} loading={analyzing} label="ANALYZE ALERTS" />
          <button onClick={runTest} style={{ padding: "8px 12px", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "2px", color: "var(--text-dim)", fontFamily: "Rajdhani, sans-serif", fontWeight: 600, fontSize: "11px", letterSpacing: "0.1em", cursor: "pointer" }}>INJECT TEST</button>
          <button onClick={() => { fetchStatus(); fetchAlerts(false) }} style={{ padding: "8px 12px", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "2px", color: "var(--text-dim)", fontFamily: "Rajdhani, sans-serif", fontWeight: 600, fontSize: "11px", letterSpacing: "0.1em", cursor: "pointer" }}>REFRESH</button>
        </div>
      </Panel>

      <Panel title={`LIVE ALERTS (${alerts.length})`}>
        {alerts.length === 0 ? (
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: "var(--success)", textAlign: "center", padding: "16px" }}>No alerts — network is clean</div>
        ) : alerts.map((a, i) => (
          <div key={i} style={{ padding: "8px 12px", borderLeft: `2px solid ${sevColor[a.severity] || "var(--border)"}`, background: "var(--bg-secondary)", marginBottom: "6px", borderRadius: "0 2px 2px 0" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "2px" }}>
              <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 600, fontSize: "12px", color: "var(--text-primary)" }}>{a.signature}</span>
              <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: sevColor[a.severity] || "var(--text-dim)" }}>SEV {a.severity}</span>
            </div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)" }}>{a.src_ip} → {a.dest_ip} | {a.proto} | {a.category}</div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", marginTop: "2px" }}>{a.timestamp?.slice(0,19)}</div>
          </div>
        ))}
      </Panel>

      {analysis && (
        <Panel title="REDSAGE IDS ANALYSIS">
          <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "13px", lineHeight: "1.7", color: "var(--text-primary)", whiteSpace: "pre-wrap" }}>{analysis}</div>
        </Panel>
      )}
    </div>
  )
}

// ── Burp Suite Panel ─────────────────────────────────────────────
function BurpPanel() {
  const [notes, setNotes] = useState("")
  const [saved, setSaved] = useState(false)

  const launchBurp = () => {
    api.post("http://localhost:8082/burp/launch").catch(() => {})
    window.open("x-burp://", "_blank")
    setTimeout(() => {
      const cmd = "open -a /Applications/Burp\ Suite\ Community\ Edition.app"
      api.post("http://localhost:8082/burp/launch", { cmd }).catch(() => {})
    }, 500)
  }

  const saveNotes = () => {
    localStorage.setItem("burp_notes", notes)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  useState(() => {
    const saved = localStorage.getItem("burp_notes")
    if (saved) setNotes(saved)
  }, [])

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
        <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)",
          borderRadius: "4px", padding: "20px" }}>
          <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700,
            fontSize: "14px", letterSpacing: "0.1em", color: "var(--accent-gold)",
            marginBottom: "8px" }}>BURP SUITE COMMUNITY</div>
          <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "12px",
            color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: "16px" }}>
            Web application security testing proxy. Intercept, modify, and replay HTTP/S traffic.
            Manual testing, spider crawling, and vulnerability discovery.
          </div>
          <button onClick={launchBurp} style={{
            padding: "10px 20px", background: "var(--accent-gold-glow)",
            border: "1px solid var(--accent-gold)", borderRadius: "4px",
            cursor: "pointer", fontFamily: "Rajdhani, sans-serif",
            fontWeight: 700, fontSize: "12px", letterSpacing: "0.15em",
            color: "var(--accent-gold)", width: "100%"
          }}>LAUNCH BURP SUITE</button>
        </div>

        <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)",
          borderRadius: "4px", padding: "20px" }}>
          <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700,
            fontSize: "14px", letterSpacing: "0.1em", color: "var(--accent-gold)",
            marginBottom: "8px" }}>PROXY SETUP</div>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px",
            color: "var(--text-secondary)", lineHeight: 2 }}>
            <div>Proxy listener: <span style={{ color: "var(--accent-gold)" }}>127.0.0.1:8080</span></div>
            <div>Browser proxy: <span style={{ color: "var(--accent-gold)" }}>localhost:8080</span></div>
            <div>Intercept: <span style={{ color: "var(--accent-gold)" }}>Proxy → Intercept ON</span></div>
            <div>CA cert: <span style={{ color: "var(--accent-gold)" }}>http://burp/cert</span></div>
          </div>
        </div>
      </div>

      <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)",
        borderRadius: "4px", padding: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
          marginBottom: "12px" }}>
          <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700,
            fontSize: "14px", letterSpacing: "0.1em", color: "var(--accent-gold)" }}>
            FINDINGS NOTES
          </div>
          <button onClick={saveNotes} style={{
            padding: "6px 14px", background: saved ? "var(--success)" : "transparent",
            border: "1px solid " + (saved ? "var(--success)" : "var(--border)"),
            borderRadius: "4px", cursor: "pointer",
            fontFamily: "Rajdhani, sans-serif", fontWeight: 600,
            fontSize: "11px", letterSpacing: "0.1em",
            color: saved ? "#000" : "var(--text-dim)"
          }}>{saved ? "SAVED" : "SAVE NOTES"}</button>
        </div>
        <textarea value={notes} onChange={e => setNotes(e.target.value)}
          placeholder="Document Burp Suite findings here...&#10;&#10;Target: &#10;Vulnerabilities found: &#10;Endpoints tested: &#10;Notes: "
          rows={12} style={{
            width: "100%", background: "var(--bg-tertiary)",
            border: "1px solid var(--border)", borderRadius: "4px",
            padding: "12px", color: "var(--text-primary)",
            fontFamily: "JetBrains Mono, monospace", fontSize: "12px",
            outline: "none", resize: "vertical", lineHeight: 1.6
          }} />
      </div>

      <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)",
        borderRadius: "4px", padding: "16px" }}>
        <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700,
          fontSize: "12px", letterSpacing: "0.1em", color: "var(--accent-gold)",
          marginBottom: "8px" }}>UPGRADE NOTE</div>
        <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "12px",
          color: "var(--text-dim)", lineHeight: 1.6 }}>
          Burp Suite Professional ($449/yr) adds REST API for full NISA integration —
          automated scanning, finding export, and programmatic control.
          Community Edition requires manual operation via the GUI.
        </div>
      </div>
    </div>
  )
}
