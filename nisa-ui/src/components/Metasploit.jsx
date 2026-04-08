import { useEffect, useRef, useState } from "react"
import { Terminal } from "@xterm/xterm"
import { FitAddon } from "@xterm/addon-fit"
import "@xterm/xterm/css/xterm.css"
import api from "../api"

const MSF_API = "http://localhost:8089"
const TERMINAL_WS = "ws://127.0.0.1:8091"
const NISA_API_KEY = "d551fd7e05134c52b84286c201f0f36d8ddeb5e0611ed771ba44d6a4264f39cf"
const GOLD = "var(--accent-gold)"
const DIM = "var(--text-dim)"
const BORDER = "var(--border)"
const BG2 = "var(--bg-secondary)"
const BG3 = "var(--bg-tertiary)"

export default function Metasploit() {
  const [activeTab, setActiveTab] = useState("search")
  const [health, setHealth] = useState(null)

  useEffect(() => {
    api.get(`${MSF_API}/health`).then(r => setHealth(r.data)).catch(() => setHealth(null))
  }, [])

  const tabs = [
    { id: "search", label: "MODULE SEARCH" },
    { id: "cve", label: "CVE LOOKUP" },
    { id: "info", label: "MODULE INFO" },
    { id: "terminal", label: "MSFCONSOLE" },
    { id: "categories", label: "CATEGORIES" },
  ]

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "20px",
            fontWeight: 700, letterSpacing: "0.15em", color: GOLD, margin: 0 }}>
            METASPLOIT FRAMEWORK
          </h2>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
            color: DIM, letterSpacing: "0.1em", marginTop: "2px" }}>
            Kali Linux Container — {health ? health.metasploit || "v6.4.124-dev" : "Connecting..."}
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{
            width: "8px", height: "8px", borderRadius: "50%",
            background: health ? "var(--success)" : "var(--danger)",
            boxShadow: health ? "0 0 6px var(--success)" : "none"
          }} />
          <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: DIM }}>
            {health ? "KALI ONLINE" : "KALI OFFLINE"}
          </span>
        </div>
      </div>

      <div style={{ background: BG2, border: `1px solid ${BORDER}`, borderRadius: "4px",
        padding: "10px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
        color: DIM, lineHeight: 1.6 }}>
        AUTHORIZED USE ONLY — Use only against systems you own or have explicit written permission to test.
      </div>

      <div style={{ display: "flex", gap: "4px", borderBottom: `1px solid ${BORDER}`, paddingBottom: "8px" }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            padding: "6px 14px", border: "none", cursor: "pointer",
            fontFamily: "Rajdhani, sans-serif", fontWeight: 600,
            fontSize: "11px", letterSpacing: "0.1em",
            background: activeTab === t.id ? "var(--accent-gold-glow)" : "transparent",
            color: activeTab === t.id ? GOLD : DIM,
            borderBottom: activeTab === t.id ? `2px solid ${GOLD}` : "2px solid transparent",
          }}>{t.label}</button>
        ))}
      </div>

      {activeTab === "search" && <SearchTab />}
      {activeTab === "cve" && <CVETab />}
      {activeTab === "info" && <InfoTab />}
      {activeTab === "terminal" && <TerminalTab />}
      {activeTab === "categories" && <CategoriesTab />}
    </div>
  )
}

