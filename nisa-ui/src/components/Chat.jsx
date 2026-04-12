import { useState, useRef, useEffect } from "react"
import { Send, Cpu, Zap, Brain, Copy, Check, Mic, MicOff, Save, Clock, Pencil, RefreshCw, Briefcase, Coffee } from "lucide-react"
import api from "../api"
import ReactMarkdown from "react-markdown"
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter"
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism"
import remarkGfm from "remark-gfm"

const NLU_API = "http://localhost:8081"
const NISA_API_KEY = "d551fd7e05134c52b84286c201f0f36d8ddeb5e0611ed771ba44d6a4264f39cf"

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
  const [showHistory, setShowHistory] = useState(false)
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [mode, setMode] = useState("work")

  const PERSONAL_TRIGGER = "PersonalMode"
  const WORK_TRIGGER = "WorkMode"

  const loadHistory = async () => {
    setHistoryLoading(true)
    try {
      const res = await api.get(`${NLU_API}/history?limit=200`)
      setHistory(res.data.sessions || [])
    } catch (e) {}
    setHistoryLoading(false)
  }

  const loadSession = (session) => {
    const restored = session.messages.map(m => ([
      { role: "user", content: m.user_message },
      { role: "assistant", content: m.nisaba_response }
    ])).flat().filter(m => m.content)
    setMessages([
      { role: "assistant", content: "Nisaba online. I am NISA — your Network Intelligence Security Assistant. How can I help you today?" },
      ...restored
    ])
    setShowHistory(false)
  }

  const bottomRef = useRef(null)
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const [recording, setRecording] = useState(false)
  const [mediaRecorder, setMediaRecorder] = useState(null)

  const startVoice = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      const chunks = []
      recorder.ondataavailable = e => chunks.push(e.data)
      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: "audio/webm" })
        const formData = new FormData()
        formData.append("audio", blob, "voice.webm")
        try {
          const res = await api.post(`${NLU_API}/voice`, formData, { headers: { "Content-Type": "multipart/form-data" } })
          if (res.data.transcript) setInput(res.data.transcript)
        } catch (e) { console.error("Voice transcription failed:", e) }
        stream.getTracks().forEach(t => t.stop())
        setRecording(false)
      }
      recorder.start()
      setMediaRecorder(recorder)
      setRecording(true)
    } catch (e) { console.error("Microphone access denied:", e) }
  }

  const stopVoice = () => {
    if (mediaRecorder) { mediaRecorder.stop(); setMediaRecorder(null) }
  }

  const send = async (overrideText = null, overrideMode = null) => {
    const text = (overrideText ?? input).trim()
    if (!text || loading) return

    let activeMode = overrideMode ?? mode
    if (text === PERSONAL_TRIGGER) {
      setMode("personal")
      activeMode = "personal"
      setInput("")
      setMessages(prev => [...prev,
        { role: "user", content: text },
        { role: "assistant", content: "— Switching to Personal Mode. Hey Josh, what's on your mind? —", model: "mode-switch", reason: "system" }
      ])
      return
    }
    if (text === WORK_TRIGGER) {
      setMode("work")
      activeMode = "work"
      setInput("")
      setMessages(prev => [...prev,
        { role: "user", content: text },
        { role: "assistant", content: "— Switching to Work Mode. Back to business. —", model: "mode-switch", reason: "system" }
      ])
      return
    }

    setInput("")
    setMessages(prev => [...prev, { role: "user", content: text }])
    setLoading(true)

    const assistantIdx = Date.now()
    setMessages(prev => [...prev, {
      role: "assistant", content: "", model: "...", moa: false,
      reason: "routing", streaming: true, id: assistantIdx
    }])

    try {
      const response = await fetch(`${NLU_API}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-NISA-API-Key": NISA_API_KEY },
        body: JSON.stringify({ message: text, mode: activeMode }),
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""
      let fullContent = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop()
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === "meta") {
              if (data.mode) setMode(data.mode)
              setMessages(prev => prev.map(m => m.id === assistantIdx ? { ...m, model: data.model, reason: data.reason } : m))
            } else if (data.type === "token") {
              fullContent += data.token
              setMessages(prev => prev.map(m => m.id === assistantIdx ? { ...m, content: fullContent } : m))
            } else if (data.type === "done") {
              setMessages(prev => prev.map(m => m.id === assistantIdx ? { ...m, streaming: false } : m))
            } else if (data.type === "error") {
              setMessages(prev => prev.map(m => m.id === assistantIdx ? { ...m, content: data.error, streaming: false } : m))
            }
          } catch {}
        }
      }
    } catch (e) {
      setMessages(prev => prev.map(m => m.id === assistantIdx ? {
        ...m, content: "Connection error. Verify NLU API is running on port 8081.", model: "error", streaming: false
      } : m))
    }
    setLoading(false)
  }

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send() }
  }

  const handleEdit = (idx) => {
    setInput(messages[idx].content)
  }

  const handleRegenerate = (idx) => {
    const userMsg = messages[idx - 1]
    if (userMsg && userMsg.role === "user") {
      setMessages(prev => prev.slice(0, idx - 1))
      send(userMsg.content, mode)
    }
  }

  const toggleMode = () => {
    const next = mode === "work" ? "personal" : "work"
    setMode(next)
    const notice = next === "personal"
      ? "— Switching to Personal Mode. Hey Josh, what's on your mind? —"
      : "— Switching to Work Mode. Back to business. —"
    setMessages(prev => [...prev, { role: "assistant", content: notice, model: "mode-switch", reason: "system" }])
  }

  const isPersonal = mode === "personal"

  return (
    <div className="fade-in" style={{
      height: "calc(100vh - 56px - 48px)", display: "flex", flexDirection: "column",
      maxWidth: "900px", margin: "0 auto", width: "100%",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingBottom: "8px" }}>
        <button onClick={toggleMode} title={isPersonal ? "Switch to Work Mode (or type WorkMode)" : "Switch to Personal Mode (or type PersonalMode)"} style={{
          display: "flex", alignItems: "center", gap: "6px", padding: "6px 12px",
          background: isPersonal ? "rgba(255,180,50,0.08)" : "transparent",
          border: `1px solid ${isPersonal ? "var(--accent-gold)" : "var(--border)"}`,
          borderRadius: "2px", color: isPersonal ? "var(--accent-gold)" : "var(--text-dim)",
          fontFamily: "Rajdhani, sans-serif", fontWeight: 600, fontSize: "10px",
          letterSpacing: "0.1em", cursor: "pointer", transition: "all 0.2s",
        }}>
          {isPersonal ? <><Coffee size={10} /> PERSONAL</> : <><Briefcase size={10} /> WORK</>}
        </button>
        <button onClick={() => { setShowHistory(true); loadHistory() }} style={{
          display: "flex", alignItems: "center", gap: "6px", padding: "6px 12px",
          background: "transparent", border: "1px solid var(--border)", borderRadius: "2px",
          color: "var(--text-dim)", fontFamily: "Rajdhani, sans-serif", fontWeight: 600,
          fontSize: "10px", letterSpacing: "0.1em", cursor: "pointer",
        }}>
          <Clock size={10} /> HISTORY
        </button>
      </div>

      {showHistory && (
        <div style={{
          position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
          background: "rgba(0,0,0,0.7)", zIndex: 1000,
          display: "flex", justifyContent: "center", alignItems: "flex-start", paddingTop: "60px"
        }} onClick={() => setShowHistory(false)}>
          <div style={{
            background: "var(--bg-secondary)", border: "1px solid var(--border)",
            borderRadius: "4px", width: "600px", maxHeight: "70vh",
            overflow: "hidden", display: "flex", flexDirection: "column"
          }} onClick={e => e.stopPropagation()}>
            <div style={{ padding: "16px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "13px", letterSpacing: "0.15em", color: "var(--accent-gold)" }}>CONVERSATION HISTORY</span>
              <button onClick={() => setShowHistory(false)} style={{ background: "none", border: "none", color: "var(--text-dim)", cursor: "pointer", fontSize: "18px" }}>x</button>
            </div>
            <div style={{ overflowY: "auto", flex: 1 }}>
              {historyLoading ? (
                <div style={{ padding: "20px", textAlign: "center", fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: "var(--text-dim)" }}>Loading...</div>
              ) : history.length === 0 ? (
                <div style={{ padding: "20px", textAlign: "center", fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: "var(--text-dim)" }}>No history found</div>
              ) : history.map((session, i) => (
                <div key={i} onClick={() => loadSession(session)} style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)", cursor: "pointer" }}
                  onMouseEnter={e => e.currentTarget.style.background = "var(--bg-primary)"}
                  onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                  <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "13px", color: "var(--text-primary)", marginBottom: "4px" }}>{session.first_message || "Untitled conversation"}</div>
                  <div style={{ display: "flex", gap: "12px" }}>
                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)" }}>{session.message_count} messages</span>
                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)" }}>{session.last_timestamp?.slice(0, 10)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "16px", paddingBottom: "16px" }}>
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} idx={i} onEdit={handleEdit} onRegenerate={handleRegenerate} isLast={i === messages.length - 1} />
        ))}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      <div style={{
        border: `1px solid ${isPersonal ? "var(--accent-gold-dim)" : "var(--border)"}`,
        borderRadius: "4px", background: "var(--bg-panel)",
        display: "flex", alignItems: "flex-end", marginTop: "8px", transition: "border-color 0.3s",
      }}>
        <textarea
          value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey}
          placeholder={isPersonal ? "Talk to Nisaba..." : "Message Nisaba..."}
          rows={1} style={{
            flex: 1, background: "transparent", border: "none", outline: "none",
            color: "var(--text-primary)", fontFamily: "Outfit, sans-serif", fontSize: "14px",
            padding: "14px 16px", resize: "none", lineHeight: "1.5",
          }}
        />
        <button onClick={recording ? stopVoice : startVoice} style={{
          padding: "14px 12px", background: "transparent", border: "none", cursor: "pointer",
          color: recording ? "var(--danger)" : "var(--text-dim)", transition: "color 0.2s", display: "flex", alignItems: "center",
        }} title={recording ? "Stop recording" : "Start voice input"}>
          {recording ? <MicOff size={16} /> : <Mic size={16} />}
        </button>
        <button onClick={() => send()} disabled={loading || !input.trim()} style={{
          padding: "14px 16px", background: "transparent", border: "none",
          cursor: loading || !input.trim() ? "not-allowed" : "pointer",
          color: loading || !input.trim() ? "var(--text-dim)" : "var(--accent-gold)",
          transition: "color 0.2s", display: "flex", alignItems: "center",
        }}>
          <Send size={16} />
        </button>
      </div>
      <div style={{
        fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)",
        textAlign: "center", marginTop: "6px", letterSpacing: "0.1em",
      }}>ENTER TO SEND — SHIFT+ENTER FOR NEW LINE — TYPE PersonalMode / WorkMode TO SWITCH</div>
    </div>
  )
}

const SAVE_DOMAINS = [
  { label: "Security", path: "/Volumes/Share Drive/NISA/knowledge/security" },
  { label: "Radar/EW", path: "/Volumes/Share Drive/NISA/knowledge/radar_ew" },
  { label: "Programs", path: "/Volumes/Share Drive/NISA/knowledge/programs" },
  { label: "General", path: "/Volumes/Share Drive/NISA/knowledge/general" },
  { label: "NISA Docs", path: "/Volumes/Share Drive/NISA/knowledge/nisa_docs" },
]

function CodeBlock({ language, children }) {
  const [copied, setCopied] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [showSaveMenu, setShowSaveMenu] = useState(false)

  const copy = () => {
    navigator.clipboard.writeText(children)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const saveToNISA = async (domain) => {
    setShowSaveMenu(false)
    setSaving(true)
    try {
      const ext = language || "txt"
      const filename = `nisa_code_${Date.now()}.${ext}`
      const res = await api.post("http://localhost:8081/save_code", {
        content: String(children), filename, domain_path: domain.path, language: language || "text"
      })
      if (res.data.status === "saved") { setSaved(true); setTimeout(() => setSaved(false), 3000) }
    } catch (e) { console.error("Save failed:", e) }
    setSaving(false)
  }

  return (
    <div style={{ position: "relative", marginBottom: "8px" }}>
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "4px 12px", background: "#1e1e1e", borderRadius: "4px 4px 0 0", borderBottom: "1px solid var(--border)",
      }}>
        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--accent-gold)", letterSpacing: "0.1em" }}>{language || "code"}</span>
        <button onClick={copy} style={{
          background: "transparent", border: "none", cursor: "pointer",
          color: copied ? "var(--success)" : "var(--text-dim)",
          display: "flex", alignItems: "center", gap: "4px",
          fontFamily: "JetBrains Mono, monospace", fontSize: "9px", letterSpacing: "0.1em", padding: "2px 6px",
        }}>
          {copied ? <><Check size={10} /> COPIED</> : <><Copy size={10} /> COPY</>}
        </button>
        <div style={{ position: "relative" }}>
          <button onClick={() => setShowSaveMenu(!showSaveMenu)} style={{
            display: "flex", alignItems: "center", gap: "4px", padding: "4px 8px",
            background: saved ? "var(--success)" : "var(--bg-primary)",
            border: "1px solid var(--border)", borderRadius: "3px",
            color: saved ? "var(--bg-primary)" : "var(--accent-gold)",
            fontFamily: "JetBrains Mono, monospace", fontSize: "9px", letterSpacing: "0.1em", cursor: "pointer",
          }}>
            {saved ? <><Check size={10} /> SAVED</> : saving ? "SAVING..." : <><Save size={10} /> SAVE TO NISA</>}
          </button>
          {showSaveMenu && (
            <div style={{
              position: "absolute", top: "100%", right: 0, zIndex: 100,
              background: "var(--bg-secondary)", border: "1px solid var(--border)",
              borderRadius: "4px", minWidth: "150px", boxShadow: "0 4px 12px rgba(0,0,0,0.4)",
            }}>
              {SAVE_DOMAINS.map(d => (
                <div key={d.label} onClick={() => saveToNISA(d)} style={{
                  padding: "8px 12px", fontFamily: "Rajdhani, sans-serif", fontWeight: 600,
                  fontSize: "11px", letterSpacing: "0.1em", color: "var(--text-secondary)",
                  cursor: "pointer", borderBottom: "1px solid var(--border)",
                }}
                onMouseEnter={e => e.target.style.color = "var(--accent-gold)"}
                onMouseLeave={e => e.target.style.color = "var(--text-secondary)"}
                >{d.label}</div>
              ))}
            </div>
          )}
        </div>
      </div>
      <SyntaxHighlighter language={language || "text"} style={vscDarkPlus}
        customStyle={{ margin: 0, borderRadius: "0 0 4px 4px", fontSize: "12px", lineHeight: "1.6", background: "#1e1e1e" }}
        showLineNumbers={true} lineNumberStyle={{ color: "#444", fontSize: "10px", minWidth: "2.5em" }}>
        {children}
      </SyntaxHighlighter>
    </div>
  )
}

function Message({ msg, idx, onEdit, onRegenerate, isLast }) {
  const isUser = msg.role === "user"
  const isSystemNotice = msg.model === "mode-switch"
  const [copied, setCopied] = useState(false)
  const [hovered, setHovered] = useState(false)

  const copyMessage = () => {
    navigator.clipboard.writeText(msg.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const components = {
    code({ node, inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || "")
      const language = match ? match[1] : ""
      if (!inline && (match || String(children).includes("\n"))) {
        return <CodeBlock language={language}>{String(children).replace(/\n$/, "")}</CodeBlock>
      }
      return <code style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px", background: "var(--bg-elevated)", padding: "1px 6px", borderRadius: "2px", color: "var(--accent-cyan)", border: "1px solid var(--border)" }} {...props}>{children}</code>
    },
    p({ children }) { return <p style={{ margin: "0 0 8px 0", lineHeight: "1.7", color: "var(--text-primary)" }}>{children}</p> },
    h1({ children }) { return <h1 style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "18px", letterSpacing: "0.1em", color: "var(--text-primary)", margin: "12px 0 6px 0", borderBottom: "1px solid var(--border)", paddingBottom: "4px" }}>{children}</h1> },
    h2({ children }) { return <h2 style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 600, fontSize: "15px", letterSpacing: "0.1em", color: "var(--accent-gold)", margin: "10px 0 4px 0" }}>{children}</h2> },
    h3({ children }) { return <h3 style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 600, fontSize: "13px", color: "var(--text-secondary)", margin: "8px 0 4px 0" }}>{children}</h3> },
    ul({ children }) { return <ul style={{ paddingLeft: "20px", margin: "4px 0 8px 0", color: "var(--text-primary)" }}>{children}</ul> },
    ol({ children }) { return <ol style={{ paddingLeft: "20px", margin: "4px 0 8px 0", color: "var(--text-primary)" }}>{children}</ol> },
    li({ children }) { return <li style={{ marginBottom: "3px", lineHeight: "1.6", fontFamily: "Outfit, sans-serif", fontSize: "14px" }}>{children}</li> },
    blockquote({ children }) { return <blockquote style={{ borderLeft: "2px solid var(--accent-gold-dim)", paddingLeft: "12px", margin: "8px 0", color: "var(--text-secondary)", fontStyle: "italic" }}>{children}</blockquote> },
    strong({ children }) { return <strong style={{ color: "var(--text-primary)", fontWeight: 600 }}>{children}</strong> },
    table({ children }) { return <div style={{ overflowX: "auto", marginBottom: "8px" }}><table style={{ borderCollapse: "collapse", width: "100%", fontFamily: "Outfit, sans-serif", fontSize: "13px" }}>{children}</table></div> },
    th({ children }) { return <th style={{ padding: "6px 12px", background: "var(--bg-elevated)", borderBottom: "1px solid var(--border)", fontFamily: "Rajdhani, sans-serif", fontWeight: 600, fontSize: "11px", letterSpacing: "0.1em", color: "var(--text-dim)", textAlign: "left" }}>{children}</th> },
    td({ children }) { return <td style={{ padding: "6px 12px", borderBottom: "1px solid var(--border)", color: "var(--text-secondary)" }}>{children}</td> },
  }

  if (isSystemNotice) {
    return (
      <div style={{ textAlign: "center", padding: "4px 0" }}>
        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--accent-gold)", letterSpacing: "0.1em", opacity: 0.7 }}>{msg.content}</span>
      </div>
    )
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: isUser ? "flex-end" : "flex-start", animation: "fadeInUp 0.3s ease forwards", position: "relative" }}
      onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)}>
      <div style={{
        maxWidth: isUser ? "80%" : "100%", width: isUser ? "auto" : "100%",
        padding: "12px 16px", borderRadius: "4px",
        background: isUser ? "var(--bg-elevated)" : "var(--bg-panel)",
        border: `1px solid ${isUser ? "var(--border-bright)" : "var(--border)"}`,
        borderLeft: isUser ? undefined : "2px solid var(--accent-gold-dim)",
        fontFamily: "Outfit, sans-serif", fontSize: "14px", lineHeight: "1.6", color: "var(--text-primary)",
      }}>
        {isUser ? (
          <span style={{ whiteSpace: "pre-wrap" }}>{msg.content}</span>
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>{msg.content}</ReactMarkdown>
        )}
      </div>

      {hovered && !msg.streaming && (
        <div style={{ display: "flex", gap: "4px", marginTop: "4px", alignSelf: isUser ? "flex-end" : "flex-start" }}>
          <ActionBtn onClick={copyMessage} title="Copy message">
            {copied ? <Check size={10} /> : <Copy size={10} />}
          </ActionBtn>
          {isUser && (
            <ActionBtn onClick={() => onEdit(idx)} title="Edit and resubmit">
              <Pencil size={10} />
            </ActionBtn>
          )}
          {!isUser && isLast && (
            <ActionBtn onClick={() => onRegenerate(idx)} title="Regenerate response">
              <RefreshCw size={10} />
            </ActionBtn>
          )}
        </div>
      )}

      {!isUser && msg.model && msg.model !== "error" && (
        <ModelBadge model={msg.model} moa={msg.moa} reason={msg.reason} />
      )}
    </div>
  )
}

function ActionBtn({ onClick, title, children }) {
  return (
    <button onClick={onClick} title={title} style={{
      background: "var(--bg-secondary)", border: "1px solid var(--border)",
      borderRadius: "2px", padding: "3px 6px", cursor: "pointer",
      color: "var(--text-dim)", display: "flex", alignItems: "center", transition: "color 0.15s",
    }}
    onMouseEnter={e => e.currentTarget.style.color = "var(--accent-gold)"}
    onMouseLeave={e => e.currentTarget.style.color = "var(--text-dim)"}
    >{children}</button>
  )
}

function ModelBadge({ model, moa, reason }) {
  const Icon = moa ? Brain : reason === "security" ? Zap : Cpu
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "4px", padding: "3px 8px", border: "1px solid var(--border)", borderRadius: "2px", background: "var(--bg-secondary)" }}>
      <Icon size={10} color="var(--accent-gold)" />
      <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", letterSpacing: "0.1em" }}>{model}</span>
      {moa && <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--accent-cyan)", letterSpacing: "0.1em" }}>MoA</span>}
      {reason && reason !== "system" && <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", letterSpacing: "0.1em" }}>— {reason}</span>}
    </div>
  )
}

function TypingIndicator() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "6px", padding: "12px 16px", border: "1px solid var(--border)", borderLeft: "2px solid var(--accent-gold-dim)", borderRadius: "4px", background: "var(--bg-panel)", width: "fit-content" }}>
      {[0, 1, 2].map(i => (
        <div key={i} style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--accent-gold)", animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite` }} />
      ))}
      <style>{`@keyframes pulse { 0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); } 40% { opacity: 1; transform: scale(1); } }`}</style>
    </div>
  )
}
