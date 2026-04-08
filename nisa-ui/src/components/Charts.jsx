import { useState, useEffect } from "react"
import { BarChart2, RefreshCw, Zap } from "lucide-react"
import axios from "axios"
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, RadialLinearScale, Title, Tooltip, Legend, Filler } from "chart.js"
import { Bar, Line, Pie, Radar } from "react-chartjs-2"

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, RadialLinearScale, Title, Tooltip, Legend, Filler)

const VIZ_API = "http://localhost:8087"
const GOLD = "#C9A84C"
const CYAN = "#00AAFF"
const GREEN = "#00FF88"
const RED = "#FF4444"
const ORANGE = "#FF6B35"

const panelStyle = { background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "4px", padding: "16px", marginBottom: "16px" }

const chartOptions = () => ({
  responsive: true, maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: "#8B9BAA" } },
    tooltip: { backgroundColor: "#1E2D3D", titleColor: GOLD, bodyColor: "#8B9BAA" }
  },
  scales: { x: { ticks: { color: "#8B9BAA" }, grid: { color: "#1E2D3D" } }, y: { ticks: { color: "#8B9BAA" }, grid: { color: "#1E2D3D" } } }
})

const radarOptions = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { labels: { color: "#8B9BAA" } }, tooltip: { backgroundColor: "#1E2D3D", titleColor: GOLD, bodyColor: "#8B9BAA" } },
  scales: { r: { ticks: { color: "#8B9BAA", backdropColor: "transparent" }, grid: { color: "#1E2D3D" }, pointLabels: { color: GOLD, font: { size: 11 } } } }
}

function ChartPanel({ title, children, loading, onRefresh }) {
  return (
    <div style={panelStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
        <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "11px", letterSpacing: "0.15em", color: GOLD }}>{title}</span>
        {onRefresh && <button onClick={onRefresh} style={{ background: "none", border: "none", color: "var(--text-dim)", cursor: "pointer" }}><RefreshCw size={11} /></button>}
      </div>
      <div style={{ height: "250px" }}>
        {loading ? <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: "var(--text-dim)" }}>Loading...</div> : children}
      </div>
    </div>
  )
}

