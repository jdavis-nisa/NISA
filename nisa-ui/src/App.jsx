import { useState, useEffect, useRef } from "react"
import { HashRouter, Routes, Route, NavLink, useLocation } from "react-router-dom"
import { MessageSquare, Shield, FileText, Activity, Search, Brain, Crosshair, BarChart2, Play, Server, Bell, Map } from "lucide-react"
import { onNewContext } from "./SessionContext"
import Chat from "./components/Chat"
import Security from "./components/Security"
import Compliance from "./components/Compliance"
import Remediation from "./components/Remediation"
import Charts from "./components/Charts"
import Forensics from "./components/Forensics"
import Memory from "./components/Memory"
import RedTeam from "./components/RedTeam"
import Signal from "./components/Signal"
import Metasploit from "./components/Metasploit"
import NetworkTopology from './components/NetworkTopology'
import ThreatIntel from './components/ThreatIntel'
import AdversarialSim from './components/AdversarialSim'
import Playbook from './components/Playbook'
import AssetInventory from './components/AssetInventory'
import CVEWatchlist from './components/CVEWatchlist'
import AttackSurface from './components/AttackSurface'
import NisabaOrb from './components/NisabaOrb'

function App() {
  return (
    <HashRouter>
      <div style={{ position: "relative", zIndex: 1, minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <Header />
        <div style={{ display: "flex", flex: 1 }}>
          <Sidebar />
          <main style={{ flex: 1, padding: "24px", overflowY: "auto" }}>
            <Routes>
              <Route path="/" element={<Chat />} />
              <Route path="/security" element={<Security />} />
              <Route path="/forensics" element={<Forensics />} />
              <Route path="/memory" element={<Memory />} />
              <Route path="/redteam" element={<RedTeam />} />
              <Route path="/remediation" element={<Remediation />} />
              <Route path="/charts" element={<Charts />} />
              <Route path="/compliance" element={<Compliance />} />
              <Route path="/signal" element={<Signal />} />
              <Route path="/metasploit" element={<Metasploit />} />
              <Route path="/topology" element={<NetworkTopology standalone={true} />} />
              <Route path="/threatintel" element={<ThreatIntel />} />
              <Route path="/adversarial" element={<AdversarialSim />} />
              <Route path="/playbook" element={<Playbook />} />
              <Route path="/assets" element={<AssetInventory />} />
              <Route path="/watchlist" element={<CVEWatchlist />} />
              <Route path="/attacksurface" element={<AttackSurface />} />
            </Routes>
          </main>
        </div>
      </div>
      <NisabaOrb />
    </HashRouter>
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
        <StatusDot label="FORENSICS API" port={8083} />
        <StatusDot label="RED TEAM API" port={8084} />
        <StatusDot label="SURICATA IDS" port={8085} />
        <StatusDot label="METASPLOIT" port={8089} />
        <StatusDot label="SIGNAL API" port={8088} />
        <StatusDot label="PHOENIX" port={6006} />
        <StatusDot label="SESSION CTX" port={8095} />
        <StatusDot label="PLAYBOOK" port={8096} />
        <StatusDot label="ASSETS" port={8097} />
        <StatusDot label="WATCHLIST" port={8098} />
        <div style={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "10px",
          color: "var(--text-dim)",
          letterSpacing: "0.1em",
        }}>v0.4.0</div>
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
  const [chatPulse, setChatPulse] = useState(false)
  const [pendingContext, setPendingContext] = useState(null)
  const location = useLocation()
  const pulseTimer = useRef(null)

  useEffect(() => {
    const unsub = onNewContext((entry) => {
      // Only pulse if not already on Chat tab
      if (location.pathname !== "/") {
        setChatPulse(true)
        setPendingContext(entry)
        // Keep pulsing until user visits Chat
      }
    })
    return unsub
  }, [location.pathname])

  useEffect(() => {
    // Clear pulse when user navigates to Chat
    if (location.pathname === "/") {
      setChatPulse(false)
      setPendingContext(null)
    }
  }, [location.pathname])

  const navItems = [
    { to: "/", icon: MessageSquare, label: "CHAT", sublabel: "Nisaba" },
    { to: "/security", icon: Shield, label: "SECURITY", sublabel: "Scan & Analyze" },
    { to: "/forensics", icon: Search, label: "FORENSICS", sublabel: "Log Analysis & IOC" },
    { to: "/memory", icon: Brain, label: "MEMORY", sublabel: "ChromaDB Explorer" },
    { to: "/redteam", icon: Crosshair, label: "RED TEAM", sublabel: "Attack & Evaluate" },
    { to: "/remediation", icon: Shield, label: "REMEDIATION", sublabel: "Patch & Verify" },
    { to: "/charts", icon: BarChart2, label: "VISUALIZE", sublabel: "Charts & Analytics" },
    { to: "/compliance", icon: FileText, label: "COMPLIANCE", sublabel: "Audit Reports" },
    { to: "/signal", icon: Activity, label: "SIGNAL", sublabel: "Waveform & Radar" },
    { to: "/metasploit", icon: Shield, label: "METASPLOIT", sublabel: "Exploit Framework" },
    { to: "/topology", icon: Shield, label: "TOPOLOGY", sublabel: "Network Graph" },
    { to: "/threatintel", icon: Shield, label: "THREAT INTEL", sublabel: "CVE & ATT&CK" },
    { to: "/adversarial", icon: Shield, label: "ADVERSARIAL", sublabel: "Kill Chain Sim" },
    { to: "/playbook", icon: Play, label: "PLAYBOOK", sublabel: "Automated Workflows" },
    { to: "/assets", icon: Server, label: "ASSETS", sublabel: "Asset Inventory" },
    { to: "/watchlist", icon: Bell, label: "WATCHLIST", sublabel: "CVE Monitoring" },
    { to: "/attacksurface", icon: Map, label: "ATTACK SURFACE", sublabel: "Exposure Map" },
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
      {navItems.map(({ to, icon: Icon, label, sublabel }) => {
        const isChatTab = to === "/"
        const isPulsing = isChatTab && chatPulse
        return (
          <NavLink key={to} to={to} end={to === "/"} style={({ isActive }) => ({
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "10px 16px",
            textDecoration: "none",
            borderLeft: isActive ? "2px solid var(--accent-gold)" : isPulsing ? "2px solid var(--accent-cyan, #00d4ff)" : "2px solid transparent",
            background: isActive ? "var(--accent-gold-glow)" : isPulsing ? "rgba(0,212,255,0.06)" : "transparent",
            transition: "all 0.2s ease",
            animation: isPulsing ? "chatPulse 2s ease-in-out infinite" : "none",
          })}>
            {({ isActive }) => (
              <>
                <div style={{ position: "relative" }}>
                  <Icon size={16} color={isActive ? "var(--accent-gold)" : isPulsing ? "var(--accent-cyan, #00d4ff)" : "var(--text-dim)"} />
                  {isPulsing && (
                    <div style={{
                      position: "absolute",
                      top: "-3px",
                      right: "-3px",
                      width: "6px",
                      height: "6px",
                      borderRadius: "50%",
                      background: "var(--accent-cyan, #00d4ff)",
                      boxShadow: "0 0 6px var(--accent-cyan, #00d4ff)",
                      animation: "chatPulse 2s ease-in-out infinite",
                    }} />
                  )}
                </div>
                <div>
                  <div style={{
                    fontFamily: "Rajdhani, sans-serif",
                    fontWeight: 600,
                    fontSize: "12px",
                    letterSpacing: "0.15em",
                    color: isActive ? "var(--accent-gold)" : isPulsing ? "var(--accent-cyan, #00d4ff)" : "var(--text-secondary)",
                  }}>{label}</div>
                  <div style={{
                    fontFamily: "Outfit, sans-serif",
                    fontSize: "10px",
                    color: isPulsing ? "var(--accent-cyan, #00d4ff)" : "var(--text-dim)",
                  }}>{isPulsing && pendingContext ? `New: ${pendingContext.tab}` : sublabel}</div>
                </div>
              </>
            )}
          </NavLink>
        )
      })}
    </nav>
  )
}

export default App
