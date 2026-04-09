import { useState } from "react"
import { pushContext } from "../SessionContext"
import { Search, FileSearch, Hash, Clock, AlertTriangle, CheckCircle, ChevronRight, Network } from "lucide-react"
import api from "../api"

const FORENSICS_API = "http://localhost:8083"

export default function Forensics() {
  const [activeTab, setActiveTab] = useState("logs")

  return (
    <div className="fade-in" style={{ maxWidth: "900px", margin: "0 auto" }}>
      <PageHeader
        icon={FileSearch}
        title="FORENSICS"
        subtitle="Log analysis, IOC extraction, file integrity, pcap analysis"
      />

      {/* Tabs */}
      <div style={{
        display: "flex",
        gap: "0",
        borderBottom: "1px solid var(--border)",
        marginBottom: "24px",
      }}>
        {[
          { id: "logs", label: "LOG ANALYSIS", icon: Search },
          { id: "ioc", label: "IOC EXTRACTOR", icon: AlertTriangle },
          { id: "hash", label: "FILE HASH", icon: Hash },
          { id: "pcap", label: "PCAP ANALYSIS", icon: Network },
        ].map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setActiveTab(id)} style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "10px 20px",
            background: "transparent",
            border: "none",
            borderBottom: activeTab === id ? "2px solid var(--accent-gold)" : "2px solid transparent",
            color: activeTab === id ? "var(--accent-gold)" : "var(--text-dim)",
            fontFamily: "Rajdhani, sans-serif",
            fontWeight: 600,
            fontSize: "12px",
            letterSpacing: "0.15em",
            cursor: "pointer",
            transition: "all 0.2s",
            marginBottom: "-1px",
          }}>
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {activeTab === "logs" && <LogAnalysisPanel />}
      {activeTab === "ioc" && <IOCPanel />}
      {activeTab === "hash" && <HashPanel />}
      {activeTab === "pcap" && <PcapPanel />}
    </div>
  )
}

