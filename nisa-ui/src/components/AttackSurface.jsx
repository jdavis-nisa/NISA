import { useState, useEffect } from "react"
import { pushContext } from "../SessionContext"
import api from "../api"
import { RefreshCw, AlertTriangle, Shield, Activity, Database, Globe, Monitor, Server, Wifi } from "lucide-react"

const ASSET_API = "http://localhost:8097"

const SERVICE_CATEGORIES = {
  "Remote Access": ["rdp", "ssh", "vnc", "telnet", "ms-wbt-server", "remote"],
  "Web":           ["http", "https", "www", "nginx", "apache", "iis", "tomcat", "web"],
  "File Sharing":  ["smb", "ftp", "sftp", "nfs", "netbios", "microsoft-ds", "cifs"],
  "Database":      ["mysql", "postgres", "mssql", "oracle", "mongodb", "redis", "db"],
  "Mail":          ["smtp", "imap", "pop3", "mail", "exchange"],
  "Other":         []
}

const CATEGORY_ICONS = {
  "Remote Access": Monitor,
  "Web":           Globe,
  "File Sharing":  Server,
  "Database":      Database,
  "Mail":          Activity,
  "Other":         Wifi
}

const riskColor = (r) => ({
  critical: "var(--danger)",
  high:     "#f59e0b",
  medium:   "var(--accent-cyan, #00d4ff)",
  low:      "var(--success)",
  unknown:  "var(--text-dim)"
})[r] || "var(--text-dim)"

const riskBg = (r) => ({
  critical: "rgba(239,68,68,0.15)",
  high:     "rgba(245,158,11,0.15)",
  medium:   "rgba(0,212,255,0.15)",
  low:      "rgba(34,197,94,0.15)",
  unknown:  "rgba(255,255,255,0.03)"
})[r] || "transparent"

const riskScore = (r) => ({ critical: 4, high: 3, medium: 2, low: 1, unknown: 0 })[r] || 0

function categorizeService(service) {
  const s = (service || "").toLowerCase()
  for (const [cat, keywords] of Object.entries(SERVICE_CATEGORIES)) {
    if (cat === "Other") continue
    if (keywords.some(k => s.includes(k))) return cat
  }
  return "Other"
}

