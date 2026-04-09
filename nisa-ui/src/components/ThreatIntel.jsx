import { useState, useEffect } from "react"
import api from "../api"

const TI_API = "http://localhost:8093"
const GOLD = "var(--accent-gold, #c9a84c)"
const BORDER = "var(--border, #1e2d4a)"
const BG2 = "var(--bg-secondary, #0d1526)"
const BG3 = "var(--bg-tertiary, #111827)"
const DIM = "var(--text-dim, #4a5568)"

const SEVERITY_COLORS = {
  CRITICAL: "#ff2244", HIGH: "#ff6600", MEDIUM: "#c9a84c",
  LOW: "#44aaff", UNKNOWN: "#666688"
}

const TACTIC_COLORS = {
  "Reconnaissance": "#ff4444", "Resource Development": "#ff6600",
  "Initial Access": "#ff8800", "Execution": "#ffaa00",
  "Persistence": "#c9a84c", "Privilege Escalation": "#88cc00",
  "Defense Evasion": "#44aa44", "Credential Access": "#44aaaa",
  "Discovery": "#4488ff", "Lateral Movement": "#6644ff",
  "Collection": "#8844ff", "Command and Control": "#aa44ff",
  "Exfiltration": "#ff44ff", "Impact": "#ff4488"
}

export default function ThreatIntel() {
  const [activeTab, setActiveTab] = useState("overview")
  const [summary, setSummary] = useState(null)

  useEffect(() => {
    api.get(`${TI_API}/intel/summary`).then(r => setSummary(r.data)).catch(() => {})
  }, [])

  const tabs = [
    { id: "overview", label: "OVERVIEW" },
    { id: "cve", label: "CVE SEARCH" },
    { id: "mitre", label: "MITRE ATT&CK" },
    { id: "tactics", label: "TACTIC MATRIX" },
  ]

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "20px",
            fontWeight: 700, letterSpacing: "0.15em", color: GOLD, margin: 0 }}>
            THREAT INTELLIGENCE
          </h2>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
            color: DIM, marginTop: "2px" }}>
            Local Knowledge — NVD CVE, MITRE ATT&CK, OWASP
          </div>
        </div>
        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
          color: DIM, textAlign: "right" }}>
          <div style={{ color: "#44ffaa" }}>SOURCE: LOCAL</div>
          <div>Zero external calls</div>
        </div>
      </div>

      <div style={{ display: "flex", gap: "4px", borderBottom: `1px solid ${BORDER}`, paddingBottom: "8px" }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            padding: "6px 14px", border: "none", cursor: "pointer",
            fontFamily: "Rajdhani, sans-serif", fontWeight: 600,
            fontSize: "11px", letterSpacing: "0.1em", background: "transparent",
            color: activeTab === t.id ? GOLD : DIM,
            borderBottom: activeTab === t.id ? `2px solid ${GOLD}` : "2px solid transparent",
          }}>{t.label}</button>
        ))}
      </div>

      {activeTab === "overview" && <OverviewTab summary={summary} />}
      {activeTab === "cve" && <CVESearchTab />}
      {activeTab === "mitre" && <MitreSearchTab />}
      {activeTab === "tactics" && <TacticsMatrixTab />}
    </div>
  )
}