function LogAnalysisPanel() {
  const [logText, setLogText] = useState("")
  const [logType, setLogType] = useState("auth")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const analyze = async () => {
    if (!logText.trim()) return
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const res = await api.post(`${FORENSICS_API}/analyze/logs`, {
        log_text: logText,
        log_type: logType
      })
      setResult(res.data)
      pushContext({ tab: 'Forensics', operation: 'Log Analysis', summary: `Log analysis complete - type: ${logType}. ${res.data.summary || ''}`.trim(), detail: null })
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  const severityColor = {
    critical: "var(--danger)",
    high: "var(--warning)",
    medium: "var(--accent-cyan)",
    low: "var(--text-dim)",
  }

  const riskColor = {
    CRITICAL: "var(--danger)",
    HIGH: "var(--warning)",
    MEDIUM: "var(--accent-cyan)",
    LOW: "var(--text-secondary)",
    CLEAN: "var(--success)",
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <Panel title="LOG INPUT">
        <div style={{ display: "flex", gap: "12px", marginBottom: "10px" }}>
          <div>
            <FieldLabel>LOG TYPE</FieldLabel>
            <select value={logType} onChange={e => setLogType(e.target.value)} style={inputStyle}>
              <option value="auth">Auth / SSH</option>
              <option value="system">System</option>
              <option value="web">Web Server</option>
              <option value="firewall">Firewall</option>
              <option value="generic">Generic</option>
            </select>
          </div>
          <div style={{ display: "flex", alignItems: "flex-end" }}>
            <ScanButton onClick={analyze} loading={loading} label="ANALYZE" />
          </div>
        </div>
        <FieldLabel>PASTE LOG DATA</FieldLabel>
        <textarea
          value={logText}
          onChange={e => setLogText(e.target.value)}
          placeholder="Paste log entries here..."
          rows={8}
          style={{
            ...inputStyle,
            width: "100%",
            resize: "vertical",
            fontFamily: "JetBrains Mono, monospace",
            fontSize: "11px",
            lineHeight: "1.6",
          }}
        />
      </Panel>

      {loading && <LoadingPanel label="Analyzing logs with RedSage..." />}
      {error && <ErrorPanel message={error} />}

      {result && (
        <>
          {/* Risk Banner */}
          <div style={{
            padding: "12px 16px",
            border: `1px solid ${riskColor[result.risk_level]}`,
            borderLeft: `3px solid ${riskColor[result.risk_level]}`,
            borderRadius: "4px",
            background: "var(--bg-panel)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}>
            <span style={{
              fontFamily: "Outfit, sans-serif",
              fontSize: "13px",
              color: "var(--text-secondary)",
            }}>{result.summary}</span>
            <span style={{
              fontFamily: "Rajdhani, sans-serif",
              fontWeight: 700,
              fontSize: "14px",
              letterSpacing: "0.15em",
              color: riskColor[result.risk_level],
            }}>{result.risk_level}</span>
          </div>

          {/* Findings */}
          {result.findings.length > 0 && (
            <Panel title={`FINDINGS (${result.findings.length})`}>
              {result.findings.map((f, i) => (
                <div key={i} style={{
                  padding: "8px 12px",
                  borderLeft: `2px solid ${severityColor[f.severity] || "var(--border)"}`,
                  background: "var(--bg-secondary)",
                  marginBottom: "6px",
                  borderRadius: "0 2px 2px 0",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  gap: "12px",
                }}>
                  <div>
                    <div style={{ display: "flex", gap: "8px", marginBottom: "3px", alignItems: "center" }}>
                      <span style={{
                        fontFamily: "Rajdhani, sans-serif",
                        fontWeight: 600,
                        fontSize: "11px",
                        letterSpacing: "0.1em",
                        color: severityColor[f.severity],
                      }}>{f.type}</span>
                      <span style={{
                        fontFamily: "JetBrains Mono, monospace",
                        fontSize: "9px",
                        color: "var(--text-dim)",
                      }}>LINE {f.line}</span>
                    </div>
                    <div style={{
                      fontFamily: "JetBrains Mono, monospace",
                      fontSize: "10px",
                      color: "var(--text-secondary)",
                    }}>{f.content}</div>
                  </div>
                  <span style={{
                    fontFamily: "JetBrains Mono, monospace",
                    fontSize: "9px",
                    color: severityColor[f.severity],
                    whiteSpace: "nowrap",
                    flexShrink: 0,
                  }}>{f.severity.toUpperCase()}</span>
                </div>
              ))}
            </Panel>
          )}

          {/* IOCs */}
          {Object.keys(result.iocs).length > 0 && (
            <Panel title="EXTRACTED IOCs">
              {Object.entries(result.iocs).map(([type, values]) => (
                <div key={type} style={{ marginBottom: "10px" }}>
                  <div style={{
                    fontFamily: "Rajdhani, sans-serif",
                    fontWeight: 600,
                    fontSize: "10px",
                    letterSpacing: "0.15em",
                    color: "var(--accent-gold)",
                    marginBottom: "4px",
                  }}>{type.toUpperCase()}</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                    {values.map((v, i) => (
                      <span key={i} style={{
                        fontFamily: "JetBrains Mono, monospace",
                        fontSize: "10px",
                        color: "var(--text-secondary)",
                        background: "var(--bg-secondary)",
                        border: "1px solid var(--border)",
                        padding: "2px 8px",
                        borderRadius: "2px",
                      }}>{v}</span>
                    ))}
                  </div>
                </div>
              ))}
            </Panel>
          )}

          {/* RedSage Analysis */}
          {result.analysis && (
            <Panel title="REDSAGE FORENSIC ANALYSIS">
              <div style={{
                fontFamily: "Outfit, sans-serif",
                fontSize: "13px",
                lineHeight: "1.7",
                color: "var(--text-primary)",
                whiteSpace: "pre-wrap",
              }}>{result.analysis}</div>
            </Panel>
          )}
        </>
      )}
    </div>
  )
}

function IOCPanel() {
  const [text, setText] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const extract = async () => {
    if (!text.trim()) return
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const res = await api.post(`${FORENSICS_API}/extract/iocs`, { text })
      setResult(res.data)
      pushContext({ tab: 'Forensics', operation: 'IOC Extraction', summary: `IOC extraction complete. ${res.data.summary || `${res.data.iocs?.length ?? 0} IOCs found`}`.trim(), detail: null })
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <Panel title="IOC EXTRACTION">
        <FieldLabel>PASTE ANY TEXT — EMAILS, LOGS, REPORTS, THREAT INTEL</FieldLabel>
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Paste text containing IPs, domains, hashes, URLs, CVEs..."
          rows={8}
          style={{
            ...inputStyle,
            width: "100%",
            resize: "vertical",
            fontFamily: "JetBrains Mono, monospace",
            fontSize: "11px",
            lineHeight: "1.6",
            marginBottom: "10px",
          }}
        />
        <ScanButton onClick={extract} loading={loading} label="EXTRACT IOCs" />
      </Panel>

      {loading && <LoadingPanel label="Extracting IOCs..." />}
      {error && <ErrorPanel message={error} />}

      {result && (
        <>
          <Panel title={`IOCs FOUND (${result.total})`}>
            {Object.keys(result.iocs).length === 0 ? (
              <div style={{
                fontFamily: "JetBrains Mono, monospace",
                fontSize: "11px",
                color: "var(--text-dim)",
              }}>No IOCs detected in provided text.</div>
            ) : (
              Object.entries(result.iocs).map(([type, values]) => (
                <div key={type} style={{ marginBottom: "12px" }}>
                  <div style={{
                    fontFamily: "Rajdhani, sans-serif",
                    fontWeight: 600,
                    fontSize: "10px",
                    letterSpacing: "0.15em",
                    color: "var(--accent-gold)",
                    marginBottom: "6px",
                  }}>{type.toUpperCase()} ({values.length})</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                    {values.map((v, i) => (
                      <span key={i} style={{
                        fontFamily: "JetBrains Mono, monospace",
                        fontSize: "10px",
                        color: "var(--text-secondary)",
                        background: "var(--bg-secondary)",
                        border: "1px solid var(--border)",
                        padding: "2px 8px",
                        borderRadius: "2px",
                      }}>{v}</span>
                    ))}
                  </div>
                </div>
              ))
            )}
          </Panel>
          {result.analysis && (
            <Panel title="REDSAGE ANALYSIS">
              <div style={{
                fontFamily: "Outfit, sans-serif",
                fontSize: "13px",
                lineHeight: "1.7",
                color: "var(--text-primary)",
                whiteSpace: "pre-wrap",
              }}>{result.analysis}</div>
            </Panel>
          )}
        </>
      )}
    </div>
  )
}

function HashPanel() {
  const [filePath, setFilePath] = useState("")
  const [expectedHash, setExpectedHash] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const check = async () => {
    if (!filePath.trim()) return
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const res = await api.post(`${FORENSICS_API}/hash/file`, {
        file_path: filePath,
        expected_hash: expectedHash || null
      })
      setResult(res.data)
      pushContext({ tab: 'Forensics', operation: 'File Hash Analysis', summary: `Hash analysis: ${res.data.file_path || filePath} - ${res.data.verdict || res.data.status || 'complete'}`, detail: null })
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <Panel title="FILE INTEGRITY CHECK">
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div>
            <FieldLabel>FILE PATH</FieldLabel>
            <input
              value={filePath}
              onChange={e => setFilePath(e.target.value)}
              placeholder="/Users/joshuadavis/NISA/src/core/nlu_api.py"
              style={{ ...inputStyle, width: "100%" }}
            />
          </div>
          <div>
            <FieldLabel>EXPECTED SHA256 (OPTIONAL — FOR VERIFICATION)</FieldLabel>
            <input
              value={expectedHash}
              onChange={e => setExpectedHash(e.target.value)}
              placeholder="Leave blank to just compute hash"
              style={{ ...inputStyle, width: "100%" }}
            />
          </div>
          <ScanButton onClick={check} loading={loading} label="COMPUTE HASH" />
        </div>
      </Panel>

      {loading && <LoadingPanel label="Computing hash..." />}
      {error && <ErrorPanel message={error} />}

      {result && (
        <Panel title="HASH RESULTS">
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <StatRow label="File" value={result.file} />
            <StatRow label="SHA256" value={result.sha256} mono />
            <StatRow label="MD5" value={result.md5} mono />
            <StatRow label="Size" value={`${result.size_bytes.toLocaleString()} bytes`} />
            {result.verified !== null && (
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                marginTop: "8px",
                padding: "8px 12px",
                border: `1px solid ${result.verified ? "var(--success)" : "var(--danger)"}`,
                borderRadius: "2px",
                background: "var(--bg-secondary)",
              }}>
                {result.verified
                  ? <CheckCircle size={14} color="var(--success)" />
                  : <AlertTriangle size={14} color="var(--danger)" />
                }
                <span style={{
                  fontFamily: "Rajdhani, sans-serif",
                  fontWeight: 600,
                  fontSize: "13px",
                  letterSpacing: "0.1em",
                  color: result.verified ? "var(--success)" : "var(--danger)",
                }}>
                  {result.verified ? "HASH VERIFIED — FILE INTEGRITY CONFIRMED" : "HASH MISMATCH — FILE MAY BE TAMPERED"}
                </span>
              </div>
            )}
          </div>
        </Panel>
      )}
    </div>
  )
}

function PcapPanel() {
  const [filePath, setFilePath] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const analyze = async () => {
    if (!filePath.trim()) return
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const res = await api.post(`${FORENSICS_API}/analyze/pcap`, {
        pcap_path: filePath,
        max_packets: 1000
      })
      setResult(res.data)
      pushContext({ tab: 'Forensics', operation: 'PCAP Analysis', summary: `PCAP analysis complete: ${filePath}. ${res.data.summary || ''}`.trim(), detail: null })
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <Panel title="PCAP FILE ANALYSIS">
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div>
            <FieldLabel>PCAP FILE PATH</FieldLabel>
            <input
              value={filePath}
              onChange={e => setFilePath(e.target.value)}
              placeholder="/tmp/capture.pcap"
              style={{ ...inputStyle, width: "100%" }}
            />
          </div>
          <ScanButton onClick={analyze} loading={loading} label="ANALYZE PCAP" />
        </div>
      </Panel>

      {loading && <LoadingPanel label="Analyzing pcap with tshark..." />}
      {error && <ErrorPanel message={error} />}

      {result && (
        <>
          <Panel title="CAPTURE SUMMARY">
            <StatRow label="Total Packets" value={result.total_packets} />
            <StatRow label="Source IPs" value={result.unique_src_ips.length} />
            <StatRow label="Dest IPs" value={result.unique_dst_ips.length} />
            <StatRow label="Summary" value={result.summary} />
          </Panel>

          {result.suspicious?.length > 0 && (
            <Panel title={`SUSPICIOUS CONNECTIONS (${result.suspicious.length})`}>
              {result.suspicious.map((s, i) => (
                <div key={i} style={{
                  padding: "8px 12px",
                  borderLeft: "2px solid var(--danger)",
                  background: "var(--bg-secondary)",
                  marginBottom: "6px",
                  borderRadius: "0 2px 2px 0",
                }}>
                  <div style={{
                    fontFamily: "JetBrains Mono, monospace",
                    fontSize: "11px",
                    color: "var(--text-secondary)",
                  }}>{s.connection}</div>
                  <div style={{
                    fontFamily: "Rajdhani, sans-serif",
                    fontSize: "10px",
                    color: "var(--danger)",
                    letterSpacing: "0.1em",
                  }}>{s.reason} — {s.packet_count} packets</div>
                </div>
              ))}
            </Panel>
          )}

          {Object.keys(result.iocs || {}).length > 0 && (
            <Panel title="EXTRACTED IOCs">
              {Object.entries(result.iocs).map(([type, values]) => (
                <div key={type} style={{ marginBottom: "10px" }}>
                  <div style={{
                    fontFamily: "Rajdhani, sans-serif",
                    fontWeight: 600,
                    fontSize: "10px",
                    letterSpacing: "0.15em",
                    color: "var(--accent-gold)",
                    marginBottom: "4px",
                  }}>{type.toUpperCase()}</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                    {values.map((v, i) => (
                      <span key={i} style={{
                        fontFamily: "JetBrains Mono, monospace",
                        fontSize: "10px",
                        color: "var(--text-secondary)",
                        background: "var(--bg-secondary)",
                        border: "1px solid var(--border)",
                        padding: "2px 8px",
                        borderRadius: "2px",
                      }}>{v}</span>
                    ))}
                  </div>
                </div>
              ))}
            </Panel>
          )}

          {result.analysis && (
            <Panel title="REDSAGE FORENSIC ANALYSIS">
              <div style={{
                fontFamily: "Outfit, sans-serif",
                fontSize: "13px",
                lineHeight: "1.7",
                color: "var(--text-primary)",
                whiteSpace: "pre-wrap",
              }}>{result.analysis}</div>
            </Panel>
          )}
        </>
      )}
    </div>
  )
}

// ── Shared Components ─────────────────────────────────────────────

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

function Panel({ title, children }) {
  return (
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
        fontFamily: "Rajdhani, sans-serif",
        fontWeight: 600,
        fontSize: "11px",
        letterSpacing: "0.15em",
        color: "var(--text-dim)",
      }}>{title}</div>
      <div style={{ padding: "14px" }}>{children}</div>
    </div>
  )
}