function TerminalTab() {
  const termRef = useRef(null)
  const termInstance = useRef(null)
  const wsRef = useRef(null)
  const fitAddon = useRef(null)
  const [connected, setConnected] = useState(false)
  const [tool, setTool] = useState("msfconsole")

  const connect = () => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    const term = new Terminal({
      theme: {
        background: "#0a0e1a",
        foreground: "#c9a84c",
        cursor: "#c9a84c",
        selectionBackground: "#c9a84c33",
        black: "#0a0e1a",
        brightBlack: "#1e2d4a",
        red: "#ff4444",
        brightRed: "#ff6666",
        green: "#44ff88",
        brightGreen: "#66ffaa",
        yellow: "#c9a84c",
        brightYellow: "#ffd700",
        blue: "#4488ff",
        brightBlue: "#66aaff",
        magenta: "#ff44ff",
        brightMagenta: "#ff66ff",
        cyan: "#44ffff",
        brightCyan: "#66ffff",
        white: "#8899bb",
        brightWhite: "#aabbcc",
      },
      fontFamily: "JetBrains Mono, monospace",
      fontSize: 13,
      lineHeight: 1.4,
      cursorBlink: true,
      convertEol: true,
    })

    const fit = new FitAddon()
    fitAddon.current = fit
    term.loadAddon(fit)
    termInstance.current = term

    if (termRef.current) {
      termRef.current.innerHTML = ""
      term.open(termRef.current)
      fit.fit()
    }

    const ws = new WebSocket(TERMINAL_WS)
    wsRef.current = ws

    ws.onopen = () => {
      ws.send(JSON.stringify({ key: NISA_API_KEY, tool }))
      setConnected(true)
    }

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.type === "output" || msg.type === "error") {
          term.write(msg.data)
        }
      } catch {}
    }

    ws.onclose = () => {
      setConnected(false)
      term.write("\r\n\x1b[33mConnection closed.\x1b[0m\r\n")
    }

    ws.onerror = () => {
      setConnected(false)
      term.write("\r\n\x1b[31mWebSocket error. Is terminal server running on port 8091?\x1b[0m\r\n")
    }

    term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "input", data }))
      }
    })
  }

  const disconnect = () => {
    if (wsRef.current) wsRef.current.close()
    setConnected(false)
  }

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close()
      if (termInstance.current) termInstance.current.dispose()
    }
  }, [])

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
        <select value={tool} onChange={e => setTool(e.target.value)}
          style={{ background: BG3, border: `1px solid ${BORDER}`, borderRadius: "4px",
            padding: "6px 10px", color: "var(--text-primary)",
            fontFamily: "JetBrains Mono, monospace", fontSize: "12px", outline: "none" }}>
          <option value="msfconsole">msfconsole</option>
          <option value="bash">Kali bash</option>
        </select>
        {!connected ? (
          <button onClick={connect} style={{
            padding: "6px 20px", background: "var(--accent-gold-glow)",
            border: `1px solid ${GOLD}`, borderRadius: "4px", cursor: "pointer",
            fontFamily: "Rajdhani, sans-serif", fontWeight: 700,
            fontSize: "12px", letterSpacing: "0.15em", color: GOLD }}>
            CONNECT
          </button>
        ) : (
          <button onClick={disconnect} style={{
            padding: "6px 20px", background: "transparent",
            border: "1px solid var(--danger)", borderRadius: "4px", cursor: "pointer",
            fontFamily: "Rajdhani, sans-serif", fontWeight: 700,
            fontSize: "12px", letterSpacing: "0.15em", color: "var(--danger)" }}>
            DISCONNECT
          </button>
        )}
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <div style={{ width: "6px", height: "6px", borderRadius: "50%",
            background: connected ? "var(--success)" : "var(--text-dim)",
            boxShadow: connected ? "0 0 6px var(--success)" : "none" }} />
          <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: DIM }}>
            {connected ? "CONNECTED" : "DISCONNECTED"}
          </span>
        </div>
      </div>

      <div ref={termRef} style={{
        background: "#0a0e1a",
        border: `1px solid ${BORDER}`,
        borderRadius: "4px",
        padding: "8px",
        height: "500px",
        overflow: "hidden",
      }} />

      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
        color: DIM, lineHeight: 1.8 }}>
        <span style={{ color: GOLD }}>TIP:</span> Type <span style={{ color: GOLD }}>help</span> for commands.
        Use <span style={{ color: GOLD }}>search [term]</span> to find modules.
        Use <span style={{ color: GOLD }}>use [module]</span> to select.
        Use <span style={{ color: GOLD }}>show options</span> to configure.
        Use <span style={{ color: GOLD }}>run</span> to execute.
      </div>
    </div>
  )
}