export default function AttackSurface() {
  const [assets, setAssets] = useState([])
  const [loading, setLoading] = useState(false)
  const [lastRefresh, setLastRefresh] = useState(null)

  useEffect(() => { fetchData() }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await api.get(`${ASSET_API}/assets`)
      const raw = res.data.assets || []
      // Fetch full detail for each asset to get ports
      const detailed = await Promise.all(
        raw.map(async a => {
          try {
            const d = await api.get(`${ASSET_API}/assets/${a.id}`)
            return d.data
          } catch { return { ...a, ports: [] } }
        })
      )
      setAssets(detailed)
      setLastRefresh(new Date().toLocaleTimeString())
      if (detailed.length > 0) {
        const critical = detailed.filter(a => a.risk_level === "critical").length
        const high = detailed.filter(a => a.risk_level === "high").length
        pushContext({
          tab: "Attack Surface",
          operation: "Surface Map Refresh",
          summary: `Attack surface: ${detailed.length} assets, ${critical} critical, ${high} high risk`,
          detail: null
        })
      }
    } catch(e) {}
    setLoading(false)
  }

  // Compute surface data
  const categories = Object.keys(SERVICE_CATEGORIES)

  const assetRows = assets.map(asset => {
    const catMap = {}
    for (const cat of categories) catMap[cat] = []
    for (const port of (asset.ports || [])) {
      const cat = categorizeService(port.service)
      catMap[cat].push(port)
    }
    return { asset, catMap }
  }).sort((a, b) => riskScore(b.asset.risk_level) - riskScore(a.asset.risk_level))

  // Vector breakdown
  const vectorCounts = {}
  for (const cat of categories) vectorCounts[cat] = 0
  for (const { catMap } of assetRows) {
    for (const cat of categories) {
      if (catMap[cat].length > 0) vectorCounts[cat]++
    }
  }

  // Risk distribution
  const riskCounts = { critical: 0, high: 0, medium: 0, low: 0, unknown: 0 }
  for (const a of assets) riskCounts[a.risk_level || "unknown"]++

  // Top exposed
  const topExposed = [...assets]
    .sort((a, b) => {
      const rs = riskScore(b.risk_level) - riskScore(a.risk_level)
      if (rs !== 0) return rs
      return (b.port_count || 0) - (a.port_count || 0)
    })
    .slice(0, 5)

  // Most common services
  const serviceCounts = {}
  for (const a of assets) {
    for (const p of (a.ports || [])) {
      const svc = p.service || "unknown"
      serviceCounts[svc] = (serviceCounts[svc] || 0) + 1
    }
  }
  const topServices = Object.entries(serviceCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)

  const totalPorts = assets.reduce((s, a) => s + (a.ports?.length || 0), 0)

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "22px", letterSpacing: "0.1em", color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "10px" }}>
            <Shield size={20} color="var(--accent-gold)" /> ATTACK SURFACE MAP
          </div>
          <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "12px", color: "var(--text-dim)", marginTop: "2px" }}>
            Live exposure analysis from asset inventory
            {lastRefresh && ` · Refreshed ${lastRefresh}`}
          </div>
        </div>
        <button onClick={fetchData} disabled={loading} style={{
          background: "transparent", border: "1px solid var(--accent-gold)", color: "var(--accent-gold)",
          borderRadius: "3px", padding: "7px 16px", cursor: loading ? "not-allowed" : "pointer",
          fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px", letterSpacing: "0.1em",
          display: "flex", alignItems: "center", gap: "6px"
        }}>
          <RefreshCw size={12} style={{ animation: loading ? "orbSpin 1s linear infinite" : "none" }} />
          REFRESH
        </button>
      </div>

      {assets.length === 0 && !loading && (
        <div style={{
          background: "var(--bg-secondary)", border: "1px dashed var(--border)", borderRadius: "4px",
          padding: "40px", textAlign: "center", color: "var(--text-dim)"
        }}>
          <Shield size={36} color="var(--text-dim)" style={{ marginBottom: "12px" }} />
          <div style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "16px", letterSpacing: "0.1em" }}>NO ASSETS IN INVENTORY</div>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px", marginTop: "6px" }}>Run an Nmap scan to populate the attack surface map</div>
        </div>
      )}

      {assets.length > 0 && (
        <>
          {/* Summary Stats */}
          <div style={{ display: "flex", gap: "10px" }}>
            {[
              { label: "TOTAL ASSETS", value: assets.length, color: "var(--text-primary)" },
              { label: "CRITICAL", value: riskCounts.critical, color: riskColor("critical") },
              { label: "HIGH", value: riskCounts.high, color: riskColor("high") },
              { label: "MEDIUM", value: riskCounts.medium, color: riskColor("medium") },
              { label: "LOW", value: riskCounts.low, color: riskColor("low") },
              { label: "EXPOSED PORTS", value: totalPorts, color: "var(--accent-cyan, #00d4ff)" },
            ].map(s => (
              <div key={s.label} style={{
                flex: 1, background: "var(--bg-secondary)", border: "1px solid var(--border)",
                borderRadius: "4px", padding: "10px", textAlign: "center"
              }}>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "20px", fontWeight: 700, color: s.color }}>{s.value}</div>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: "var(--text-dim)", letterSpacing: "0.08em", marginTop: "2px" }}>{s.label}</div>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: "16px" }}>
            {/* Left: Exposure Matrix */}
            <div style={{ flex: 2, display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "4px" }}>
                <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
                  <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px", letterSpacing: "0.15em", color: "var(--accent-gold)" }}>EXPOSURE MATRIX</span>
                </div>
                <div style={{ padding: "12px 16px", overflowX: "auto" }}>
                  {/* Header row */}
                  <div style={{ display: "flex", gap: "4px", marginBottom: "6px", paddingLeft: "140px" }}>
                    {categories.map(cat => {
                      const Icon = CATEGORY_ICONS[cat]
                      return (
                        <div key={cat} style={{
                          width: "80px", flexShrink: 0, textAlign: "center",
                          fontFamily: "JetBrains Mono, monospace", fontSize: "8px",
                          color: "var(--text-dim)", letterSpacing: "0.05em",
                          display: "flex", flexDirection: "column", alignItems: "center", gap: "3px"
                        }}>
                          <Icon size={11} color="var(--text-dim)" />
                          {cat.toUpperCase()}
                        </div>
                      )
                    })}
                  </div>
                  {/* Asset rows */}
                  {assetRows.map(({ asset, catMap }) => (
                    <div key={asset.id} style={{ display: "flex", gap: "4px", marginBottom: "4px", alignItems: "center" }}>
                      {/* Asset label */}
                      <div style={{
                        width: "140px", flexShrink: 0, paddingRight: "8px",
                        display: "flex", alignItems: "center", gap: "6px"
                      }}>
                        <div style={{
                          width: "6px", height: "6px", borderRadius: "50%",
                          background: riskColor(asset.risk_level), flexShrink: 0
                        }} />
                        <div>
                          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-primary)" }}>{asset.ip}</div>
                          {asset.hostname && <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: "var(--text-dim)" }}>{asset.hostname.split(".")[0]}</div>}
                        </div>
                      </div>
                      {/* Category cells */}
                      {categories.map(cat => {
                        const ports = catMap[cat]
                        const hasExposure = ports.length > 0
                        const cellRisk = hasExposure ? (
                          ["rdp","telnet","vnc"].some(s => ports.some(p => (p.service||"").toLowerCase().includes(s))) ? "critical" :
                          ["smb","ftp","ssh"].some(s => ports.some(p => (p.service||"").toLowerCase().includes(s))) ? "high" :
                          "medium"
                        ) : null
                        return (
                          <div key={cat} title={hasExposure ? ports.map(p => `${p.port}/${p.service}`).join(", ") : "No exposure"} style={{
                            width: "80px", height: "32px", flexShrink: 0,
                            borderRadius: "3px",
                            background: hasExposure ? riskBg(cellRisk) : "var(--bg-primary)",
                            border: `1px solid ${hasExposure ? riskColor(cellRisk) : "var(--border)"}`,
                            display: "flex", alignItems: "center", justifyContent: "center",
                            cursor: hasExposure ? "default" : "default",
                            transition: "all 0.15s ease"
                          }}>
                            {hasExposure && (
                              <div style={{ textAlign: "center" }}>
                                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: riskColor(cellRisk), fontWeight: 700 }}>{ports.length}</div>
                                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "7px", color: riskColor(cellRisk) }}>port{ports.length > 1 ? "s" : ""}</div>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  ))}
                </div>
              </div>

              {/* Attack Vector Breakdown */}
              <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "4px" }}>
                <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
                  <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px", letterSpacing: "0.15em", color: "var(--accent-gold)" }}>ATTACK VECTORS</span>
                </div>
                <div style={{ padding: "12px 16px", display: "flex", flexDirection: "column", gap: "8px" }}>
                  {categories.map(cat => {
                    const count = vectorCounts[cat]
                    const pct = assets.length > 0 ? (count / assets.length) * 100 : 0
                    const Icon = CATEGORY_ICONS[cat]
                    return (
                      <div key={cat} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <Icon size={13} color={count > 0 ? "var(--text-secondary)" : "var(--text-dim)"} style={{ width: "16px", flexShrink: 0 }} />
                        <div style={{ width: "100px", fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: count > 0 ? "var(--text-secondary)" : "var(--text-dim)" }}>{cat}</div>
                        <div style={{ flex: 1, background: "var(--bg-primary)", borderRadius: "2px", height: "6px", overflow: "hidden" }}>
                          <div style={{
                            width: `${pct}%`, height: "100%", borderRadius: "2px",
                            background: pct > 60 ? "var(--danger)" : pct > 30 ? "#f59e0b" : "var(--success)",
                            transition: "width 0.5s ease"
                          }} />
                        </div>
                        <div style={{ width: "60px", textAlign: "right", fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: count > 0 ? "var(--text-secondary)" : "var(--text-dim)" }}>
                          {count}/{assets.length} assets
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* Right: Summary Panels */}
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "12px" }}>
              {/* Risk Distribution */}
              <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "4px" }}>
                <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
                  <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px", letterSpacing: "0.15em", color: "var(--accent-gold)" }}>RISK DISTRIBUTION</span>
                </div>
                <div style={{ padding: "12px 16px", display: "flex", flexDirection: "column", gap: "8px" }}>
                  {["critical","high","medium","low"].map(r => (
                    <div key={r} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <div style={{ width: "55px", fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: riskColor(r), textTransform: "uppercase", letterSpacing: "0.1em" }}>{r}</div>
                      <div style={{ flex: 1, background: "var(--bg-primary)", borderRadius: "2px", height: "8px", overflow: "hidden" }}>
                        <div style={{
                          width: assets.length > 0 ? `${(riskCounts[r] / assets.length) * 100}%` : "0%",
                          height: "100%", borderRadius: "2px", background: riskColor(r),
                          transition: "width 0.5s ease"
                        }} />
                      </div>
                      <div style={{ width: "20px", textAlign: "right", fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: riskColor(r), fontWeight: 700 }}>{riskCounts[r]}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Top Exposed Assets */}
              <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "4px" }}>
                <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
                  <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px", letterSpacing: "0.15em", color: "var(--accent-gold)" }}>TOP EXPOSED ASSETS</span>
                </div>
                <div style={{ padding: "8px 16px", display: "flex", flexDirection: "column", gap: "6px" }}>
                  {topExposed.map((a, i) => (
                    <div key={a.id} style={{ display: "flex", alignItems: "center", gap: "8px", padding: "6px 8px", background: "var(--bg-primary)", borderRadius: "3px", border: `1px solid ${riskColor(a.risk_level)}22` }}>
                      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", width: "14px" }}>#{i+1}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: "var(--text-primary)" }}>{a.ip}</div>
                        {a.hostname && <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: "var(--text-dim)" }}>{a.hostname}</div>}
                      </div>
                      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)" }}>{a.port_count || a.ports?.length || 0}p</div>
                      <div style={{
                        background: riskBg(a.risk_level), border: `1px solid ${riskColor(a.risk_level)}`,
                        borderRadius: "2px", padding: "1px 5px",
                        fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: riskColor(a.risk_level),
                        textTransform: "uppercase"
                      }}>{a.risk_level}</div>
                    </div>
                  ))}
                  {topExposed.length === 0 && <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)", padding: "8px" }}>No assets ranked yet</div>}
                </div>
              </div>

              {/* Most Common Services */}
              <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "4px" }}>
                <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
                  <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px", letterSpacing: "0.15em", color: "var(--accent-gold)" }}>COMMON SERVICES</span>
                </div>
                <div style={{ padding: "8px 16px", display: "flex", flexDirection: "column", gap: "5px" }}>
                  {topServices.map(([svc, count]) => (
                    <div key={svc} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <div style={{ flex: 1, fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-secondary)" }}>{svc}</div>
                      <div style={{ width: "60px", background: "var(--bg-primary)", borderRadius: "2px", height: "5px", overflow: "hidden" }}>
                        <div style={{
                          width: `${(count / (topServices[0]?.[1] || 1)) * 100}%`,
                          height: "100%", borderRadius: "2px", background: "var(--accent-cyan, #00d4ff)"
                        }} />
                      </div>
                      <div style={{ width: "20px", textAlign: "right", fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)" }}>{count}</div>
                    </div>
                  ))}
                  {topServices.length === 0 && <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)", padding: "8px" }}>No services detected</div>}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