function OverviewTab({ summary }) {
  const [recentCVEs, setRecentCVEs] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    api.get(`${TI_API}/cve/recent?severity=CRITICAL&limit=10`)
      .then(r => setRecentCVEs(r.data.cves || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {summary && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "8px" }}>
          {[
            { label: "CVEs INDEXED", value: summary.cve_count || "N/A", color: "#ff4444" },
            { label: "CRITICAL REFS", value: summary.critical_mentions || "N/A", color: "#ff6600" },
            { label: "ATT&CK TECHNIQUES", value: summary.mitre_techniques_indexed || "N/A", color: GOLD },
            { label: "KNOWLEDGE FILES", value: summary.knowledge_files || "N/A", color: "#44aaff" },
          ].map(s => (
            <div key={s.label} style={{ background: BG2, border: `1px solid ${BORDER}`,
              borderRadius: "4px", padding: "12px", textAlign: "center" }}>
              <div style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "24px",
                fontWeight: 700, color: s.color }}>{s.value}</div>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                color: DIM, letterSpacing: "0.1em" }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ background: BG2, border: `1px solid ${BORDER}`, borderRadius: "4px", padding: "16px" }}>
        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
          color: DIM, letterSpacing: "0.1em", marginBottom: "12px" }}>
          CRITICAL CVEs FROM LOCAL KNOWLEDGE
        </div>
        {loading && <div style={{ color: DIM, fontFamily: "JetBrains Mono, monospace",
          fontSize: "11px" }}>Loading...</div>}
        {recentCVEs.length === 0 && !loading && (
          <div style={{ color: DIM, fontFamily: "JetBrains Mono, monospace", fontSize: "11px" }}>
            No CVEs parsed from knowledge file. GraphRAG indexing will improve results.
          </div>
        )}
        {recentCVEs.map((cve, i) => (
          <div key={i} style={{ padding: "10px 0", borderBottom: `1px solid ${BORDER}` }}>
            <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "4px" }}>
              <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px",
                color: GOLD, minWidth: "140px" }}>{cve.id}</span>
              <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                padding: "2px 6px", borderRadius: "2px",
                background: (SEVERITY_COLORS[cve.severity] || "#666") + "22",
                color: SEVERITY_COLORS[cve.severity] || DIM,
                border: `1px solid ${SEVERITY_COLORS[cve.severity] || "#666"}` }}>
                {cve.severity}
              </span>
              {cve.cvss && <span style={{ color: DIM, fontSize: "9px",
                fontFamily: "JetBrains Mono, monospace" }}>CVSS {cve.cvss}</span>}
            </div>
            <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "11px",
              color: "var(--text-secondary, #8899bb)", lineHeight: 1.5 }}>
              {cve.description}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function CVESearchTab() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const search = async () => {
    if (!query.trim()) return
    setLoading(true); setError("")
    try {
      const res = await api.get(`${TI_API}/cve/search?q=${encodeURIComponent(query)}&limit=20`)
      setResults(res.data)
    } catch(e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ display: "flex", gap: "8px" }}>
        <input value={query} onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === "Enter" && search()}
          placeholder="Search CVEs... (e.g. postgresql, buffer overflow, remote code execution)"
          style={{ flex: 1, background: BG3, border: `1px solid ${BORDER}`,
            borderRadius: "4px", padding: "8px 12px", color: "var(--text-primary, #e2e8f0)",
            fontFamily: "JetBrains Mono, monospace", fontSize: "12px", outline: "none" }} />
        <button onClick={search} disabled={loading} style={{
          padding: "8px 20px", background: "var(--accent-gold-glow, #c9a84c22)",
          border: `1px solid ${GOLD}`, borderRadius: "4px", cursor: "pointer",
          fontFamily: "Rajdhani, sans-serif", fontWeight: 700,
          fontSize: "12px", letterSpacing: "0.15em", color: GOLD }}>
          {loading ? "SEARCHING..." : "SEARCH"}
        </button>
      </div>

      {error && <div style={{ color: "var(--danger, #ff4444)",
        fontFamily: "JetBrains Mono, monospace", fontSize: "11px" }}>{error}</div>}

      {results && (
        <div style={{ background: BG2, border: `1px solid ${BORDER}`, borderRadius: "4px", padding: "16px" }}>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
            color: DIM, marginBottom: "12px" }}>
            {results.total} results for "{results.query}" — source: {results.source}
          </div>
          {results.cves.map((cve, i) => (
            <div key={i} style={{ padding: "10px 0", borderBottom: `1px solid ${BORDER}` }}>
              <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "4px" }}>
                <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px",
                  color: GOLD, minWidth: "140px" }}>{cve.id}</span>
                <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                  padding: "2px 6px", borderRadius: "2px",
                  background: (SEVERITY_COLORS[cve.severity] || "#666") + "22",
                  color: SEVERITY_COLORS[cve.severity] || DIM,
                  border: `1px solid ${SEVERITY_COLORS[cve.severity] || "#666"}` }}>
                  {cve.severity}
                </span>
              </div>
              <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "11px",
                color: "var(--text-secondary, #8899bb)", lineHeight: 1.5 }}>
                {cve.description}
              </div>
            </div>
          ))}
          {results.cves.length === 0 && (
            <div style={{ color: DIM, fontFamily: "JetBrains Mono, monospace", fontSize: "11px" }}>
              No matches found. Try a different search term or run the knowledge scraper to expand the CVE library.
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function MitreSearchTab() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)

  const search = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const res = await api.get(`${TI_API}/mitre/search?q=${encodeURIComponent(query)}`)
      setResults(res.data)
    } catch(e) {}
    setLoading(false)
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ display: "flex", gap: "8px" }}>
        <input value={query} onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === "Enter" && search()}
          placeholder="Search ATT&CK techniques... (e.g. phishing, credential dumping, lateral movement)"
          style={{ flex: 1, background: BG3, border: `1px solid ${BORDER}`,
            borderRadius: "4px", padding: "8px 12px", color: "var(--text-primary, #e2e8f0)",
            fontFamily: "JetBrains Mono, monospace", fontSize: "12px", outline: "none" }} />
        <button onClick={search} disabled={loading} style={{
          padding: "8px 20px", background: "var(--accent-gold-glow, #c9a84c22)",
          border: `1px solid ${GOLD}`, borderRadius: "4px", cursor: "pointer",
          fontFamily: "Rajdhani, sans-serif", fontWeight: 700,
          fontSize: "12px", letterSpacing: "0.15em", color: GOLD }}>
          {loading ? "SEARCHING..." : "SEARCH"}
        </button>
      </div>

      {results && (
        <div style={{ background: BG2, border: `1px solid ${BORDER}`, borderRadius: "4px", padding: "16px" }}>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
            color: DIM, marginBottom: "12px" }}>
            {results.total} techniques found for "{results.query}"
          </div>
          {results.techniques.map((t, i) => (
            <div key={i} style={{ padding: "10px 0", borderBottom: `1px solid ${BORDER}` }}>
              <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "4px" }}>
                <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px",
                  color: GOLD, minWidth: "70px" }}>{t.id}</span>
                <span style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "13px",
                  fontWeight: 600, color: "var(--text-primary, #e2e8f0)" }}>{t.name}</span>
                <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                  padding: "2px 6px", borderRadius: "2px",
                  background: (TACTIC_COLORS[t.tactic] || "#666") + "22",
                  color: TACTIC_COLORS[t.tactic] || DIM,
                  border: `1px solid ${(TACTIC_COLORS[t.tactic] || "#666") + "66"}` }}>
                  {t.tactic}
                </span>
              </div>
              {t.description && (
                <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "11px",
                  color: "var(--text-secondary, #8899bb)", lineHeight: 1.5 }}>
                  {t.description}
                </div>
              )}
            </div>
          ))}
          {results.techniques.length === 0 && (
            <div style={{ color: DIM, fontFamily: "JetBrains Mono, monospace", fontSize: "11px" }}>
              No techniques found. Try broader search terms.
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function TacticsMatrixTab() {
  const [tactics, setTactics] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.get(`${TI_API}/mitre/tactics`)
      .then(r => setTactics(r.data.tactics || []))
      .catch(() => {})
  }, [])

  const handleTacticClick = async (tactic) => {
    if (selected?.id === tactic.id) { setSelected(null); return }
    setLoading(true)
    try {
      const res = await api.get(`${TI_API}/mitre/search?q=${encodeURIComponent(tactic.name)}`)
      setSelected({ ...tactic, techniques: res.data.techniques || [] })
    } catch(e) {
      setSelected({ ...tactic, techniques: [] })
    }
    setLoading(false)
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
        color: DIM }}>
        MITRE ATT&CK Enterprise — 14 Tactics — Click a tactic to explore techniques
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: "6px" }}>
        {tactics.map(t => (
          <div key={t.id} onClick={() => handleTacticClick(t)}
            style={{
              background: selected?.id === t.id ? t.color + "33" : BG2,
              border: `1px solid ${selected?.id === t.id ? t.color : BORDER}`,
              borderRadius: "4px", padding: "10px 8px", cursor: "pointer",
              transition: "all 0.2s",
              borderTop: `3px solid ${t.color}`
            }}>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px",
              color: t.color, marginBottom: "4px" }}>{t.id}</div>
            <div style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "11px",
              fontWeight: 600, color: "var(--text-primary, #e2e8f0)", lineHeight: 1.3 }}>
              {t.name}
            </div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
              color: DIM, marginTop: "4px" }}>{t.techniques} techniques</div>
          </div>
        ))}
      </div>

      {selected && (
        <div style={{ background: BG2, border: `1px solid ${selected.color || BORDER}`,
          borderRadius: "4px", padding: "16px" }}>
          <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "12px" }}>
            <div style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "16px",
              fontWeight: 700, color: selected.color }}>{selected.name}</div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
              color: DIM }}>{selected.id}</div>
          </div>
          {loading && <div style={{ color: DIM, fontFamily: "JetBrains Mono, monospace",
            fontSize: "11px" }}>Loading techniques...</div>}
          {!loading && selected.techniques.length === 0 && (
            <div style={{ color: DIM, fontFamily: "JetBrains Mono, monospace", fontSize: "11px" }}>
              No technique details found in local knowledge. GraphRAG indexing will improve results.
            </div>
          )}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
            {selected.techniques.map((t, i) => (
              <div key={i} style={{ background: BG3, border: `1px solid ${BORDER}`,
                borderRadius: "4px", padding: "10px" }}>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
                  color: GOLD, marginBottom: "4px" }}>{t.id}</div>
                <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "11px",
                  color: "var(--text-secondary, #8899bb)", lineHeight: 1.4 }}>
                  {t.name || t.description?.slice(0, 100)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
