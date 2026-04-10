import { useState, useEffect } from "react"
import { pushContext } from "../SessionContext"
import api from "../api"
import { Server, Shield, AlertTriangle, CheckCircle, Clock, Tag, Trash2, Edit2, Save, X, RefreshCw } from "lucide-react"

const ASSET_API = "http://localhost:8097"

const riskColor = (r) => ({
  critical: "var(--danger)",
  high:     "#f59e0b",
  medium:   "var(--accent-cyan, #00d4ff)",
  low:      "var(--success)",
  unknown:  "var(--text-dim)"
})[r] || "var(--text-dim)"

const riskBg = (r) => ({
  critical: "rgba(239,68,68,0.08)",
  high:     "rgba(245,158,11,0.08)",
  medium:   "rgba(0,212,255,0.08)",
  low:      "rgba(34,197,94,0.08)",
  unknown:  "transparent"
})[r] || "transparent"

export default function AssetInventory() {
  const [assets, setAssets] = useState([])
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)
  const [stats, setStats] = useState(null)
  const [editing, setEditing] = useState(false)
  const [editData, setEditData] = useState({})
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState("all")

  useEffect(() => { fetchAssets(); fetchStats() }, [])

  const fetchAssets = async () => {
    setLoading(true)
    try {
      const res = await api.get(`${ASSET_API}/assets`)
      setAssets(res.data.assets || [])
    } catch(e) {}
    setLoading(false)
  }

  const fetchStats = async () => {
    try {
      const res = await api.get(`${ASSET_API}/assets/stats/summary`)
      setStats(res.data)
    } catch(e) {}
  }

  const selectAsset = async (asset) => {
    setSelected(asset)
    setEditing(false)
    try {
      const res = await api.get(`${ASSET_API}/assets/${asset.id}`)
      setDetail(res.data)
    } catch(e) {}
  }

  const startEdit = () => {
    setEditData({
      hostname: detail?.hostname || "",
      notes: detail?.notes || "",
      tags: detail?.tags || [],
      risk_level: detail?.risk_level || "unknown"
    })
    setEditing(true)
  }

  const saveEdit = async () => {
    try {
      await api.put(`${ASSET_API}/assets/${selected.id}`, editData)
      await selectAsset(selected)
      await fetchAssets()
      setEditing(false)
    } catch(e) {}
  }

  const deleteAsset = async (id) => {
    if (!window.confirm("Remove this asset from inventory?")) return
    try {
      await api.delete(`${ASSET_API}/assets/${id}`)
      setSelected(null)
      setDetail(null)
      await fetchAssets()
      await fetchStats()
    } catch(e) {}
  }

  const filtered = filter === "all" ? assets : assets.filter(a => a.risk_level === filter)

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px", height: "calc(100vh - 120px)" }}>

      {/* Stats Bar */}
      {stats && (
        <div style={{ display: "flex", gap: "12px" }}>
          {[
            { label: "TOTAL ASSETS", value: stats.total_assets, color: "var(--text-primary)" },
            { label: "CRITICAL", value: stats.by_risk?.critical || 0, color: riskColor("critical") },
            { label: "HIGH", value: stats.by_risk?.high || 0, color: riskColor("high") },
            { label: "MEDIUM", value: stats.by_risk?.medium || 0, color: riskColor("medium") },
            { label: "LOW", value: stats.by_risk?.low || 0, color: riskColor("low") },
            { label: "OPEN PORTS", value: stats.total_ports, color: "var(--accent-cyan, #00d4ff)" },
            { label: "OPEN VULNS", value: stats.open_vulns, color: stats.open_vulns > 0 ? "var(--danger)" : "var(--success)" },
          ].map(s => (
            <div key={s.label} style={{
              flex: 1, background: "var(--bg-secondary)", border: "1px solid var(--border)",
              borderRadius: "4px", padding: "10px 14px", textAlign: "center"
            }}>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "18px", fontWeight: 700, color: s.color }}>{s.value}</div>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: "var(--text-dim)", letterSpacing: "0.1em", marginTop: "2px" }}>{s.label}</div>
            </div>
          ))}
          <button onClick={() => { fetchAssets(); fetchStats() }} style={{
            background: "transparent", border: "1px solid var(--border)", borderRadius: "4px",
            color: "var(--text-dim)", cursor: "pointer", padding: "0 14px",
            display: "flex", alignItems: "center", gap: "6px",
            fontFamily: "JetBrains Mono, monospace", fontSize: "10px"
          }}>
            <RefreshCw size={12} /> REFRESH
          </button>
        </div>
      )}

      <div style={{ display: "flex", gap: "16px", flex: 1, minHeight: 0 }}>
        {/* Asset List */}
        <div style={{
          width: "280px", flexShrink: 0,
          background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "4px",
          display: "flex", flexDirection: "column"
        }}>
          <div style={{ padding: "12px 14px", borderBottom: "1px solid var(--border)" }}>
            <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px", letterSpacing: "0.15em", color: "var(--accent-gold)", marginBottom: "8px" }}>
              ASSET INVENTORY
            </div>
            <select value={filter} onChange={e => setFilter(e.target.value)} style={{
              width: "100%", background: "var(--bg-primary)", border: "1px solid var(--border)",
              borderRadius: "3px", color: "var(--text-secondary)", fontFamily: "JetBrains Mono, monospace",
              fontSize: "10px", padding: "5px 8px"
            }}>
              <option value="all">All Assets ({assets.length})</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div style={{ flex: 1, overflowY: "auto", padding: "6px" }}>
            {loading && <div style={{ color: "var(--text-dim)", fontFamily: "JetBrains Mono, monospace", fontSize: "10px", padding: "12px", textAlign: "center" }}>Loading...</div>}
            {!loading && filtered.length === 0 && (
              <div style={{ color: "var(--text-dim)", fontFamily: "JetBrains Mono, monospace", fontSize: "10px", padding: "12px", textAlign: "center", lineHeight: 1.6 }}>
                No assets yet.<br />Run an Nmap scan to<br />populate inventory.
              </div>
            )}
            {filtered.map(asset => (
              <div key={asset.id} onClick={() => selectAsset(asset)} style={{
                padding: "10px 12px", borderRadius: "3px", cursor: "pointer", marginBottom: "3px",
                background: selected?.id === asset.id ? riskBg(asset.risk_level) : "transparent",
                border: selected?.id === asset.id ? `1px solid ${riskColor(asset.risk_level)}` : "1px solid transparent",
                transition: "all 0.15s ease"
              }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "12px", color: "var(--text-primary)" }}>
                    {asset.ip}
                  </div>
                  <RiskBadge risk={asset.risk_level} small />
                </div>
                {asset.hostname && (
                  <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "10px", color: "var(--text-dim)", marginTop: "2px" }}>{asset.hostname}</div>
                )}
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", marginTop: "3px" }}>
                  {asset.port_count} ports · {asset.vuln_count} vulns · {asset.scan_count} scans
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Asset Detail */}
        <div style={{ flex: 1, overflowY: "auto" }}>
          {!selected && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--text-dim)", gap: "12px" }}>
              <Server size={40} color="var(--text-dim)" />
              <div style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "16px", letterSpacing: "0.1em" }}>SELECT AN ASSET</div>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px" }}>Run a scan to discover assets</div>
            </div>
          )}

          {selected && detail && !editing && (
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              {/* Header */}
              <div style={{
                background: "var(--bg-secondary)", border: `1px solid ${riskColor(detail.risk_level)}`,
                borderRadius: "4px", padding: "16px 20px",
                display: "flex", alignItems: "flex-start", justifyContent: "space-between"
              }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "20px", color: "var(--text-primary)" }}>{detail.ip}</span>
                    <RiskBadge risk={detail.risk_level} />
                  </div>
                  {detail.hostname && <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "13px", color: "var(--text-secondary)" }}>{detail.hostname}</div>}
                  <div style={{ display: "flex", gap: "16px", marginTop: "8px" }}>
                    <Stat label="FIRST SEEN" value={new Date(detail.first_seen).toLocaleDateString()} />
                    <Stat label="LAST SEEN" value={new Date(detail.last_seen).toLocaleDateString()} />
                    <Stat label="SCAN COUNT" value={detail.scan_count} />
                  </div>
                  {detail.tags?.length > 0 && (
                    <div style={{ display: "flex", gap: "6px", marginTop: "8px", flexWrap: "wrap" }}>
                      {detail.tags.map(t => (
                        <span key={t} style={{
                          background: "var(--bg-primary)", border: "1px solid var(--border)",
                          borderRadius: "10px", padding: "2px 8px",
                          fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)"
                        }}>{t}</span>
                      ))}
                    </div>
                  )}
                  {detail.notes && <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "11px", color: "var(--text-dim)", marginTop: "8px" }}>{detail.notes}</div>}
                </div>
                <div style={{ display: "flex", gap: "6px" }}>
                  <button onClick={startEdit} style={iconBtn("var(--accent-cyan, #00d4ff)")}><Edit2 size={13} /></button>
                  <button onClick={() => deleteAsset(detail.id)} style={iconBtn("var(--danger)")}><Trash2 size={13} /></button>
                </div>
              </div>

              {/* Ports */}
              <Panel title={`OPEN PORTS (${detail.ports?.length || 0})`}>
                {detail.ports?.length === 0 && <Empty>No open ports recorded</Empty>}
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  {detail.ports?.map(p => (
                    <div key={p.id} style={{
                      display: "flex", alignItems: "center", gap: "12px",
                      padding: "7px 10px", background: "var(--bg-primary)",
                      borderRadius: "3px", border: "1px solid var(--border)"
                    }}>
                      <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "12px", color: "var(--accent-cyan, #00d4ff)", width: "80px" }}>{p.port}/{p.protocol}</span>
                      <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: "var(--text-secondary)", flex: 1 }}>{p.service}</span>
                      {p.version && <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)" }}>{p.version}</span>}
                      <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--success)" }}>{p.state}</span>
                    </div>
                  ))}
                </div>
              </Panel>

              {/* Risk History */}
              {detail.risk_history?.length > 0 && (
                <Panel title="RISK HISTORY">
                  <div style={{ display: "flex", gap: "4px", alignItems: "flex-end", height: "40px" }}>
                    {detail.risk_history.slice().reverse().map((h, i) => (
                      <div key={i} title={`${h.risk_level} - ${new Date(h.recorded_at).toLocaleDateString()}`} style={{
                        flex: 1, borderRadius: "2px",
                        background: riskColor(h.risk_level),
                        height: ({ critical: "100%", high: "75%", medium: "50%", low: "25%", unknown: "10%" })[h.risk_level] || "10%",
                        opacity: 0.7, cursor: "default", transition: "opacity 0.2s",
                        minWidth: "4px"
                      }} />
                    ))}
                  </div>
                  <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", marginTop: "4px" }}>
                    Last {detail.risk_history.length} scans
                  </div>
                </Panel>
              )}
            </div>
          )}

          {/* Edit panel */}
          {selected && editing && (
            <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--accent-gold)", borderRadius: "4px", padding: "20px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
                <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "14px", letterSpacing: "0.15em", color: "var(--accent-gold)" }}>EDIT ASSET — {detail.ip}</span>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button onClick={() => setEditing(false)} style={iconBtn("var(--text-dim)")}><X size={13} /></button>
                  <button onClick={saveEdit} style={{
                    background: "var(--accent-gold)", border: "none", color: "var(--bg-primary)",
                    borderRadius: "3px", padding: "6px 14px", cursor: "pointer",
                    fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px",
                    display: "flex", alignItems: "center", gap: "5px"
                  }}><Save size={12} /> SAVE</button>
                </div>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                <div>
                  <FieldLabel>HOSTNAME</FieldLabel>
                  <input value={editData.hostname} onChange={e => setEditData({...editData, hostname: e.target.value})} style={inputStyle} />
                </div>
                <div>
                  <FieldLabel>RISK LEVEL</FieldLabel>
                  <select value={editData.risk_level} onChange={e => setEditData({...editData, risk_level: e.target.value})} style={inputStyle}>
                    {["critical","high","medium","low","unknown"].map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
                <div>
                  <FieldLabel>TAGS (comma separated)</FieldLabel>
                  <input value={editData.tags?.join(", ") || ""} onChange={e => setEditData({...editData, tags: e.target.value.split(",").map(t => t.trim()).filter(Boolean)})} style={inputStyle} placeholder="e.g. critical-infrastructure, DMZ, workstation" />
                </div>
                <div>
                  <FieldLabel>NOTES</FieldLabel>
                  <textarea value={editData.notes} onChange={e => setEditData({...editData, notes: e.target.value})} style={{ ...inputStyle, height: "80px", resize: "vertical" }} />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function RiskBadge({ risk, small }) {
  return (
    <span style={{
      background: riskBg(risk), border: `1px solid ${riskColor(risk)}`,
      borderRadius: "3px", padding: small ? "1px 6px" : "2px 8px",
      fontFamily: "JetBrains Mono, monospace", fontSize: small ? "8px" : "10px",
      color: riskColor(risk), letterSpacing: "0.1em", textTransform: "uppercase"
    }}>{risk}</span>
  )
}

function Panel({ title, children }) {
  return (
    <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "4px" }}>
      <div style={{ padding: "10px 16px", borderBottom: "1px solid var(--border)" }}>
        <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "11px", letterSpacing: "0.15em", color: "var(--accent-gold)" }}>{title}</span>
      </div>
      <div style={{ padding: "12px 16px" }}>{children}</div>
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div>
      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: "var(--text-dim)", letterSpacing: "0.1em" }}>{label}</div>
      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "12px", color: "var(--text-secondary)" }}>{value}</div>
    </div>
  )
}

function Empty({ children }) {
  return <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)", padding: "8px" }}>{children}</div>
}

const inputStyle = {
  background: "var(--bg-primary)", border: "1px solid var(--border)", borderRadius: "3px",
  color: "var(--text-primary)", fontFamily: "JetBrains Mono, monospace", fontSize: "12px",
  padding: "7px 10px", width: "100%", outline: "none", boxSizing: "border-box"
}

const iconBtn = (color) => ({
  background: "transparent", border: `1px solid ${color}`, color,
  borderRadius: "3px", padding: "5px 7px", cursor: "pointer",
  display: "flex", alignItems: "center", justifyContent: "center"
})

function FieldLabel({ children }) {
  return <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", letterSpacing: "0.15em", marginBottom: "4px" }}>{children}</div>
}
