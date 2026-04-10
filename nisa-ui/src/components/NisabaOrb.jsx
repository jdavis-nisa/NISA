import { useState, useRef, useEffect } from "react"
import { Brain, X, Send, Minimize2, AlertTriangle } from "lucide-react"
import api from "../api"
import ReactMarkdown from "react-markdown"
import { onAlert, acknowledgeAlerts } from "../SessionContext"

const NLU_API = "http://localhost:8081"

export default function NisabaOrb() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [spinning, setSpinning] = useState(false)
  const [alerts, setAlerts] = useState([])
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    if (open && inputRef.current) inputRef.current.focus()
  }, [open])

  useEffect(() => {
    const unsub = onAlert((incoming) => {
      setAlerts(incoming)
      if (incoming.length > 0 && !open) setOpen(true)
    })
    return unsub
  }, [])

  const hasAlerts = alerts.length > 0

  const handleOpen = () => {
    setOpen(o => !o)
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const send = async () => {
    const msg = input.trim()
    if (!msg || loading) return
    setInput("")
    setMessages(prev => [...prev, { role: "user", content: msg }])
    setLoading(true)
    setSpinning(true)
    try {
      const res = await api.post(`${NLU_API}/chat`, {
        message: msg,
        temperature: 0.3,
        max_tokens: 400
      })
      setMessages(prev => [...prev, { role: "assistant", content: res.data.response }])
    } catch(e) {
      setMessages(prev => [...prev, { role: "assistant", content: "Connection error. Check NLU API." }])
    }
    setLoading(false)
    setSpinning(false)
  }

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <div style={{ position: "fixed", bottom: "24px", right: "24px", zIndex: 9999 }}>
      {/* Chat window */}
      {open && (
        <div style={{
          position: "absolute", bottom: "60px", right: 0,
          width: "320px", height: "420px",
          background: "var(--bg-secondary)",
          border: "1px solid var(--accent-gold)",
          borderRadius: "8px",
          display: "flex", flexDirection: "column",
          boxShadow: "0 8px 32px rgba(0,0,0,0.4), 0 0 16px rgba(212,175,55,0.1)",
          overflow: "hidden"
        }}>
          {/* Header */}
          <div style={{
            padding: "10px 14px",
            borderBottom: "1px solid var(--border)",
            display: "flex", alignItems: "center", justifyContent: "space-between",
            background: "var(--bg-primary)"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Brain size={14} color="var(--accent-gold)" />
              <span style={{
                fontFamily: "Rajdhani, sans-serif", fontWeight: 700,
                fontSize: "12px", letterSpacing: "0.15em", color: "var(--accent-gold)"
              }}>NISABA</span>
            </div>
            <div style={{ display: "flex", gap: "6px" }}>
              <button onClick={() => { setMessages([]); }} style={miniBtn}>
                <Minimize2 size={11} color="var(--text-dim)" />
              </button>
              <button onClick={() => setOpen(false)} style={miniBtn}>
                <X size={11} color="var(--text-dim)" />
              </button>
            </div>
          </div>

          {/* Alert Banner */}
          {alerts.length > 0 && (
            <div style={{
              background: "rgba(239,68,68,0.12)", borderBottom: "1px solid var(--danger)",
              padding: "8px 12px"
            }}>
              {alerts.map(a => (
                <div key={a.id} style={{ marginBottom: alerts.length > 1 ? "6px" : 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "2px" }}>
                    <AlertTriangle size={11} color="var(--danger)" />
                    <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "11px", color: "var(--danger)", letterSpacing: "0.1em" }}>{a.title}</span>
                  </div>
                  <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "10px", color: "var(--text-secondary)", lineHeight: 1.4 }}>{a.summary}</div>
                  {a.recommendation && (
                    <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--accent-cyan, #00d4ff)", marginTop: "3px" }}>{a.recommendation}</div>
                  )}
                </div>
              ))}
              <button onClick={() => { acknowledgeAlerts(); setAlerts([]) }} style={{
                marginTop: "6px", background: "transparent", border: "1px solid var(--danger)",
                color: "var(--danger)", borderRadius: "3px", padding: "2px 8px", cursor: "pointer",
                fontFamily: "JetBrains Mono, monospace", fontSize: "9px"
              }}>ACKNOWLEDGE</button>
            </div>
          )}

          {/* Messages */}
          <div style={{ flex: 1, overflowY: "auto", padding: "12px", display: "flex", flexDirection: "column", gap: "8px" }}>
            {messages.length === 0 && (
              <div style={{
                color: "var(--text-dim)", fontFamily: "JetBrains Mono, monospace",
                fontSize: "10px", textAlign: "center", marginTop: "20px", lineHeight: 1.6
              }}>
                Ask me anything about<br />what you're working on.
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} style={{
                alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                maxWidth: "85%"
              }}>
                <div style={{
                  padding: "8px 10px",
                  borderRadius: m.role === "user" ? "8px 8px 2px 8px" : "8px 8px 8px 2px",
                  background: m.role === "user" ? "var(--accent-gold-glow)" : "var(--bg-primary)",
                  border: m.role === "user" ? "1px solid var(--accent-gold)" : "1px solid var(--border)",
                  fontFamily: m.role === "user" ? "Outfit, sans-serif" : "inherit",
                  fontSize: "11px",
                  color: "var(--text-primary)",
                  lineHeight: 1.5
                }}>
                  {m.role === "assistant"
                    ? <ReactMarkdown components={{
                        p: ({children}) => <p style={{ margin: 0, fontSize: "11px", fontFamily: "Outfit, sans-serif" }}>{children}</p>,
                        code: ({children}) => <code style={{ fontSize: "10px", background: "var(--bg-secondary)", padding: "1px 4px", borderRadius: "2px" }}>{children}</code>
                      }}>{m.content}</ReactMarkdown>
                    : m.content
                  }
                </div>
              </div>
            ))}
            {loading && (
              <div style={{ alignSelf: "flex-start" }}>
                <div style={{
                  padding: "8px 12px", borderRadius: "8px 8px 8px 2px",
                  background: "var(--bg-primary)", border: "1px solid var(--border)",
                  fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)"
                }}>thinking...</div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div style={{
            padding: "10px", borderTop: "1px solid var(--border)",
            display: "flex", gap: "6px", background: "var(--bg-primary)"
          }}>
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask Nisaba..."
              style={{
                flex: 1, background: "var(--bg-secondary)",
                border: "1px solid var(--border)", borderRadius: "4px",
                color: "var(--text-primary)", fontFamily: "Outfit, sans-serif",
                fontSize: "11px", padding: "6px 10px", outline: "none"
              }}
            />
            <button onClick={send} disabled={loading || !input.trim()} style={{
              background: loading ? "transparent" : "var(--accent-gold)",
              border: "1px solid var(--accent-gold)",
              color: loading ? "var(--accent-gold)" : "var(--bg-primary)",
              borderRadius: "4px", padding: "6px 10px", cursor: loading ? "not-allowed" : "pointer",
              display: "flex", alignItems: "center", justifyContent: "center"
            }}>
              <Send size={12} />
            </button>
          </div>
        </div>
      )}

      {/* Orb button */}
      <button
        onClick={handleOpen}
        style={{
          width: "48px", height: "48px", borderRadius: "50%",
          background: hasAlerts ? "var(--danger)" : open ? "var(--accent-gold)" : "var(--bg-secondary)",
          border: `2px solid ${hasAlerts ? "var(--danger)" : "var(--accent-gold)"}`,
          cursor: "pointer",
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: hasAlerts
            ? "0 0 20px rgba(239,68,68,0.6)"
            : open ? "0 0 20px rgba(212,175,55,0.5)" : "0 0 12px rgba(212,175,55,0.2)",
          transition: "all 0.2s ease",
          animation: hasAlerts ? "orbPulse 1.5s ease-in-out infinite" : spinning ? "orbSpin 1s linear infinite" : "none"
        }}
        title={hasAlerts ? `${alerts.length} alert(s) — click to view` : "Ask Nisaba"}
      >
        {hasAlerts
          ? <AlertTriangle size={22} color="white" />
          : <Brain size={22} color={open ? "var(--bg-primary)" : "var(--accent-gold)"} style={{ transition: "color 0.2s ease" }} />
        }
      </button>
    </div>
  )
}

const miniBtn = {
  background: "transparent", border: "none",
  cursor: "pointer", padding: "3px",
  display: "flex", alignItems: "center", justifyContent: "center",
  borderRadius: "3px"
}
