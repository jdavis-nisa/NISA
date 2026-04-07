import { useState, useRef, useEffect } from "react"
import { Send, Cpu, Zap, Brain, Copy, Check } from "lucide-react"
import axios from "axios"
import ReactMarkdown from "react-markdown"
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter"
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism"
import remarkGfm from "remark-gfm"

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

      <div style={{
        border: "1px solid var(--border)",
        borderRadius: "4px",
        background: "var(--bg-panel)",
        display: "flex",
        alignItems: "flex-end",
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

function CodeBlock({ language, children }) {
  const [copied, setCopied] = useState(false)

  const copy = () => {
    navigator.clipboard.writeText(children)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div style={{ position: "relative", marginBottom: "8px" }}>
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "4px 12px",
        background: "#1e1e1e",
        borderRadius: "4px 4px 0 0",
        borderBottom: "1px solid var(--border)",
      }}>
        <span style={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "10px",
          color: "var(--accent-gold)",
          letterSpacing: "0.1em",
        }}>{language || "code"}</span>
        <button onClick={copy} style={{
          background: "transparent",
          border: "none",
          cursor: "pointer",
          color: copied ? "var(--success)" : "var(--text-dim)",
          display: "flex",
          alignItems: "center",
          gap: "4px",
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "9px",
          letterSpacing: "0.1em",
          padding: "2px 6px",
        }}>
          {copied ? <><Check size={10} /> COPIED</> : <><Copy size={10} /> COPY</>}
        </button>
      </div>
      <SyntaxHighlighter
        language={language || "text"}
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          borderRadius: "0 0 4px 4px",
          fontSize: "12px",
          lineHeight: "1.6",
          background: "#1e1e1e",
        }}
        showLineNumbers={true}
        lineNumberStyle={{
          color: "#444",
          fontSize: "10px",
          minWidth: "2.5em",
        }}
      >
        {children}
      </SyntaxHighlighter>
    </div>
  )
}

function Message({ msg }) {
  const isUser = msg.role === "user"

  const components = {
    code({ node, inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || "")
      const language = match ? match[1] : ""
      if (!inline && (match || String(children).includes("\n"))) {
        return <CodeBlock language={language}>{String(children).replace(/\n$/, "")}</CodeBlock>
      }
      return (
        <code style={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "11px",
          background: "var(--bg-elevated)",
          padding: "1px 6px",
          borderRadius: "2px",
          color: "var(--accent-cyan)",
          border: "1px solid var(--border)",
        }} {...props}>
          {children}
        </code>
      )
    },
    p({ children }) {
      return <p style={{
        margin: "0 0 8px 0",
        lineHeight: "1.7",
        color: "var(--text-primary)",
      }}>{children}</p>
    },
    h1({ children }) {
      return <h1 style={{
        fontFamily: "Rajdhani, sans-serif",
        fontWeight: 700,
        fontSize: "18px",
        letterSpacing: "0.1em",
        color: "var(--text-primary)",
        margin: "12px 0 6px 0",
        borderBottom: "1px solid var(--border)",
        paddingBottom: "4px",
      }}>{children}</h1>
    },
    h2({ children }) {
      return <h2 style={{
        fontFamily: "Rajdhani, sans-serif",
        fontWeight: 600,
        fontSize: "15px",
        letterSpacing: "0.1em",
        color: "var(--accent-gold)",
        margin: "10px 0 4px 0",
      }}>{children}</h2>
    },
    h3({ children }) {
      return <h3 style={{
        fontFamily: "Rajdhani, sans-serif",
        fontWeight: 600,
        fontSize: "13px",
        color: "var(--text-secondary)",
        margin: "8px 0 4px 0",
      }}>{children}</h3>
    },
    ul({ children }) {
      return <ul style={{
        paddingLeft: "20px",
        margin: "4px 0 8px 0",
        color: "var(--text-primary)",
      }}>{children}</ul>
    },
    ol({ children }) {
      return <ol style={{
        paddingLeft: "20px",
        margin: "4px 0 8px 0",
        color: "var(--text-primary)",
      }}>{children}</ol>
    },
    li({ children }) {
      return <li style={{
        marginBottom: "3px",
        lineHeight: "1.6",
        fontFamily: "Outfit, sans-serif",
        fontSize: "14px",
      }}>{children}</li>
    },
    blockquote({ children }) {
      return <blockquote style={{
        borderLeft: "2px solid var(--accent-gold-dim)",
        paddingLeft: "12px",
        margin: "8px 0",
        color: "var(--text-secondary)",
        fontStyle: "italic",
      }}>{children}</blockquote>
    },
    strong({ children }) {
      return <strong style={{
        color: "var(--text-primary)",
        fontWeight: 600,
      }}>{children}</strong>
    },
    table({ children }) {
      return (
        <div style={{ overflowX: "auto", marginBottom: "8px" }}>
          <table style={{
            borderCollapse: "collapse",
            width: "100%",
            fontFamily: "Outfit, sans-serif",
            fontSize: "13px",
          }}>{children}</table>
        </div>
      )
    },
    th({ children }) {
      return <th style={{
        padding: "6px 12px",
        background: "var(--bg-elevated)",
        borderBottom: "1px solid var(--border)",
        fontFamily: "Rajdhani, sans-serif",
        fontWeight: 600,
        fontSize: "11px",
        letterSpacing: "0.1em",
        color: "var(--text-dim)",
        textAlign: "left",
      }}>{children}</th>
    },
    td({ children }) {
      return <td style={{
        padding: "6px 12px",
        borderBottom: "1px solid var(--border)",
        color: "var(--text-secondary)",
      }}>{children}</td>
    },
  }

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: isUser ? "flex-end" : "flex-start",
      animation: "fadeInUp 0.3s ease forwards",
    }}>
      <div style={{
        maxWidth: isUser ? "80%" : "100%",
        width: isUser ? "auto" : "100%",
        padding: "12px 16px",
        borderRadius: "4px",
        background: isUser ? "var(--bg-elevated)" : "var(--bg-panel)",
        border: `1px solid ${isUser ? "var(--border-bright)" : "var(--border)"}`,
        borderLeft: isUser ? undefined : "2px solid var(--accent-gold-dim)",
        fontFamily: "Outfit, sans-serif",
        fontSize: "14px",
        lineHeight: "1.6",
        color: "var(--text-primary)",
      }}>
        {isUser ? (
          <span style={{ whiteSpace: "pre-wrap" }}>{msg.content}</span>
        ) : (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={components}
          >
            {msg.content}
          </ReactMarkdown>
        )}
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
