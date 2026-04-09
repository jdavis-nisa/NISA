import { useState, useEffect, useRef } from "react"
import { pushContext } from "../SessionContext"
import { Shield, Play, Clock, TrendingUp, ChevronRight, CheckCircle, XCircle, Minus, RefreshCw } from "lucide-react"
import api from "../api"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"

const RT_API = "http://localhost:8084"

export default function RedTeam() {
  const [sessions, setSessions] = useState([])
  const [history, setHistory] = useState([])
  const [activeSession, setActiveSession] = useState(null)
  const [liveData, setLiveData] = useState(null)
  const pollRef = useRef(null)

  useEffect(() => {
    fetchSessions()
    fetchHistory()
  }, [])

  useEffect(() => {
    if (activeSession && liveData?.status === "running") {
      pollRef.current = setInterval(async () => {
        try {
          const res = await api.get(`${RT_API}/session/${activeSession}`)
          setLiveData(res.data)
          if (res.data.status !== "running") {
            clearInterval(pollRef.current)
            fetchSessions()
            fetchHistory()
            pushContext({
              tab: 'Red Team',
              operation: 'Red Team Evaluation',
              summary: `Red team complete - score: ${res.data.score_passed ?? 0}/${res.data.score_total ?? 0} passed. Status: ${res.data.status}`,
              detail: null
            })
          }
        } catch (e) {}
      }, 3000)
    }
    return () => clearInterval(pollRef.current)
  }, [activeSession, liveData?.status])

  const fetchSessions = async () => {
    try {
      const res = await api.get(`${RT_API}/sessions`)
      setSessions(res.data.sessions || [])
    } catch (e) {}
  }

  const fetchHistory = async () => {
    try {
      const res = await api.get(`${RT_API}/history`)
      setHistory(res.data.history || [])
    } catch (e) {}
  }

  const launchAttack = async (config) => {
    try {
      const res = await api.post(`${RT_API}/run`, config)
      const sid = res.data.session_id
      setActiveSession(sid)
      setLiveData({ status: "running", turns: [], score_passed: 0, score_total: 0 })
    } catch (e) {
      console.error(e)
    }
  }

  // Build chart data from history
  const chartData = {}
  history.forEach(h => {
    if (!chartData[h.version]) chartData[h.version] = { version: h.version }
    chartData[h.version][h.attack_type] = h.avg_score
  })
  const chartArray = Object.values(chartData)

  // Add known historical data points
  const fullChart = [
    { version: "v0.1.0", PyRIT: 100, OWASP: null },
    { version: "v0.2.0", PyRIT: 100, OWASP: 81 },
    ...chartArray.filter(d => !["v0.1.0", "v0.2.0"].includes(d.version))
  ]

  return (
    <div className="fade-in" style={{ maxWidth: "1100px", margin: "0 auto" }}>
      <PageHeader
        icon={Shield}
        title="RED TEAM OPERATIONS"
        subtitle="NISA Security Testing Suite — adversarial evaluation and regression tracking"
      />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
        {/* Panel 1 - Launch */}
        <LaunchPanel onLaunch={launchAttack} />

        {/* Panel 2 - Live Results */}
        <LivePanel sessionId={activeSession} liveData={liveData} />
      </div>

      {/* Panel 3 - History */}
      <HistoryPanel sessions={sessions} onRefresh={fetchSessions} onSelect={(sid) => {
        setActiveSession(sid)
        api.get(`${RT_API}/session/${sid}`).then(r => setLiveData(r.data))
      }} />

      {/* Regression Chart */}
      <RegressionChart data={fullChart} />
    </div>
  )
}

