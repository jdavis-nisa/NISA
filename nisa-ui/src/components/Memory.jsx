import { useState, useEffect } from "react"
import { Brain, Search, RefreshCw, Filter, X } from "lucide-react"
import api from "../api"

const NLU_API = "http://localhost:8081"

const ROUTE_COLORS = {
  security:    { bg: "rgba(201,168,76,0.12)",  border: "rgba(201,168,76,0.4)",  text: "#C9A84C", label: "SECURITY"  },
  coding:      { bg: "rgba(68,170,255,0.10)",  border: "rgba(68,170,255,0.35)", text: "#44AAFF", label: "CODING"    },
  primary:     { bg: "rgba(110,200,110,0.10)", border: "rgba(110,200,110,0.35)",text: "#6EC86E", label: "PRIMARY"   },
  reasoning:   { bg: "rgba(180,120,255,0.10)", border: "rgba(180,120,255,0.35)",text: "#B478FF", label: "REASONING" },
  moa_full_moa:{ bg: "rgba(255,120,80,0.10)",  border: "rgba(255,120,80,0.35)", text: "#FF7850", label: "MOA"       },
}
const ROUTE_DEFAULT = { bg: "rgba(120,120,120,0.1)", border: "rgba(120,120,120,0.3)", text: "#888", label: "OTHER" }

function routeStyle(reason) {
  if (!reason) return ROUTE_DEFAULT
  const key = Object.keys(ROUTE_COLORS).find(k => reason.toLowerCase().includes(k))
  return key ? ROUTE_COLORS[key] : ROUTE_DEFAULT
}