function FieldLabel({ children }) {
  return (
    <div style={{
      fontFamily: "JetBrains Mono, monospace",
      fontSize: "9px",
      letterSpacing: "0.15em",
      color: "var(--text-dim)",
      marginBottom: "6px",
    }}>{children}</div>
  )
}

function StatRow({ label, value, mono }) {
  return (
    <div style={{
      display: "flex",
      gap: "12px",
      padding: "4px 0",
      borderBottom: "1px solid var(--border)",
    }}>
      <span style={{
        fontFamily: "JetBrains Mono, monospace",
        fontSize: "10px",
        color: "var(--text-dim)",
        minWidth: "80px",
      }}>{label}</span>
      <span style={{
        fontFamily: mono ? "JetBrains Mono, monospace" : "Outfit, sans-serif",
        fontSize: mono ? "10px" : "12px",
        color: "var(--text-secondary)",
        wordBreak: "break-all",
      }}>{value}</span>
    </div>
  )
}

function ScanButton({ onClick, loading, label }) {
  return (
    <button onClick={onClick} disabled={loading} style={{
      display: "flex",
      alignItems: "center",
      gap: "8px",
      padding: "8px 16px",
      background: loading ? "var(--bg-elevated)" : "var(--accent-gold-glow)",
      border: `1px solid ${loading ? "var(--border)" : "var(--accent-gold-dim)"}`,
      borderRadius: "2px",
      color: loading ? "var(--text-dim)" : "var(--accent-gold)",
      fontFamily: "Rajdhani, sans-serif",
      fontWeight: 600,
      fontSize: "12px",
      letterSpacing: "0.15em",
      cursor: loading ? "not-allowed" : "pointer",
      transition: "all 0.2s",
    }}>
      <ChevronRight size={14} />
      {loading ? "ANALYZING..." : label}
    </button>
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

function ErrorPanel({ message }) {
  return (
    <div style={{
      padding: "14px",
      border: "1px solid var(--danger)",
      borderRadius: "4px",
      background: "rgba(232, 64, 64, 0.05)",
      display: "flex",
      alignItems: "flex-start",
      gap: "10px",
    }}>
      <AlertTriangle size={14} color="var(--danger)" style={{ marginTop: "2px", flexShrink: 0 }} />
      <span style={{
        fontFamily: "JetBrains Mono, monospace",
        fontSize: "11px",
        color: "var(--danger)",
      }}>{message}</span>
    </div>
  )
}

const inputStyle = {
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: "2px",
  color: "var(--text-primary)",
  fontFamily: "JetBrains Mono, monospace",
  fontSize: "12px",
  padding: "8px 10px",
  outline: "none",
}
