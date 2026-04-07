import { useState } from "react"
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom"
import { MessageSquare, Shield, FileText, Activity } from "lucide-react"
import Chat from "./components/Chat"
import Security from "./components/Security"
import Compliance from "./components/Compliance"

function App() {
  return (
    <BrowserRouter>
      <div style={{ position: "relative", zIndex: 1, minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <Header />
        <div style={{ display: "flex", flex: 1 }}>
          <Sidebar />
          <main style={{ flex: 1, padding: "24px", overflowY: "auto" }}>
            <Routes>
              <Route path="/" element={<Chat />} />
              <Route path="/security" element={<Security />} />
              <Route path="/compliance" element={<Compliance />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  )
}

function Header() {
  return (
    <header style={{
      borderBottom: "1px solid var(--border)",
      padding: "0 24px",
      height: "56px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      background: "var(--bg-secondary)",
      position: "relative",
      zIndex: 10,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <div style={{
          width: "32px", height: "32px",
          border: "1px solid var(--accent-gold)",
          display: "flex", alignItems: "center", justifyContent: "center",
          transform: "rotate(45deg)",
        }}>
          <div style={{
            width: "12px", height: "12px",
            background: "var(--accent-gold)",
            transform: "rotate(0deg)",
          }} />
        </div>
        <div>
          <div style={{
            fontFamily: "Rajdhani, sans-serif",
            fontWeight: 700,
            fontSize: "18px",
            letterSpacing: "0.15em",
            color: "var(--text-primary)",
            lineHeight: 1,
          }}>NISA</div>
          <div style={{
            fontFamily: "JetBrains Mono, monospace",
            fontSize: "9px",
            color: "var(--accent-gold)",
            letterSpacing: "0.2em",
            lineHeight: 1,
            marginTop: "2px",
          }}>NETWORK INTELLIGENCE SECURITY ASSISTANT</div>
        </div>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
        <StatusDot label="NLU API" port={8081} />
        <StatusDot label="SECURITY API" port={8082} />
        <div style={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "10px",
          color: "var(--text-dim)",
          letterSpacing: "0.1em",
        }}>v0.2.0</div>
      </div>
    </header>
  )
}

function StatusDot({ label, port }) {
  const [online, setOnline] = useState(null)
  useState(() => {
    fetch(`http://localhost:${port}/health`)
      .then(() => setOnline(true))
      .catch(() => setOnline(false))
  }, [])
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
      <div style={{
        width: "6px", height: "6px", borderRadius: "50%",
        background: online === null ? "var(--text-dim)" : online ? "var(--success)" : "var(--danger)",
        boxShadow: online ? "0 0 6px var(--success)" : "none",
      }} />
      <span style={{
        fontFamily: "JetBrains Mono, monospace",
        fontSize: "9px",
        color: "var(--text-dim)",
        letterSpacing: "0.1em",
      }}>{label}</span>
    </div>
  )
}

function Sidebar() {
  const navItems = [
    { to: "/", icon: MessageSquare, label: "CHAT", sublabel: "Nisaba" },
    { to: "/security", icon: Shield, label: "SECURITY", sublabel: "Scan & Analyze" },
    { to: "/compliance", icon: FileText, label: "COMPLIANCE", sublabel: "Audit Reports" },
  ]
  return (
    <nav style={{
      width: "200px",
      borderRight: "1px solid var(--border)",
      background: "var(--bg-secondary)",
      padding: "16px 0",
      display: "flex",
      flexDirection: "column",
      gap: "4px",
    }}>
      {navItems.map(({ to, icon: Icon, label, sublabel }) => (
        <NavLink key={to} to={to} end={to === "/"} style={({ isActive }) => ({
          display: "flex",
          alignItems: "center",
          gap: "12px",
          padding: "10px 16px",
          textDecoration: "none",
          borderLeft: isActive ? "2px solid var(--accent-gold)" : "2px solid transparent",
          background: isActive ? "var(--accent-gold-glow)" : "transparent",
          transition: "all 0.2s ease",
        })}>
          {({ isActive }) => (
            <>
              <Icon size={16} color={isActive ? "var(--accent-gold)" : "var(--text-dim)"} />
              <div>
                <div style={{
                  fontFamily: "Rajdhani, sans-serif",
                  fontWeight: 600,
                  fontSize: "12px",
                  letterSpacing: "0.15em",
                  color: isActive ? "var(--accent-gold)" : "var(--text-secondary)",
                }}>{label}</div>
                <div style={{
                  fontFamily: "Outfit, sans-serif",
                  fontSize: "10px",
                  color: "var(--text-dim)",
                }}>{sublabel}</div>
              </div>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}

export default App
