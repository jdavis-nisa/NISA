import { useState, useRef, useEffect } from "react"
import { Send, Cpu, Zap, Brain } from "lucide-react"
import axios from "axios"

const NLU_API = "http://localhost:8081"

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Nisaba online. I am NISA — your Network Intelligence Security Assistant. How can I help you today?",
      model: "qwen/qwen3-32b",
      moa: false,
      reason: "system",
    }
  ])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return
    setInput("")
    setMessages(prev => [...prev, { role: "user", content: text }])
    setLoading(true)
    try {
      const res = await axios.post(`${NLU_API}/chat`, { message: text })
      setMessages(prev => [...prev, {
        role: "assistant",
        content: res.data.response,
        model: res.data.model_used,
        moa: res.data.moa_used,
        reason: res.data.routing_reason,
      }])
    } catch (e) {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Connection error. Verify NLU API is running on port 8081.",
        model: "error",
        moa: false,
        reason: "error",
      }])
    }
    setLoading(false)
  }

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="fade-in" style={{
      height: "calc(100vh - 56px - 48px)",
      display: "flex",
      flexDirection: "column",
      maxWidth: "900px",
      margin: "0 auto",
      width: "100%",
    }}>
      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: "auto",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        paddingBottom: "16px",
      }}>
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} />
        ))}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{
        border: "1px solid var(--border)",
        borderRadius: "4px",
        background: "var(--bg-panel)",
        display: "flex",
        alignItems: "flex-end",
        gap: "0",
        marginTop: "8px",
      }}>
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Message Nisaba..."
          rows={1}
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            outline: "none",
            color: "var(--text-primary)",
            fontFamily: "Outfit, sans-serif",
            fontSize: "14px",
            padding: "14px 16px",
            resize: "none",
            lineHeight: "1.5",
          }}
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          style={{
            padding: "14px 16px",
            background: "transparent",
            border: "none",
            cursor: loading || !input.trim() ? "not-allowed" : "pointer",
            color: loading || !input.trim() ? "var(--text-dim)" : "var(--accent-gold)",
            transition: "color 0.2s",
            display: "flex",
            alignItems: "center",
          }}
        >
          <Send size={16} />
        </button>
      </div>
      <div style={{
        fontFamily: "JetBrains Mono, monospace",
        fontSize: "9px",
        color: "var(--text-dim)",
        textAlign: "center",
        marginTop: "6px",
        letterSpacing: "0.1em",
      }}>ENTER TO SEND — SHIFT+ENTER FOR NEW LINE</div>
    </div>
  )
}

function Message({ msg }) {
  const isUser = msg.role === "user"
  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: isUser ? "flex-end" : "flex-start",
      animation: "fadeInUp 0.3s ease forwards",
    }}>
      <div style={{
        maxWidth: "80%",
        padding: "12px 16px",
        borderRadius: "4px",
        background: isUser ? "var(--bg-elevated)" : "var(--bg-panel)",
        border: `1px solid ${isUser ? "var(--border-bright)" : "var(--border)"}`,
        borderLeft: isUser ? undefined : "2px solid var(--accent-gold-dim)",
        fontFamily: "Outfit, sans-serif",
        fontSize: "14px",
        lineHeight: "1.6",
        color: "var(--text-primary)",
        whiteSpace: "pre-wrap",
      }}>
        {msg.content}
      </div>
      {!isUser && msg.model && msg.model !== "error" && (
        <ModelBadge model={msg.model} moa={msg.moa} reason={msg.reason} />
      )}
    </div>
  )
}

function ModelBadge({ model, moa, reason }) {
  const Icon = moa ? Brain : reason === "security" ? Zap : Cpu
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: "6px",
      marginTop: "4px",
      padding: "3px 8px",
      border: "1px solid var(--border)",
      borderRadius: "2px",
      background: "var(--bg-secondary)",
    }}>
      <Icon size={10} color="var(--accent-gold)" />
      <span style={{
        fontFamily: "JetBrains Mono, monospace",
        fontSize: "9px",
        color: "var(--text-dim)",
        letterSpacing: "0.1em",
      }}>{model}</span>
      {moa && (
        <span style={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "9px",
          color: "var(--accent-cyan)",
          letterSpacing: "0.1em",
        }}>MoA</span>
      )}
      {reason && reason !== "system" && (
        <span style={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "9px",
          color: "var(--text-dim)",
          letterSpacing: "0.1em",
        }}>— {reason}</span>
      )}
    </div>
  )
}

function TypingIndicator() {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: "6px",
      padding: "12px 16px",
      border: "1px solid var(--border)",
      borderLeft: "2px solid var(--accent-gold-dim)",
      borderRadius: "4px",
      background: "var(--bg-panel)",
      width: "fit-content",
    }}>
      {[0, 1, 2].map(i => (
        <div key={i} style={{
          width: "6px", height: "6px",
          borderRadius: "50%",
          background: "var(--accent-gold)",
          animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
        }} />
      ))}
      <style>{`
        @keyframes pulse {
          0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
          40% { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </div>
  )
}