export default function Memory() {
  const [memories, setMemories]   = useState([])
  const [filtered, setFiltered]   = useState([])
  const [search, setSearch]       = useState("")
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)
  const [routeFilter, setRouteFilter] = useState("all")
  const [modelFilter, setModelFilter] = useState("all")

  const fetchMemories = async () => {
    setLoading(true); setError(null)
    try {
      const res = await api.get(`${NLU_API}/memory`)
      const entries = res.data.entries || []
      setMemories(entries)
      setFiltered(entries)
    } catch (e) {
      setError("Memory endpoint not available")
    }
    setLoading(false)
  }

  const handleSearch = async () => {
    if (!search.trim()) { applyFilters(memories); return }
    setLoading(true)
    try {
      const res = await api.post(`${NLU_API}/memory/search`, { query: search })
      applyFilters(res.data.results || [], true)
    } catch {
      applyFilters(memories.filter(m => m.document?.toLowerCase().includes(search.toLowerCase())), true)
    }
    setLoading(false)
  }

  const applyFilters = (base, fromSearch = false) => {
    let result = base
    if (routeFilter !== "all") result = result.filter(m => (m.metadata?.routing_reason || "").toLowerCase().includes(routeFilter))
    if (modelFilter !== "all") result = result.filter(m => (m.metadata?.model_used || "").includes(modelFilter))
    setFiltered(result)
  }

  const clearFilters = () => {
    setSearch(""); setRouteFilter("all"); setModelFilter("all"); setFiltered(memories)
  }

  useEffect(() => { fetchMemories() }, [])
  useEffect(() => { applyFilters(memories) }, [routeFilter, modelFilter])
  useEffect(() => { if (!search.trim()) applyFilters(memories) }, [search, memories])

  // Unique models for dropdown
  const models = ["all", ...Array.from(new Set(memories.map(m => m.metadata?.model_used).filter(Boolean)))]
  const routes = ["all", "security", "coding", "primary", "reasoning", "moa_full_moa"]

  // Stats
  const routeCounts = {}
  memories.forEach(m => {
    const r = m.metadata?.routing_reason || "other"
    routeCounts[r] = (routeCounts[r] || 0) + 1
  })

  return (
    <div className="fade-in" style={{ maxWidth: "960px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
          <Brain size={18} color="var(--accent-gold)" />
          <h1 style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "20px", letterSpacing: "0.15em", color: "var(--text-primary)" }}>
            MEMORY EXPLORER
          </h1>
        </div>
        <p style={{ fontFamily: "Outfit, sans-serif", fontSize: "13px", color: "var(--text-dim)", marginLeft: "28px" }}>
          Nisaba remembers — semantic memory stored in ChromaDB
        </p>
      </div>

      {/* Stats row */}
      <div style={{ display: "flex", gap: "12px", marginBottom: "20px", flexWrap: "wrap" }}>
        <StatCard label="TOTAL MEMORIES" value={memories.length} />
        <StatCard label="COLLECTION" value="nisa_memory" mono />
        {Object.entries(routeCounts).slice(0,3).map(([r, n]) => (
          <StatCard key={r} label={routeStyle(r).label} value={n}
            accent={routeStyle(r).text} />
        ))}
      </div>

      {/* Search + Filters */}
      <div style={{ border: "1px solid var(--border)", borderRadius: "4px", background: "var(--bg-panel)", padding: "14px", marginBottom: "12px" }}>
        {/* Search row */}
        <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "10px" }}>
          <Search size={14} color="var(--text-dim)" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSearch()}
            placeholder="Semantic search across memories..."
            style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: "var(--text-primary)", fontFamily: "Outfit, sans-serif", fontSize: "13px" }}
          />
          <button onClick={handleSearch} style={{ padding: "6px 12px", background: "var(--accent-gold-glow)", border: "1px solid var(--accent-gold-dim)", borderRadius: "2px", color: "var(--accent-gold)", fontFamily: "Rajdhani, sans-serif", fontWeight: 600, fontSize: "11px", letterSpacing: "0.15em", cursor: "pointer" }}>
            SEARCH
          </button>
          <button onClick={fetchMemories} style={{ background: "transparent", border: "none", color: "var(--text-dim)", cursor: "pointer", display: "flex", alignItems: "center" }}>
            <RefreshCw size={13} />
          </button>
        </div>
        {/* Filter row */}
        <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
          <Filter size={12} color="var(--text-dim)" />
          <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", letterSpacing: "0.1em" }}>FILTER:</span>
          <select value={routeFilter} onChange={e => setRouteFilter(e.target.value)}
            style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "2px", color: "var(--text-secondary)", fontFamily: "JetBrains Mono, monospace", fontSize: "10px", padding: "3px 6px", cursor: "pointer" }}>
            {routes.map(r => <option key={r} value={r}>{r === "all" ? "ALL ROUTES" : routeStyle(r).label}</option>)}
          </select>
          <select value={modelFilter} onChange={e => setModelFilter(e.target.value)}
            style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "2px", color: "var(--text-secondary)", fontFamily: "JetBrains Mono, monospace", fontSize: "10px", padding: "3px 6px", cursor: "pointer", maxWidth: "200px" }}>
            {models.map(m => <option key={m} value={m}>{m === "all" ? "ALL MODELS" : m.split("/").pop().slice(0,25)}</option>)}
          </select>
          {(routeFilter !== "all" || modelFilter !== "all" || search) && (
            <button onClick={clearFilters} style={{ display: "flex", alignItems: "center", gap: "4px", background: "transparent", border: "1px solid var(--border)", borderRadius: "2px", color: "var(--text-dim)", fontFamily: "JetBrains Mono, monospace", fontSize: "9px", padding: "3px 8px", cursor: "pointer", letterSpacing: "0.1em" }}>
              <X size={10} /> CLEAR
            </button>
          )}
          <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", marginLeft: "auto" }}>
            {filtered.length} / {memories.length}
          </span>
        </div>
      </div>

      {error && (
        <div style={{ padding: "12px 14px", border: "1px solid var(--warning)", borderRadius: "4px", background: "var(--bg-panel)", fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--warning)", marginBottom: "16px" }}>{error}</div>
      )}

      {/* Memory list */}
      {loading ? (
        <LoadingPanel label="Loading memories from ChromaDB..." />
      ) : (
        <div style={{ border: "1px solid var(--border)", borderRadius: "4px", background: "var(--bg-panel)", overflow: "hidden" }}>
          <div style={{ padding: "8px 14px", borderBottom: "1px solid var(--border)", background: "var(--bg-secondary)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 600, fontSize: "11px", letterSpacing: "0.15em", color: "var(--text-dim)" }}>MEMORY ENTRIES</span>
            <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)" }}>{filtered.length} entries</span>
          </div>
          {filtered.length === 0 ? (
            <div style={{ padding: "32px", textAlign: "center", fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: "var(--text-dim)" }}>
              {search || routeFilter !== "all" || modelFilter !== "all" ? "No memories match filters" : "No memories yet — chat with Nisaba to build memory"}
            </div>
          ) : (
            <div style={{ maxHeight: "600px", overflowY: "auto" }}>
              {filtered.map((entry, i) => <MemoryEntry key={entry.id || i} entry={entry} index={i} />)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function MemoryEntry({ entry, index }) {
  const [expanded, setExpanded] = useState(false)
  const meta = entry.metadata || {}
  const doc  = entry.document || entry.content || ""
  const rs   = routeStyle(meta.routing_reason)

  // Split document into user/nisaba parts
  const userMatch  = doc.match(/^User:\s*([\s\S]*?)\nNisaba:/m)
  const nisMatch   = doc.match(/\nNisaba:\s*([\s\S]*)$/m)
  const userMsg    = userMatch  ? userMatch[1].trim()  : (meta.user_message  || doc.slice(0, 200))
  const nisabaMsg  = nisMatch   ? nisMatch[1].trim()   : (meta.nisaba_response || "")
  const modelShort = (meta.model_used || "").split("/").pop()
  const ts         = meta.timestamp ? meta.timestamp.slice(0, 16).replace("T", " ") : ""

  return (
    <div
      onClick={() => setExpanded(!expanded)}
      style={{ padding: "12px 14px", borderBottom: "1px solid var(--border)", cursor: "pointer", background: expanded ? "var(--bg-elevated)" : "transparent", transition: "background 0.15s" }}
      onMouseEnter={e => { if (!expanded) e.currentTarget.style.background = "var(--bg-secondary)" }}
      onMouseLeave={e => { if (!expanded) e.currentTarget.style.background = "transparent" }}
    >
      {/* Top row: badge + model + timestamp */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px", flexWrap: "wrap" }}>
        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", fontWeight: 700, letterSpacing: "0.1em", color: rs.text, background: rs.bg, border: `1px solid ${rs.border}`, borderRadius: "2px", padding: "1px 6px" }}>
          {rs.label}
        </span>
        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)" }}>
          {modelShort}
        </span>
        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", marginLeft: "auto" }}>
          {ts}
        </span>
      </div>

      {/* User message preview */}
      <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "12px", lineHeight: "1.5", color: "var(--text-secondary)" }}>
        <span style={{ color: "var(--accent-gold-dim)", fontFamily: "JetBrains Mono, monospace", fontSize: "9px", letterSpacing: "0.1em", marginRight: "6px" }}>YOU</span>
        {expanded ? userMsg : userMsg.slice(0, 120) + (userMsg.length > 120 ? "..." : "")}
      </div>

      {/* Expanded: Nisaba response */}
      {expanded && nisabaMsg && (
        <div style={{ marginTop: "10px", paddingTop: "10px", borderTop: "1px solid var(--border)" }}>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--accent-gold)", letterSpacing: "0.1em", marginBottom: "4px" }}>NISABA</div>
          <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "12px", lineHeight: "1.6", color: "var(--text-secondary)", whiteSpace: "pre-wrap", maxHeight: "300px", overflowY: "auto" }}>
            {nisabaMsg.slice(0, 800)}{nisabaMsg.length > 800 ? "..." : ""}
          </div>
        </div>
      )}

      {/* Metadata when expanded */}
      {expanded && (
        <div style={{ marginTop: "8px", padding: "6px 8px", background: "var(--bg-secondary)", borderRadius: "2px", fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", display: "flex", gap: "16px", flexWrap: "wrap" }}>
          <span>ID: {entry.id?.slice(0, 16)}...</span>
          {meta.session_id && <span>SESSION: {meta.session_id}</span>}
          {meta.routing_reason && <span>ROUTE: {meta.routing_reason}</span>}
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, mono, accent }) {
  return (
    <div style={{ padding: "12px 16px", border: "1px solid var(--border)", borderRadius: "4px", background: "var(--bg-panel)", minWidth: "110px" }}>
      <div style={{ fontFamily: mono ? "JetBrains Mono, monospace" : "Rajdhani, sans-serif", fontWeight: mono ? 400 : 700, fontSize: mono ? "11px" : "22px", color: accent || "var(--text-primary)", marginBottom: "2px" }}>{value}</div>
      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", letterSpacing: "0.1em" }}>{label}</div>
    </div>
  )
}

function LoadingPanel({ label }) {
  return (
    <div style={{ padding: "20px", border: "1px solid var(--border)", borderLeft: "2px solid var(--accent-gold-dim)", borderRadius: "4px", background: "var(--bg-panel)", display: "flex", alignItems: "center", gap: "12px" }}>
      <div style={{ width: "16px", height: "16px", border: "2px solid var(--accent-gold-dim)", borderTop: "2px solid var(--accent-gold)", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
      <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: "var(--text-secondary)", letterSpacing: "0.1em" }}>{label}</span>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