function ModuleTable({ modules }) {
  if (!modules || modules.length === 0) return (
    <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px",
      color: DIM, padding: "20px", textAlign: "center" }}>No modules found</div>
  )
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse",
        fontFamily: "JetBrains Mono, monospace", fontSize: "11px" }}>
        <thead>
          <tr style={{ borderBottom: `1px solid ${BORDER}` }}>
            {["Module", "Date", "Rank", "Description"].map(h => (
              <th key={h} style={{ padding: "8px 12px", textAlign: "left",
                color: DIM, fontWeight: 600, letterSpacing: "0.1em",
                fontSize: "9px" }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {modules.map((m, i) => (
            <tr key={i} style={{ borderBottom: `1px solid ${BORDER}`,
              background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.02)" }}>
              <td style={{ padding: "8px 12px", color: GOLD, whiteSpace: "nowrap" }}>{m.name}</td>
              <td style={{ padding: "8px 12px", color: DIM, whiteSpace: "nowrap" }}>{m.disclosure_date}</td>
              <td style={{ padding: "8px 12px", color: getRankColor(m.rank) }}>{m.rank}</td>
              <td style={{ padding: "8px 12px", color: "var(--text-secondary)" }}>{m.description}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function getRankColor(rank) {
  if (!rank) return DIM
  const r = rank.toLowerCase()
  if (r === "excellent") return "var(--success)"
  if (r === "great" || r === "good") return GOLD
  if (r === "normal" || r === "average") return "var(--text-secondary)"
  return DIM
}

function SearchTab() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const search = async () => {
    if (!query.trim()) return
    setLoading(true); setError("")
    try {
      const res = await api.post(`${MSF_API}/search`, { query, limit: 30 })
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
          placeholder="Search modules... (e.g. apache, windows/smb, eternalblue)"
          style={{ flex: 1, background: BG3, border: `1px solid ${BORDER}`,
            borderRadius: "4px", padding: "8px 12px", color: "var(--text-primary)",
            fontFamily: "JetBrains Mono, monospace", fontSize: "12px", outline: "none" }} />
        <button onClick={search} disabled={loading} style={{
          padding: "8px 20px", background: "var(--accent-gold-glow)",
          border: `1px solid ${GOLD}`, borderRadius: "4px", cursor: "pointer",
          fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px",
          letterSpacing: "0.15em", color: GOLD }}>
          {loading ? "SEARCHING..." : "SEARCH"}
        </button>
      </div>
      {error && <div style={{ color: "var(--danger)", fontFamily: "JetBrains Mono, monospace",
        fontSize: "11px" }}>{error}</div>}
      {results && (
        <div>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
            color: DIM, marginBottom: "8px" }}>
            {results.count} modules found for "{results.query}"
          </div>
          <ModuleTable modules={results.modules} />
        </div>
      )}
    </div>
  )
}

function CVETab() {
  const [cve, setCve] = useState("")
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const search = async () => {
    if (!cve.trim()) return
    setLoading(true); setError("")
    try {
      const res = await api.post(`${MSF_API}/search/cve`, { query: cve, limit: 20 })
      setResults(res.data)
    } catch(e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ display: "flex", gap: "8px" }}>
        <input value={cve} onChange={e => setCve(e.target.value)}
          onKeyDown={e => e.key === "Enter" && search()}
          placeholder="Enter CVE number (e.g. 2021-44228, CVE-2017-0144)"
          style={{ flex: 1, background: BG3, border: `1px solid ${BORDER}`,
            borderRadius: "4px", padding: "8px 12px", color: "var(--text-primary)",
            fontFamily: "JetBrains Mono, monospace", fontSize: "12px", outline: "none" }} />
        <button onClick={search} disabled={loading} style={{
          padding: "8px 20px", background: "var(--accent-gold-glow)",
          border: `1px solid ${GOLD}`, borderRadius: "4px", cursor: "pointer",
          fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px",
          letterSpacing: "0.15em", color: GOLD }}>
          {loading ? "LOOKING UP..." : "LOOKUP"}
        </button>
      </div>
      {error && <div style={{ color: "var(--danger)", fontFamily: "JetBrains Mono, monospace",
        fontSize: "11px" }}>{error}</div>}
      {results && (
        <div>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
            color: DIM, marginBottom: "8px" }}>
            {results.count} exploit modules for {results.cve}
          </div>
          <ModuleTable modules={results.modules} />
        </div>
      )}
    </div>
  )
}

function InfoTab() {
  const [module, setModule] = useState("")
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const getInfo = async () => {
    if (!module.trim()) return
    setLoading(true); setError("")
    try {
      const res = await api.post(`${MSF_API}/info`, { module_path: module })
      setResult(res.data)
    } catch(e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ display: "flex", gap: "8px" }}>
        <input value={module} onChange={e => setModule(e.target.value)}
          onKeyDown={e => e.key === "Enter" && getInfo()}
          placeholder="Module path (e.g. exploit/windows/smb/ms17_010_eternalblue)"
          style={{ flex: 1, background: BG3, border: `1px solid ${BORDER}`,
            borderRadius: "4px", padding: "8px 12px", color: "var(--text-primary)",
            fontFamily: "JetBrains Mono, monospace", fontSize: "12px", outline: "none" }} />
        <button onClick={getInfo} disabled={loading} style={{
          padding: "8px 20px", background: "var(--accent-gold-glow)",
          border: `1px solid ${GOLD}`, borderRadius: "4px", cursor: "pointer",
          fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px",
          letterSpacing: "0.15em", color: GOLD }}>
          {loading ? "LOADING..." : "GET INFO"}
        </button>
      </div>
      {error && <div style={{ color: "var(--danger)", fontFamily: "JetBrains Mono, monospace",
        fontSize: "11px" }}>{error}</div>}
      {result && (
        <pre style={{ background: BG2, border: `1px solid ${BORDER}`, borderRadius: "4px",
          padding: "16px", margin: 0, fontFamily: "JetBrains Mono, monospace",
          fontSize: "11px", color: "var(--text-secondary)", overflowX: "auto",
          whiteSpace: "pre-wrap", lineHeight: 1.6 }}>{result.info}</pre>
      )}
    </div>
  )
}

function CategoriesTab() {
  const [categories, setCategories] = useState([])

  useEffect(() => {
    api.get(`${MSF_API}/modules/categories`)
      .then(r => setCategories(r.data.categories))
      .catch(() => {})
  }, [])

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
      {categories.map(cat => (
        <div key={cat.id} style={{ background: BG2, border: `1px solid ${BORDER}`,
          borderRadius: "4px", padding: "16px" }}>
          <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700,
            fontSize: "14px", letterSpacing: "0.1em", color: GOLD,
            marginBottom: "6px" }}>{cat.id.toUpperCase()}</div>
          <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "12px",
            color: "var(--text-secondary)", lineHeight: 1.5 }}>{cat.description}</div>
        </div>
      ))}
    </div>
  )
}
