import { useState, useEffect } from "react"
import { pushAlert, acknowledgeAlerts } from "../SessionContext"
import api from "../api"
import { Plus, Trash2, RefreshCw, Bell, BellOff, CheckCircle, AlertTriangle, Eye, Shield } from "lucide-react"

const WL_API = "http://localhost:8098"

const severityColor = (s) => ({
  critical: "var(--danger)",
  high:     "#f59e0b",
  medium:   "var(--accent-cyan, #00d4ff)",
  low:      "var(--success)"
})[s] || "var(--text-dim)"

const severityBg = (s) => ({
  critical: "rgba(239,68,68,0.08)",
  high:     "rgba(245,158,11,0.08)",
  medium:   "rgba(0,212,255,0.08)",
  low:      "rgba(34,197,94,0.08)"
})[s] || "transparent"

const ENTRY_TYPES = [
  { value: "service",  label: "Service",  placeholder: "e.g. rdp, ssh, smb, ftp" },
  { value: "cve",      label: "CVE ID",   placeholder: "e.g. CVE-2017-0144" },
  { value: "keyword",  label: "Keyword",  placeholder: "e.g. apache, nginx, tomcat" },
]

const QUICK_ENTRIES = [
  { entry_type: "service", value: "rdp",    label: "RDP Exposure",    severity: "critical" },
  { entry_type: "service", value: "telnet", label: "Telnet",          severity: "critical" },
  { entry_type: "service", value: "smb",    label: "SMB/NetBIOS",     severity: "high" },
  { entry_type: "service", value: "ftp",    label: "FTP",             severity: "high" },
  { entry_type: "cve",     value: "CVE-2017-0144", label: "EternalBlue", severity: "critical" },
  { entry_type: "cve",     value: "CVE-2019-0708", label: "BlueKeep",    severity: "critical" },
  { entry_type: "cve",     value: "CVE-2021-44228", label: "Log4Shell",  severity: "critical" },
]

