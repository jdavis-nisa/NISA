import { useState, useEffect } from "react"
import { Brain, Search, RefreshCw, Database } from "lucide-react"
import api from "../api"

const NLU_API = "http://localhost:8081"

export default function Memory() {
  const [memories, setMemories] = useState([])
  const [filtered, setFiltered] = useState([])
  const [search, setSearch] = useState("")
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)

  const fetchMemories = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.get(`${NLU_API}/memory`)
      setMemories(res.data.entries || [])
      setFiltered(res.data.entries || [])
      setStats(res.data.stats || null)
    } catch (e) {
      setError("Memory endpoint not available — add /memory to NLU API")
    }
    setLoading(false)
  }

  const handleSearch = async () => {
    if (!search.trim()) {
      setFiltered(memories)
      return
    }
    setLoading(true)
    try {
      const res = await api.post(`${NLU_API}/memory/search`, { query: search })
      setFiltered(res.data.results || [])
    } catch (e) {
      // Fall back to client-side filter
      setFiltered(memories.filter(m =>
        m.document?.toLowerCase().includes(search.toLowerCase())
      ))
    }
    setLoading(false)
  }

  useEffect(() => { fetchMemories() }, [])

  useEffect(() => {
    if (!search.trim()) setFiltered(memories)
  }, [search, memories])

  return (
    <div className="fade-in" style={{ maxWidth: "900px", margin: "0 auto" }}>
      <PageHeader
        icon={Brain}
        title="MEMORY EXPLORER"
        subtitle="Nisaba remembers — semantic memory stored in ChromaDB"
      />

      {/* Stats */}
      <div style={{
        display: "flex",
        gap: "12px",
        marginBottom: "24px",
        flexWrap: "wrap",
      }}>
        <StatCard label="TOTAL MEMORIES" value={memories.length} />
        <StatCard label="COLLECTION" value="nisa_memory" mono />
        <StatCard label="EMBEDDINGS" value="MiniLM-L6-v2" mono />
        <StatCard label="STORAGE" value="ChromaDB" mono />
      </div>

      {/* Search */}
      <div style={{
        border: "1px solid var(--border)",
        borderRadius: "4px",
        background: "var(--bg-panel)",
        padding: "14px",
        marginBottom: "16px",
        display: "flex",
        gap: "10px",
        alignItems: "center",
      }}>
        <Search size={14} color="var(--text-dim)" />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleSearch()}
          placeholder="Semantic search across memories..."
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            outline: "none",
            color: "var(--text-primary)",
            fontFamily: "Outfit, sans-serif",
            fontSize: "13px",
          }}
        />
        <button onClick={handleSearch} style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          padding: "6px 12px",
          background: "var(--accent-gold-glow)",
          border: "1px solid var(--accent-gold-dim)",
          borderRadius: "2px",
          color: "var(--accent-gold)",
          fontFamily: "Rajdhani, sans-serif",
          fontWeight: 600,
          fontSize: "11px",
          letterSpacing: "0.15em",
          cursor: "pointer",
        }}>
          SEARCH
        </button>
        <button onClick={fetchMemories} style={{
          background: "transparent",
          border: "none",
          color: "var(--text-dim)",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
        }}>
          <RefreshCw size={13} />
        </button>
      </div>

      {/* Results count */}
      {search && (
        <div style={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "10px",
          color: "var(--text-dim)",
          marginBottom: "10px",
          letterSpacing: "0.1em",
        }}>
          SHOWING {filtered.length} OF {memories.length} MEMORIES
        </div>
      )}

      {/* Error */}
      {error && (
        <div style={{
          padding: "12px 14px",
          border: "1px solid var(--warning)",
          borderLeft: "2px solid var(--warning)",
          borderRadius: "4px",
          background: "var(--bg-panel)",
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "10px",
          color: "var(--warning)",
          marginBottom: "16px",
        }}>{error}</div>
      )}

      {/* Memory entries */}
      {loading ? (
        <LoadingPanel label="Loading memories from ChromaDB..." />
      ) : (
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
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}>
            <span style={{
              fontFamily: "Rajdhani, sans-serif",
              fontWeight: 600,
              fontSize: "11px",
              letterSpacing: "0.15em",
              color: "var(--text-dim)",
            }}>MEMORY ENTRIES</span>
            <span style={{
              fontFamily: "JetBrains Mono, monospace",
              fontSize: "9px",
              color: "var(--text-dim)",
            }}>{filtered.length} entries</span>
          </div>

          {filtered.length === 0 ? (
            <div style={{
              padding: "32px",
              textAlign: "center",
              fontFamily: "JetBrains Mono, monospace",
              fontSize: "11px",
              color: "var(--text-dim)",
            }}>
              {search ? "No memories match your search" : "No memories yet — chat with Nisaba to build memory"}
            </div>
          ) : (
            <div style={{ maxHeight: "600px", overflowY: "auto" }}>
              {filtered.map((entry, i) => (
                <MemoryEntry key={i} entry={entry} index={i} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function MemoryEntry({ entry, index }) {
  const [expanded, setExpanded] = useState(false)
  const doc = entry.document || entry.content || ""
  const preview = doc.slice(0, 150)
  const hasMore = doc.length > 150

  return (
    <div
      onClick={() => setExpanded(!expanded)}
      style={{
        padding: "12px 14px",
        borderBottom: "1px solid var(--border)",
        cursor: "pointer",
        transition: "background 0.15s",
        background: expanded ? "var(--bg-elevated)" : "transparent",
      }}
      onMouseEnter={e => e.currentTarget.style.background = "var(--bg-secondary)"}
      onMouseLeave={e => e.currentTarget.style.background = expanded ? "var(--bg-elevated)" : "transparent"}
    >
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
        <span style={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "9px",
          color: "var(--accent-gold-dim)",
          letterSpacing: "0.1em",
        }}>MEMORY #{index + 1}</span>
        {entry.id && (
          <span style={{
            fontFamily: "JetBrains Mono, monospace",
            fontSize: "9px",
            color: "var(--text-dim)",
          }}>{entry.id?.slice(0, 16)}...</span>
        )}
      </div>
      <div style={{
        fontFamily: "Outfit, sans-serif",
        fontSize: "12px",
        lineHeight: "1.6",
        color: "var(--text-secondary)",
        whiteSpace: "pre-wrap",
      }}>
        {expanded ? doc : preview}
        {!expanded && hasMore && (
          <span style={{ color: "var(--text-dim)" }}>...</span>
        )}
      </div>
      {entry.metadata && expanded && (
        <div style={{
          marginTop: "8px",
          padding: "6px 8px",
          background: "var(--bg-secondary)",
          borderRadius: "2px",
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "9px",
          color: "var(--text-dim)",
        }}>
          {JSON.stringify(entry.metadata)}
        </div>
      )}
    </div>
  )
}

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

function StatCard({ label, value, mono }) {
  return (
    <div style={{
      padding: "12px 16px",
      border: "1px solid var(--border)",
      borderRadius: "4px",
      background: "var(--bg-panel)",
      minWidth: "120px",
    }}>
      <div style={{
        fontFamily: mono ? "JetBrains Mono, monospace" : "Rajdhani, sans-serif",
        fontWeight: mono ? 400 : 700,
        fontSize: mono ? "12px" : "22px",
        color: "var(--text-primary)",
        marginBottom: "2px",
      }}>{value}</div>
      <div style={{
        fontFamily: "JetBrains Mono, monospace",
        fontSize: "9px",
        color: "var(--text-dim)",
        letterSpacing: "0.1em",
      }}>{label}</div>
    </div>
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