function LaunchPanel({ onLaunch }) {
  const [attackType, setAttackType] = useState("pyrit")
  const [intensity, setIntensity] = useState("standard")
  const [loading, setLoading] = useState(false)

  const launch = async () => {
    setLoading(true)
    await onLaunch({
      attack_type: attackType,
      target: "http://localhost:8081",
      intensity
    })
    setLoading(false)
  }

  const attacks = [
    { value: "pyrit", label: "PyRIT Multi-Turn", desc: "Adversarial conversation sequences" },
    { value: "owasp", label: "OWASP Evaluation", desc: "LLM Top 10 test suite (50 cases)" },
    { value: "garak", label: "Garak Probes", desc: "DAN + encoding injection probes" },
  ]

  const intensities = [
    { value: "quick", label: "Quick", desc: "2 sequences" },
    { value: "standard", label: "Standard", desc: "4 sequences" },
    { value: "deep", label: "Deep", desc: "6 sequences" },
  ]

  return (
    <Panel title="LAUNCH ATTACK">
      <div style={{ marginBottom: "14px" }}>
        <FieldLabel>ATTACK TYPE</FieldLabel>
        {attacks.map(a => (
          <div
            key={a.value}
            onClick={() => setAttackType(a.value)}
            style={{
              padding: "8px 12px",
              marginBottom: "6px",
              border: `1px solid ${attackType === a.value ? "var(--accent-gold)" : "var(--border)"}`,
              borderRadius: "2px",
              background: attackType === a.value ? "var(--accent-gold-glow)" : "var(--bg-secondary)",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            <div style={{
              fontFamily: "Rajdhani, sans-serif",
              fontWeight: 600,
              fontSize: "12px",
              color: attackType === a.value ? "var(--accent-gold)" : "var(--text-secondary)",
              letterSpacing: "0.1em",
            }}>{a.label}</div>
            <div style={{
              fontFamily: "Outfit, sans-serif",
              fontSize: "11px",
              color: "var(--text-dim)",
            }}>{a.desc}</div>
          </div>
        ))}
      </div>

      <div style={{ marginBottom: "16px" }}>
        <FieldLabel>INTENSITY</FieldLabel>
        <div style={{ display: "flex", gap: "6px" }}>
          {intensities.map(i => (
            <button
              key={i.value}
              onClick={() => setIntensity(i.value)}
              style={{
                flex: 1,
                padding: "6px 8px",
                border: `1px solid ${intensity === i.value ? "var(--accent-gold)" : "var(--border)"}`,
                borderRadius: "2px",
                background: intensity === i.value ? "var(--accent-gold-glow)" : "var(--bg-secondary)",
                color: intensity === i.value ? "var(--accent-gold)" : "var(--text-dim)",
                fontFamily: "Rajdhani, sans-serif",
                fontWeight: 600,
                fontSize: "11px",
                letterSpacing: "0.1em",
                cursor: "pointer",
              }}
            >
              {i.label}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={launch}
        disabled={loading}
        style={{
          width: "100%",
          padding: "12px",
          background: loading ? "var(--bg-elevated)" : "rgba(232, 64, 64, 0.1)",
          border: `1px solid ${loading ? "var(--border)" : "var(--danger)"}`,
          borderRadius: "2px",
          color: loading ? "var(--text-dim)" : "var(--danger)",
          fontFamily: "Rajdhani, sans-serif",
          fontWeight: 700,
          fontSize: "14px",
          letterSpacing: "0.2em",
          cursor: loading ? "not-allowed" : "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "8px",
          transition: "all 0.2s",
        }}
      >
        {loading ? (
          <><RefreshCw size={14} style={{ animation: "spin 0.8s linear infinite" }} /> LAUNCHING...</>
        ) : (
          <><Play size={14} /> RUN RED TEAM</>
        )}
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </button>
    </Panel>
  )
}

function LivePanel({ sessionId, liveData }) {
  if (!liveData) return (
    <Panel title="LIVE RESULTS FEED">
      <div style={{
        height: "200px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "JetBrains Mono, monospace",
        fontSize: "11px",
        color: "var(--text-dim)",
        letterSpacing: "0.1em",
      }}>
        AWAITING ATTACK LAUNCH
      </div>
    </Panel>
  )

  const total = liveData.score_total || 0
  const passed = liveData.score_passed || 0
  const pct = total > 0 ? Math.round(passed / total * 100) : 0
  const turns = liveData.turns || []

  const resultColor = {
    DEFENDED: "var(--success)",
    BREACHED: "var(--danger)",
    NEUTRAL: "var(--warning)",
    ERROR: "var(--text-dim)",
    COMPLETE: "var(--accent-cyan)",
  }

  return (
    <Panel title="LIVE RESULTS FEED">
      {/* Score bar */}
      <div style={{ marginBottom: "12px" }}>
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: "4px",
        }}>
          <span style={{
            fontFamily: "JetBrains Mono, monospace",
            fontSize: "10px",
            color: "var(--text-dim)",
          }}>DEFENSE SCORE</span>
          <span style={{
            fontFamily: "Rajdhani, sans-serif",
            fontWeight: 700,
            fontSize: "16px",
            color: pct >= 80 ? "var(--success)" : pct >= 50 ? "var(--warning)" : "var(--danger)",
          }}>{passed}/{total} ({pct}%)</span>
        </div>
        <div style={{
          height: "4px",
          background: "var(--bg-elevated)",
          borderRadius: "2px",
          overflow: "hidden",
        }}>
          <div style={{
            height: "100%",
            width: `${pct}%`,
            background: pct >= 80 ? "var(--success)" : pct >= 50 ? "var(--warning)" : "var(--danger)",
            transition: "width 0.5s ease",
          }} />
        </div>
      </div>

      {/* Status */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "6px",
        marginBottom: "10px",
      }}>
        <div style={{
          width: "6px", height: "6px",
          borderRadius: "50%",
          background: liveData.status === "running" ? "var(--warning)" :
                      liveData.status === "complete" ? "var(--success)" : "var(--danger)",
          animation: liveData.status === "running" ? "pulse 1s infinite" : "none",
        }} />
        <span style={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "10px",
          color: "var(--text-dim)",
          letterSpacing: "0.1em",
        }}>{liveData.status?.toUpperCase()}</span>
        <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }`}</style>
      </div>

      {/* Turn feed */}
      <div style={{ maxHeight: "220px", overflowY: "auto" }}>
        {turns.length === 0 ? (
          <div style={{
            fontFamily: "JetBrains Mono, monospace",
            fontSize: "10px",
            color: "var(--text-dim)",
            padding: "8px 0",
          }}>Waiting for first turn...</div>
        ) : (
          turns.map((t, i) => (
            <div key={i} style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "4px 0",
              borderBottom: "1px solid var(--border)",
              fontFamily: "JetBrains Mono, monospace",
              fontSize: "10px",
            }}>
              <span style={{ color: "var(--text-dim)", minWidth: "16px" }}>
                [{t.turn}]
              </span>
              <span style={{ color: "var(--text-secondary)", flex: 1 }}>
                {t.attack}
              </span>
              <span style={{
                color: resultColor[t.result] || "var(--text-dim)",
                fontWeight: 600,
              }}>
                {t.result === "DEFENDED" ? "✓" : t.result === "BREACHED" ? "✗" : "~"} {t.result}
              </span>
            </div>
          ))
        )}
      </div>
    </Panel>
  )
}

function HistoryPanel({ sessions, onRefresh, onSelect }) {
  return (
    <Panel title="SESSION HISTORY">
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              {["DATE", "ATTACK TYPE", "SCORE", "PCT", "DURATION", "STATUS"].map(h => (
                <th key={h} style={thStyle}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sessions.length === 0 ? (
              <tr>
                <td colSpan={6} style={{
                  ...tdStyle,
                  textAlign: "center",
                  color: "var(--text-dim)",
                  padding: "20px",
                }}>No sessions yet — launch your first red team attack</td>
              </tr>
            ) : (
              sessions.map((s, i) => (
                <tr
                  key={i}
                  onClick={() => onSelect(s.session_id)}
                  style={{
                    cursor: "pointer",
                    background: i % 2 === 0 ? "transparent" : "var(--bg-secondary)",
                  }}
                >
                  <td style={tdStyle}>{s.timestamp?.slice(0, 16)}</td>
                  <td style={tdStyle}>{s.attack_type?.toUpperCase()}</td>
                  <td style={tdStyle}>{s.score_passed}/{s.score_total}</td>
                  <td style={{
                    ...tdStyle,
                    color: s.score_pct >= 80 ? "var(--success)" :
                           s.score_pct >= 50 ? "var(--warning)" : "var(--danger)",
                    fontWeight: 600,
                  }}>{s.score_pct ? `${Math.round(s.score_pct)}%` : "--"}</td>
                  <td style={tdStyle}>
                    {s.duration_seconds ? `${Math.round(s.duration_seconds)}s` : "--"}
                  </td>
                  <td style={{
                    ...tdStyle,
                    color: s.status === "complete" ? "var(--success)" :
                           s.status === "running" ? "var(--warning)" : "var(--text-dim)",
                  }}>{s.status?.toUpperCase()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <button onClick={onRefresh} style={{
        marginTop: "8px",
        background: "transparent",
        border: "none",
        color: "var(--text-dim)",
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        gap: "4px",
        fontFamily: "JetBrains Mono, monospace",
        fontSize: "9px",
        letterSpacing: "0.1em",
      }}>
        <RefreshCw size={10} /> REFRESH
      </button>
    </Panel>
  )
}

function RegressionChart({ data }) {
  return (
    <div style={{
      border: "1px solid var(--border)",
      borderRadius: "4px",
      background: "var(--bg-panel)",
      overflow: "hidden",
      marginTop: "16px",
    }}>
      <div style={{
        padding: "8px 14px",
        borderBottom: "1px solid var(--border)",
        background: "var(--bg-secondary)",
        display: "flex",
        alignItems: "center",
        gap: "8px",
      }}>
        <TrendingUp size={12} color="var(--accent-gold)" />
        <span style={{
          fontFamily: "Rajdhani, sans-serif",
          fontWeight: 600,
          fontSize: "11px",
          letterSpacing: "0.15em",
          color: "var(--text-dim)",
        }}>SECURITY REGRESSION — DEFENSE SCORE BY VERSION</span>
      </div>
      <div style={{ padding: "16px" }}>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="version"
              tick={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, fill: "var(--text-dim)" }}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, fill: "var(--text-dim)" }}
              tickFormatter={v => `${v}%`}
            />
            <Tooltip
              contentStyle={{
                background: "var(--bg-elevated)",
                border: "1px solid var(--border)",
                fontFamily: "JetBrains Mono, monospace",
                fontSize: "11px",
              }}
              formatter={(value) => [`${value}%`]}
            />
            <Legend
              wrapperStyle={{
                fontFamily: "JetBrains Mono, monospace",
                fontSize: "10px",
              }}
            />
            <Line
              type="monotone"
              dataKey="PyRIT"
              stroke="var(--accent-gold)"
              strokeWidth={2}
              dot={{ fill: "var(--accent-gold)", r: 4 }}
              connectNulls
            />
            <Line
              type="monotone"
              dataKey="OWASP"
              stroke="var(--accent-cyan)"
              strokeWidth={2}
              dot={{ fill: "var(--accent-cyan)", r: 4 }}
              connectNulls
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
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

const thStyle = {
  fontFamily: "Rajdhani, sans-serif",
  fontWeight: 600,
  fontSize: "10px",
  letterSpacing: "0.15em",
  color: "var(--text-dim)",
  textAlign: "left",
  padding: "6px 10px",
  borderBottom: "1px solid var(--border)",
  background: "var(--bg-secondary)",
  whiteSpace: "nowrap",
}

const tdStyle = {
  fontFamily: "JetBrains Mono, monospace",
  fontSize: "10px",
  color: "var(--text-secondary)",
  padding: "6px 10px",
  borderBottom: "1px solid var(--border)",
  whiteSpace: "nowrap",
}