export default function CVEWatchlist() {
  const [entries, setEntries] = useState([])
  const [alerts, setAlerts] = useState([])
  const [stats, setStats] = useState(null)
  const [checking, setChecking] = useState(false)
  const [newEntry, setNewEntry] = useState({ entry_type: "service", value: "", label: "", severity: "high" })
  const [error, setError] = useState("")
  const [lastCheck, setLastCheck] = useState(null)
  const [tab, setTab] = useState("entries")

  useEffect(() => { fetchAll() }, [])

  const fetchAll = async () => {
    try {
      const [eRes, aRes, sRes] = await Promise.all([
        api.get(`${WL_API}/watchlist`),
        api.get(`${WL_API}/alerts?unacked_only=false`),
        api.get(`${WL_API}/stats`)
      ])
      setEntries(eRes.data.entries || [])
      setAlerts(aRes.data.alerts || [])
      setStats(sRes.data)
    } catch(e) { setError("Failed to load watchlist") }
  }

  const addEntry = async () => {
    if (!newEntry.value.trim()) return
    try {
      await api.post(`${WL_API}/watchlist`, {
        ...newEntry,
        label: newEntry.label || newEntry.value
      })
      setNewEntry({ entry_type: "service", value: "", label: "", severity: "high" })
      await fetchAll()
    } catch(e) {
      setError(e.response?.data?.detail || "Failed to add entry")
      setTimeout(() => setError(""), 3000)
    }
  }

  const addQuick = async (entry) => {
    try {
      await api.post(`${WL_API}/watchlist`, entry)
      await fetchAll()
    } catch(e) {}
  }

  const deleteEntry = async (id) => {
    try {
      await api.delete(`${WL_API}/watchlist/${id}`)
      await fetchAll()
    } catch(e) {}
  }

  const runCheck = async () => {
    setChecking(true)
    setError("")
    try {
      const res = await api.post(`${WL_API}/check`)
      setLastCheck(new Date().toLocaleTimeString())
      await fetchAll()

      // Push alerts to Nisaba Orb
      if (res.data.new_alerts > 0) {
        for (const alert of res.data.alerts) {
          await pushAlert({
            title: `CVE Watchlist: ${alert.entry_value}`,
            summary: alert.detail,
            severity: alert.severity,
            source: "CVE Watchlist",
            recommendation: alert.recommendation
          })
        }
        setTab("alerts")
      }
    } catch(e) { setError("Check failed: " + e.message) }
    setChecking(false)
  }

  const ackAll = async () => {
    try {
      await api.post(`${WL_API}/alerts/acknowledge/all`)
      acknowledgeAlerts()
      await fetchAll()
    } catch(e) {}
  }

  const unacked = alerts.filter(a => !a.acknowledged)

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>

      {/* Stats Bar */}
      <div style={{ display: "flex", gap: "12px", alignItems: "stretch" }}>
        {[
          { label: "WATCH ENTRIES", value: stats?.active_entries ?? 0, color: "var(--accent-gold)" },
          { label: "UNACKED ALERTS", value: stats?.unacknowledged_alerts ?? 0, color: unacked.length > 0 ? "var(--danger)" : "var(--success)" },
          { label: "TOTAL ALERTS", value: stats?.total_alerts ?? 0, color: "var(--text-secondary)" },
        ].map(s => (
          <div key={s.label} style={{
            flex: 1, background: "var(--bg-secondary)", border: "1px solid var(--border)",
            borderRadius: "4px", padding: "10px 14px", textAlign: "center"
          }}>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "22px", fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: "var(--text-dim)", letterSpacing: "0.1em", marginTop: "2px" }}>{s.label}</div>
          </div>
        ))}
        <div style={{ display: "flex", flexDirection: "column", gap: "6px", justifyContent: "center" }}>
          <button onClick={runCheck} disabled={checking} style={{
            background: checking ? "transparent" : "var(--accent-gold)",
            border: "1px solid var(--accent-gold)",
            color: checking ? "var(--accent-gold)" : "var(--bg-primary)",
            borderRadius: "3px", padding: "8px 18px", cursor: checking ? "not-allowed" : "pointer",
            fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "13px", letterSpacing: "0.1em",
            display: "flex", alignItems: "center", gap: "6px"
          }}>
            <RefreshCw size={13} style={{ animation: checking ? "orbSpin 1s linear infinite" : "none" }} />
            {checking ? "CHECKING..." : "RUN CHECK"}
          </button>
          {lastCheck && <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", textAlign: "center" }}>Last: {lastCheck}</div>}
        </div>
      </div>

      {error && (
        <div style={{ background: "rgba(239,68,68,0.1)", border: "1px solid var(--danger)", borderRadius: "4px", padding: "8px 12px", color: "var(--danger)", fontFamily: "JetBrains Mono, monospace", fontSize: "11px" }}>{error}</div>
      )}

      {/* Tabs */}
      <div style={{ display: "flex", gap: "0", borderBottom: "1px solid var(--border)" }}>
        {[
          { key: "entries", label: "WATCH ENTRIES", count: entries.length },
          { key: "alerts",  label: "ALERTS", count: unacked.length, alert: unacked.length > 0 },
          { key: "quick",   label: "QUICK ADD" },
        ].map(t => (
          <button key={t.key} onClick={() => setTab(t.key)} style={{
            background: "transparent", border: "none", borderBottom: tab === t.key ? "2px solid var(--accent-gold)" : "2px solid transparent",
            color: tab === t.key ? "var(--accent-gold)" : "var(--text-dim)",
            padding: "8px 16px", cursor: "pointer", fontFamily: "Rajdhani, sans-serif",
            fontWeight: 700, fontSize: "12px", letterSpacing: "0.15em",
            display: "flex", alignItems: "center", gap: "6px"
          }}>
            {t.label}
            {t.count !== undefined && (
              <span style={{
                background: t.alert ? "var(--danger)" : "var(--bg-secondary)",
                border: `1px solid ${t.alert ? "var(--danger)" : "var(--border)"}`,
                borderRadius: "10px", padding: "0 6px",
                fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                color: t.alert ? "white" : "var(--text-dim)"
              }}>{t.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* Watch Entries Tab */}
      {tab === "entries" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {/* Add Entry Form */}
          <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "4px", padding: "14px 16px" }}>
            <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "11px", letterSpacing: "0.15em", color: "var(--accent-gold)", marginBottom: "10px" }}>ADD WATCH ENTRY</div>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "flex-end" }}>
              <div>
                <FieldLabel>TYPE</FieldLabel>
                <select value={newEntry.entry_type} onChange={e => setNewEntry({...newEntry, entry_type: e.target.value})} style={inputStyle}>
                  {ENTRY_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              <div style={{ flex: 1, minWidth: "150px" }}>
                <FieldLabel>VALUE</FieldLabel>
                <input
                  value={newEntry.value}
                  onChange={e => setNewEntry({...newEntry, value: e.target.value})}
                  onKeyDown={e => e.key === "Enter" && addEntry()}
                  placeholder={ENTRY_TYPES.find(t => t.value === newEntry.entry_type)?.placeholder}
                  style={inputStyle}
                />
              </div>
              <div style={{ flex: 1, minWidth: "120px" }}>
                <FieldLabel>LABEL (optional)</FieldLabel>
                <input value={newEntry.label} onChange={e => setNewEntry({...newEntry, label: e.target.value})} placeholder="Display name" style={inputStyle} />
              </div>
              <div>
                <FieldLabel>SEVERITY</FieldLabel>
                <select value={newEntry.severity} onChange={e => setNewEntry({...newEntry, severity: e.target.value})} style={inputStyle}>
                  {["critical","high","medium","low"].map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <button onClick={addEntry} style={{
                background: "var(--accent-gold)", border: "none", color: "var(--bg-primary)",
                borderRadius: "3px", padding: "7px 14px", cursor: "pointer",
                fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px",
                display: "flex", alignItems: "center", gap: "5px", whiteSpace: "nowrap"
              }}><Plus size={12} /> ADD</button>
            </div>
          </div>

          {/* Entries List */}
          {entries.length === 0 && (
            <div style={{ color: "var(--text-dim)", fontFamily: "JetBrains Mono, monospace", fontSize: "11px", padding: "20px", textAlign: "center", border: "1px dashed var(--border)", borderRadius: "4px" }}>
              No watch entries. Add entries above or use Quick Add.
            </div>
          )}
          {entries.map(e => (
            <div key={e.id} style={{
              background: "var(--bg-secondary)", border: `1px solid ${severityColor(e.severity)}22`,
              borderRadius: "4px", padding: "12px 16px",
              display: "flex", alignItems: "center", gap: "12px"
            }}>
              <div style={{
                background: severityBg(e.severity), border: `1px solid ${severityColor(e.severity)}`,
                borderRadius: "3px", padding: "2px 8px",
                fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: severityColor(e.severity),
                letterSpacing: "0.1em", textTransform: "uppercase", whiteSpace: "nowrap"
              }}>{e.entry_type}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "13px", color: "var(--text-primary)" }}>{e.value}</div>
                {e.label && e.label !== e.value && <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "11px", color: "var(--text-dim)" }}>{e.label}</div>}
              </div>
              <div style={{
                background: severityBg(e.severity), border: `1px solid ${severityColor(e.severity)}`,
                borderRadius: "3px", padding: "2px 8px",
                fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: severityColor(e.severity),
                textTransform: "uppercase"
              }}>{e.severity}</div>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", whiteSpace: "nowrap" }}>
                {e.hit_count} hits
              </div>
              {e.last_checked && (
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", whiteSpace: "nowrap" }}>
                  {new Date(e.last_checked).toLocaleDateString()}
                </div>
              )}
              <button onClick={() => deleteEntry(e.id)} style={{
                background: "transparent", border: "1px solid var(--border)", color: "var(--danger)",
                borderRadius: "3px", padding: "4px 7px", cursor: "pointer",
                display: "flex", alignItems: "center"
              }}><Trash2 size={12} /></button>
            </div>
          ))}
        </div>
      )}

      {/* Alerts Tab */}
      {tab === "alerts" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {unacked.length > 0 && (
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button onClick={ackAll} style={{
                background: "transparent", border: "1px solid var(--border)", color: "var(--text-dim)",
                borderRadius: "3px", padding: "5px 12px", cursor: "pointer",
                fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
                display: "flex", alignItems: "center", gap: "5px"
              }}><CheckCircle size={11} /> ACKNOWLEDGE ALL</button>
            </div>
          )}
          {alerts.length === 0 && (
            <div style={{ color: "var(--text-dim)", fontFamily: "JetBrains Mono, monospace", fontSize: "11px", padding: "20px", textAlign: "center", border: "1px dashed var(--border)", borderRadius: "4px" }}>
              No alerts. Run a check to scan your asset inventory.
            </div>
          )}
          {alerts.map(a => (
            <div key={a.id} style={{
              background: a.acknowledged ? "var(--bg-secondary)" : severityBg(a.severity),
              border: `1px solid ${a.acknowledged ? "var(--border)" : severityColor(a.severity)}`,
              borderRadius: "4px", padding: "14px 16px",
              opacity: a.acknowledged ? 0.5 : 1
            }}>
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "10px" }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                    <AlertTriangle size={13} color={severityColor(a.severity)} />
                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "12px", color: severityColor(a.severity) }}>
                      {a.asset_ip}:{a.port} — {a.service}
                    </span>
                    <span style={{
                      background: severityBg(a.severity), border: `1px solid ${severityColor(a.severity)}`,
                      borderRadius: "3px", padding: "1px 6px",
                      fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: severityColor(a.severity),
                      textTransform: "uppercase"
                    }}>{a.severity}</span>
                    {a.acknowledged && <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: "var(--text-dim)" }}>ACK</span>}
                  </div>
                  <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "12px", color: "var(--text-secondary)", marginBottom: "6px" }}>{a.detail}</div>
                  {a.recommendation && (
                    <div style={{
                      background: "var(--bg-primary)", border: "1px solid var(--border)",
                      borderRadius: "3px", padding: "6px 10px",
                      fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--accent-cyan, #00d4ff)",
                      lineHeight: 1.5
                    }}>
                      <span style={{ color: "var(--text-dim)", marginRight: "6px" }}>REC:</span>{a.recommendation}
                    </div>
                  )}
                </div>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", whiteSpace: "nowrap" }}>
                  {new Date(a.created_at).toLocaleString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Quick Add Tab */}
      {tab === "quick" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "12px", color: "var(--text-dim)", marginBottom: "4px" }}>
            Common high-value watch entries. Click to add instantly.
          </div>
          {QUICK_ENTRIES.map((e, i) => {
            const already = entries.some(ex => ex.value.toLowerCase() === e.value.toLowerCase())
            return (
              <div key={i} style={{
                background: "var(--bg-secondary)", border: `1px solid ${already ? "var(--border)" : severityColor(e.severity)}33`,
                borderRadius: "4px", padding: "12px 16px",
                display: "flex", alignItems: "center", gap: "12px",
                opacity: already ? 0.5 : 1
              }}>
                <Shield size={14} color={severityColor(e.severity)} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 600, fontSize: "13px", color: "var(--text-primary)" }}>{e.label}</div>
                  <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)" }}>{e.entry_type}: {e.value}</div>
                </div>
                <span style={{
                  background: severityBg(e.severity), border: `1px solid ${severityColor(e.severity)}`,
                  borderRadius: "3px", padding: "2px 8px",
                  fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: severityColor(e.severity),
                  textTransform: "uppercase"
                }}>{e.severity}</span>
                <button onClick={() => !already && addQuick(e)} disabled={already} style={{
                  background: already ? "transparent" : "var(--accent-gold)",
                  border: "1px solid var(--accent-gold)",
                  color: already ? "var(--text-dim)" : "var(--bg-primary)",
                  borderRadius: "3px", padding: "5px 12px", cursor: already ? "default" : "pointer",
                  fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "11px"
                }}>{already ? "ADDED" : "ADD"}</button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

const inputStyle = {
  background: "var(--bg-primary)", border: "1px solid var(--border)", borderRadius: "3px",
  color: "var(--text-primary)", fontFamily: "JetBrains Mono, monospace", fontSize: "12px",
  padding: "7px 10px", width: "100%", outline: "none", boxSizing: "border-box"
}

function FieldLabel({ children }) {
  return <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", letterSpacing: "0.15em", marginBottom: "4px" }}>{children}</div>
}