export default function Charts() {
  const [prompt, setPrompt] = useState("")
  const [loading, setLoading] = useState(false)
  const [naturalChart, setNaturalChart] = useState(null)
  const [explanation, setExplanation] = useState("")
  const [auditData, setAuditData] = useState(null)
  const [routingData, setRoutingData] = useState(null)
  const [memoryData, setMemoryData] = useState(null)
  const [analyticsLoading, setAnalyticsLoading] = useState(true)

  const loadAnalytics = async () => {
    setAnalyticsLoading(true)
    try {
      const [audit, routing, memory] = await Promise.all([
        axios.get(`${VIZ_API}/prebuilt/audit_events`).catch(() => null),
        axios.get(`${VIZ_API}/prebuilt/model_routing`).catch(() => null),
        axios.get(`${VIZ_API}/prebuilt/memory_growth`).catch(() => null),
      ])
      if (audit?.data?.chart?.data?.[0]) {
        const t = audit.data.chart.data[0]
        setAuditData({ labels: t.x || [], datasets: [{ label: "Events", data: t.y || [], backgroundColor: GOLD + "99", borderColor: GOLD, borderWidth: 1 }] })
      }
      if (routing?.data?.chart?.data?.[0]) {
        const t = routing.data.chart.data[0]
        setRoutingData({ labels: t.labels || [], datasets: [{ data: t.values || [], backgroundColor: [GOLD, CYAN, GREEN, RED, ORANGE, "#AA88FF"], borderWidth: 0 }] })
      }
      if (memory?.data?.chart?.data?.[0]) {
        const t = memory.data.chart.data[0]
        setMemoryData({ labels: t.x || [], datasets: [{ label: "Memories", data: t.y || [], borderColor: GREEN, backgroundColor: GREEN + "22", fill: true, tension: 0.3 }] })
      }
    } catch (e) {}
    setAnalyticsLoading(false)
  }

  useEffect(() => { loadAnalytics() }, [])

  const generateNatural = async () => {
    if (!prompt.trim()) return
    setLoading(true)
    setNaturalChart(null)
    try {
      const res = await axios.post(`${VIZ_API}/natural`, { prompt })
      const trace = res.data?.chart?.data?.[0]
      if (trace) {
        const type = trace.type
        if (type === "bar") setNaturalChart({ type: "bar", data: { labels: trace.x, datasets: [{ label: "Data", data: trace.y, backgroundColor: GOLD + "99", borderColor: GOLD, borderWidth: 1 }] } })
        else if (type === "scatter") setNaturalChart({ type: "line", data: { labels: trace.x, datasets: [{ label: "Data", data: trace.y, borderColor: CYAN, backgroundColor: CYAN + "22", fill: true, tension: 0.3 }] } })
        else if (type === "pie") setNaturalChart({ type: "pie", data: { labels: trace.labels, datasets: [{ data: trace.values, backgroundColor: [GOLD, CYAN, GREEN, RED, ORANGE], borderWidth: 0 }] } })
        else if (type === "scatterpolar") setNaturalChart({ type: "radar", data: { labels: trace.theta, datasets: [{ label: "Score", data: trace.r, borderColor: GOLD, backgroundColor: GOLD + "33", pointBackgroundColor: GOLD }] } })
        setExplanation(res.data.explanation || "")
      }
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const renderNaturalChart = () => {
    if (!naturalChart) return null
    const opts = naturalChart.type === "radar" ? radarOptions : chartOptions()
    switch (naturalChart.type) {
      case "bar": return <Bar data={naturalChart.data} options={opts} />
      case "line": return <Line data={naturalChart.data} options={opts} />
      case "pie": return <Pie data={naturalChart.data} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: "#8B9BAA" } } } }} />
      case "radar": return <Radar data={naturalChart.data} options={opts} />
      default: return null
    }
  }

  const securityData = {
    labels: ["PyRIT", "OWASP", "Auth", "Encryption", "Monitoring", "Forensics"],
    datasets: [{ label: "Score %", data: [100, 88, 95, 90, 85, 92], borderColor: GOLD, backgroundColor: GOLD + "33", pointBackgroundColor: GOLD }]
  }

  return (
    <div className="fade-in" style={{ maxWidth: "900px", margin: "0 auto" }}>
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
          <BarChart2 size={20} color={GOLD} />
          <h1 style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "24px", letterSpacing: "0.2em", color: "var(--text-primary)", margin: 0 }}>VISUALIZATIONS</h1>
        </div>
        <p style={{ fontFamily: "Outfit, sans-serif", fontSize: "13px", color: "var(--text-dim)", margin: 0 }}>AI-generated charts, NISA analytics, and data visualization</p>
      </div>

      <div style={panelStyle}>
        <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px", letterSpacing: "0.15em", color: GOLD, marginBottom: "12px", display: "flex", alignItems: "center", gap: "6px" }}>
          <Zap size={12} /> AI CHART GENERATOR
        </div>
        <textarea value={prompt} onChange={e => setPrompt(e.target.value)}
          placeholder="Describe a chart... e.g. radar chart of NISA security scores, bar chart of OWASP vulnerabilities..."
          style={{ width: "100%", background: "var(--bg-primary)", border: "1px solid var(--border)", borderRadius: "2px", padding: "8px 10px", color: "var(--text-primary)", fontFamily: "JetBrains Mono, monospace", fontSize: "12px", outline: "none", boxSizing: "border-box", height: "80px", resize: "vertical", marginBottom: "10px" }}
        />
        <button onClick={generateNatural} disabled={loading || !prompt.trim()}
          style={{ padding: "10px 20px", background: "transparent", border: `1px solid ${GOLD}`, borderRadius: "2px", color: GOLD, fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "11px", letterSpacing: "0.15em", cursor: "pointer", display: "flex", alignItems: "center", gap: "6px" }}>
          <Zap size={12} /> {loading ? "GENERATING..." : "GENERATE CHART"}
        </button>
      </div>

      {(loading || naturalChart) && (
        <ChartPanel title={explanation || "AI Generated Chart"} loading={loading}>{renderNaturalChart()}</ChartPanel>
      )}

      <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "11px", letterSpacing: "0.2em", color: "var(--text-dim)", marginBottom: "16px" }}>NISA ANALYTICS</div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
        <ChartPanel title="SECURITY ASSESSMENT SCORES" onRefresh={loadAnalytics}>
          <Radar data={securityData} options={radarOptions} />
        </ChartPanel>
        <ChartPanel title="MODEL ROUTING DISTRIBUTION" loading={analyticsLoading} onRefresh={loadAnalytics}>
          {routingData && <Pie data={routingData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: "#8B9BAA", font: { size: 10 } } } } }} />}
        </ChartPanel>
        <ChartPanel title="AUDIT EVENTS BY TYPE" loading={analyticsLoading} onRefresh={loadAnalytics}>
          {auditData && <Bar data={auditData} options={chartOptions()} />}
        </ChartPanel>
        <ChartPanel title="MEMORY GROWTH OVER TIME" loading={analyticsLoading} onRefresh={loadAnalytics}>
          {memoryData && <Line data={memoryData} options={chartOptions()} />}
        </ChartPanel>
      </div>
    </div>
  )
}
