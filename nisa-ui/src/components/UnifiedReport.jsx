
import { useState, useEffect } from "react"

const API = "http://127.0.0.1:8101"
const NISA_KEY = "d551fd7e05134c52b84286c201f0f36d8ddeb5e0611ed771ba44d6a4264f39cf"

const api = {
  get: (url) => fetch(url, { headers: { "X-NISA-API-Key": NISA_KEY } }).then(r => r.json()),
  post: (url, body) => fetch(url, { method: "POST", headers: { "Content-Type": "application/json", "X-NISA-API-Key": NISA_KEY }, body: JSON.stringify(body) }).then(r => r.json()),
  del: (url) => fetch(url, { method: "DELETE", headers: { "X-NISA-API-Key": NISA_KEY } }).then(r => r.json()),
}

const SEVERITY_COLOR = { CRITICAL: "#ff2244", HIGH: "#f59e0b", MEDIUM: "#00d4ff", LOW: "#44ffaa", INFO: "#8899bb" }
const TAB_ICON = {
  SECURITY: "🛡", FORENSICS: "🔍", REMEDIATION: "🔧", "THREAT INTEL": "🎯",
  ADVERSARIAL: "⚔", PLAYBOOK: "▶", ASSETS: "🖥", WATCHLIST: "👁",
  METASPLOIT: "💀", SIGNAL: "📡", TOPOLOGY: "🗺", COMPLIANCE: "📋"
}

const STYLE = {
  panel: { background: "#0d1117", border: "1px solid #1e2a3a", borderRadius: 4, padding: 20, marginBottom: 16 },
  label: { fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: 11, letterSpacing: "0.15em", color: "#c9a84c", marginBottom: 8 },
  input: { width: "100%", background: "#080c14", border: "1px solid #1e2a3a", borderRadius: 4, padding: "8px 12px", fontFamily: "Outfit, sans-serif", fontSize: 13, color: "#e2e8f0", outline: "none" },
  btn: (color="#c9a84c") => ({ padding: "8px 18px", background: "transparent", border: `1px solid ${color}`, borderRadius: 4, cursor: "pointer", fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: 12, letterSpacing: "0.1em", color }),
  tag: (color) => ({ display: "inline-block", padding: "2px 8px", borderRadius: 3, border: `1px solid ${color}33`, background: `${color}11`, fontFamily: "JetBrains Mono, monospace", fontSize: 10, color, marginRight: 6 }),
}

function SectionCard({ section, onRemove, index, total, onMoveUp, onMoveDown }) {
  const [expanded, setExpanded] = useState(false)
  const sev = section.severity || "INFO"
  const icon = TAB_ICON[section.tab_name] || "📄"
  return (
    <div style={{ background: "#080c14", border: "1px solid #1e2a3a", borderRadius: 4, marginBottom: 8, overflow: "hidden" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", cursor: "pointer" }} onClick={() => setExpanded(e => !e)}>
        <span style={{ fontSize: 16 }}>{icon}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: 13, color: "#e2e8f0", letterSpacing: "0.05em" }}>{section.tab_name} — {section.operation_type}</div>
          <div style={{ fontFamily: "Outfit, sans-serif", fontSize: 11, color: "#8899bb", marginTop: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: 480 }}>{section.summary}</div>
        </div>
        <span style={STYLE.tag(SEVERITY_COLOR[sev])}>{sev}</span>
        <div style={{ display: "flex", gap: 4 }}>
          <button onClick={e => { e.stopPropagation(); onMoveUp() }} disabled={index === 0} style={{ ...STYLE.btn("#8899bb"), padding: "3px 7px", opacity: index === 0 ? 0.3 : 1 }}>▲</button>
          <button onClick={e => { e.stopPropagation(); onMoveDown() }} disabled={index === total - 1} style={{ ...STYLE.btn("#8899bb"), padding: "3px 7px", opacity: index === total - 1 ? 0.3 : 1 }}>▼</button>
          <button onClick={e => { e.stopPropagation(); onRemove() }} style={{ ...STYLE.btn("#ff4444"), padding: "3px 8px" }}>✕</button>
        </div>
      </div>
      {expanded && section.detail && (
        <div style={{ padding: "10px 14px", borderTop: "1px solid #1e2a3a", fontFamily: "Outfit, sans-serif", fontSize: 12, color: "#8899bb", lineHeight: 1.6, whiteSpace: "pre-wrap", maxHeight: 200, overflowY: "auto" }}>
          {section.detail}
        </div>
      )}
    </div>
  )
}

function ReportPreview({ report }) {
  const cls = report.classification || "UNCLASSIFIED"
  const clsColor = cls === "UNCLASSIFIED" ? "#44ffaa" : cls === "CUI" ? "#f59e0b" : "#ff2244"
  return (
    <div style={{ background: "#080c14", border: "1px solid #1e2a3a", borderRadius: 4, padding: 24, fontFamily: "Outfit, sans-serif" }}>
      <div style={{ textAlign: "center", borderBottom: "1px solid #1e2a3a", paddingBottom: 16, marginBottom: 20 }}>
        <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: 11, letterSpacing: "0.2em", color: clsColor, marginBottom: 8 }}>{cls}</div>
        <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: 22, color: "#c9a84c", letterSpacing: "0.1em" }}>{report.title}</div>
        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#8899bb", marginTop: 6 }}>
          Generated: {new Date(report.generated_at).toLocaleString()} · Sections: {report.section_count} · Report ID: {report.report_id}
        </div>
        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#44ffaa", marginTop: 4 }}>
          ML-DSA-65 (NIST FIPS 204) · {report.mldsa_signature_bytes} bytes · Report #{report.report_id}
        </div>
      </div>
      {report.sections.map((s, i) => (
        <div key={i} style={{ marginBottom: 20, paddingBottom: 20, borderBottom: i < report.sections.length - 1 ? "1px solid #1e2a3a" : "none" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
            <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: 14, color: "#c9a84c" }}>{i + 1}. {s.tab_name} — {s.operation_type}</span>
            <span style={STYLE.tag(SEVERITY_COLOR[s.severity] || SEVERITY_COLOR.INFO)}>{s.severity}</span>
            <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#8899bb", marginLeft: "auto" }}>{new Date(s.timestamp).toLocaleString()}</span>
          </div>
          <div style={{ fontSize: 13, color: "#e2e8f0", marginBottom: 6 }}>{s.summary}</div>
          {s.detail && <div style={{ fontSize: 12, color: "#8899bb", whiteSpace: "pre-wrap", lineHeight: 1.6, maxHeight: 150, overflowY: "auto" }}>{s.detail}</div>}
        </div>
      ))}
      <div style={{ textAlign: "center", marginTop: 20, paddingTop: 16, borderTop: "1px solid #1e2a3a", fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#8899bb" }}>
        NISA v0.4.0 · Network Intelligence Security Assistant · {cls} · {report.crypto} · Sig: {report.mldsa_signature?.slice(0, 24)}...
      </div>
    </div>
  )
}

export default function UnifiedReport() {
  const [sessionId] = useState(() => "session_" + Date.now())
  const [queue, setQueue] = useState([])
  const [title, setTitle] = useState("NISA Security Assessment Report")
  const [classification, setClassification] = useState("UNCLASSIFIED")
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState("builder")
  const [addForm, setAddForm] = useState({ tab_name: "SECURITY", operation_type: "", summary: "", detail: "", severity: "INFO" })
  const [adding, setAdding] = useState(false)

  const fetchQueue = async () => {
    const data = await api.get(`${API}/report/queue/${sessionId}`)
    setQueue(data.sections || [])
  }

  useEffect(() => { fetchQueue() }, [])

  useEffect(() => {
    const handler = (e) => {
      if (e.detail?.reportSection) {
        const s = e.detail.reportSection
        api.post(`${API}/report/queue`, { ...s, session_id: sessionId }).then(fetchQueue)
      }
    }
    window.addEventListener("nisa-add-to-report", handler)
    return () => window.removeEventListener("nisa-add-to-report", handler)
  }, [sessionId])

  const removeSection = async (id) => {
    await api.del(`${API}/report/queue/${id}`)
    fetchQueue()
  }

  const moveSection = (index, dir) => {
    const updated = [...queue]
    const target = index + dir
    if (target < 0 || target >= updated.length) return
    ;[updated[index], updated[target]] = [updated[target], updated[index]]
    setQueue(updated)
    api.post(`${API}/report/reorder?session_id=${sessionId}`, updated.map(s => s.id))
  }

  const addManual = async () => {
    if (!addForm.operation_type || !addForm.summary) { setError("Operation type and summary are required"); return }
    setAdding(true)
    await api.post(`${API}/report/queue`, { ...addForm, session_id: sessionId })
    setAddForm({ tab_name: "SECURITY", operation_type: "", summary: "", detail: "", severity: "INFO" })
    await fetchQueue()
    setAdding(false)
  }

  const buildReport = async () => {
    if (queue.length === 0) { setError("Add at least one section before generating"); return }
    if (!title.trim()) { setError("Report title is required"); return }
    setLoading(true)
    setError(null)
    try {
      const result = await api.post(`${API}/report/build`, { session_id: sessionId, title, classification })
      setReport(result)
      setActiveTab("preview")
    } catch (e) {
      setError("Failed to generate report")
    }
    setLoading(false)
  }

  const exportPDF = () => {
    if (!report) return
    const clsColor = report.classification === "UNCLASSIFIED" ? "#44ffaa" : report.classification === "CUI" ? "#f59e0b" : "#ff2244"
    const sectionsHTML = report.sections.map((s, idx) => `
      <div class="section">
        <div class="section-header">
          <span class="section-title">${idx+1}. ${s.tab_name} — ${s.operation_type}</span>
          <span class="severity" style="color:${SEVERITY_COLOR[s.severity]||"#8899bb"}">${s.severity}</span>
          <span class="timestamp">${new Date(s.timestamp).toLocaleString()}</span>
        </div>
        <div class="summary">${s.summary}</div>
        ${s.detail ? `<div class="detail">${s.detail}</div>` : ""}
      </div>`).join("")
    const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>${report.title}</title>
      <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=JetBrains+Mono:wght@400&family=Outfit:wght@400;500&display=swap" rel="stylesheet">
      <style>
        @media print {
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .no-print { display: none; }
        }
        body { background: #080c14; color: #e2e8f0; font-family: Outfit, sans-serif; max-width: 900px; margin: 40px auto; padding: 32px; }
        .cls-banner { text-align:center; font-family:Rajdhani,sans-serif; font-weight:700; font-size:13px; letter-spacing:0.2em; color:${clsColor}; margin-bottom:8px; }
        .title { text-align:center; font-family:Rajdhani,sans-serif; font-weight:700; font-size:26px; color:#c9a84c; letter-spacing:0.1em; margin:0 0 8px; }
        .meta { text-align:center; font-family:JetBrains Mono,monospace; font-size:10px; color:#8899bb; margin-bottom:4px; }
        .sig { text-align:center; font-family:JetBrains Mono,monospace; font-size:9px; color:#44ffaa; margin-bottom:24px; }
        hr { border:none; border-top:1px solid #1e2a3a; margin:24px 0; }
        .section { margin-bottom:24px; padding-bottom:24px; border-bottom:1px solid #1e2a3a; }
        .section-header { display:flex; align-items:center; gap:12px; margin-bottom:8px; flex-wrap:wrap; }
        .section-title { font-family:Rajdhani,sans-serif; font-weight:700; font-size:15px; color:#c9a84c; }
        .severity { font-family:JetBrains Mono,monospace; font-size:10px; font-weight:700; }
        .timestamp { font-family:JetBrains Mono,monospace; font-size:9px; color:#8899bb; margin-left:auto; }
        .summary { font-size:13px; color:#e2e8f0; margin-bottom:6px; }
        .detail { font-size:12px; color:#8899bb; white-space:pre-wrap; line-height:1.6; }
        .footer { text-align:center; margin-top:32px; padding-top:16px; border-top:1px solid #1e2a3a; font-family:JetBrains Mono,monospace; font-size:9px; color:#8899bb; }
      </style></head><body>
      <div class="cls-banner">${report.classification}</div>
      <h1 class="title">${report.title}</h1>
      <div class="meta">Generated: ${new Date(report.generated_at).toLocaleString()} &middot; Sections: ${report.section_count} &middot; Report ID: ${report.report_id}</div>
      <div class="sig">ML-DSA-65 (NIST FIPS 204) &middot; ${report.mldsa_signature_bytes} bytes &middot; Sig: ${report.mldsa_signature?.slice(0,32)}...</div>
      <hr/>
      ${sectionsHTML}
      <div class="footer">NISA v0.4.0 &middot; ${report.classification} &middot; ${report.crypto} &middot; Integrity: ${report.mldsa_signature?.slice(0,24)}...</div>
    </body></html>`
    const printWin = window.open("", "_blank")
    printWin.document.write(html)
    printWin.document.close()
    printWin.focus()
    setTimeout(() => { printWin.print() }, 800)
  }

  const exportHTML = () => {
    if (!report) return
    const clsColor = report.classification === "UNCLASSIFIED" ? "#44ffaa" : report.classification === "CUI" ? "#f59e0b" : "#ff2244"
    const sectionsHTML = report.sections.map((s, i) => `
      <div style="margin-bottom:24px;padding-bottom:24px;border-bottom:1px solid #1e2a3a;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
          <span style="font-family:Rajdhani,sans-serif;font-weight:700;font-size:15px;color:#c9a84c;">${i+1}. ${s.tab_name} — ${s.operation_type}</span>
          <span style="padding:2px 8px;border-radius:3px;font-family:JetBrains Mono,monospace;font-size:10px;color:${SEVERITY_COLOR[s.severity]||"#8899bb"}">${s.severity}</span>
        </div>
        <div style="font-size:13px;color:#e2e8f0;margin-bottom:6px;">${s.summary}</div>
        ${s.detail ? `<div style="font-size:12px;color:#8899bb;white-space:pre-wrap;line-height:1.6;">${s.detail}</div>` : ""}
      </div>`).join("")
    const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>${report.title}</title>
      <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=JetBrains+Mono:wght@400&family=Outfit:wght@400;500&display=swap" rel="stylesheet">
      <style>body{background:#080c14;color:#e2e8f0;font-family:Outfit,sans-serif;max-width:900px;margin:40px auto;padding:32px;}h1{font-family:Rajdhani,sans-serif;}</style>
      </head><body>
      <div style="text-align:center;border-bottom:1px solid #1e2a3a;padding-bottom:20px;margin-bottom:32px;">
        <div style="font-family:Rajdhani,sans-serif;font-weight:700;font-size:12px;letter-spacing:0.2em;color:${clsColor};margin-bottom:8px;">${report.classification}</div>
        <h1 style="color:#c9a84c;letter-spacing:0.1em;margin:0 0 8px;">${report.title}</h1>
        <div style="font-family:JetBrains Mono,monospace;font-size:10px;color:#8899bb;">Generated: ${new Date(report.generated_at).toLocaleString()} · Sections: ${report.section_count}</div>
        <div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#44ffaa;margin-top:4px;">ML-DSA-65 (NIST FIPS 204) · ${report.mldsa_signature_bytes} bytes · Report #${report.report_id}</div>
      </div>
      ${sectionsHTML}
      <div style="text-align:center;margin-top:32px;padding-top:16px;border-top:1px solid #1e2a3a;font-family:JetBrains Mono,monospace;font-size:9px;color:#8899bb;">
        NISA v0.4.0 · ${report.classification} · ${report.crypto} · Sig: ${report.mldsa_signature?.slice(0,24)}...
      </div></body></html>`
    const blob = new Blob([html], { type: "text/html" })
    const a = document.createElement("a")
    a.href = URL.createObjectURL(blob)
    a.download = `NISA_Report_${Date.now()}.html`
    a.click()
  }

  const TABS = [{ id: "builder", label: "REPORT BUILDER" }, { id: "add", label: "ADD SECTION" }, { id: "preview", label: "PREVIEW" }]

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: 22, color: "#c9a84c", letterSpacing: "0.15em" }}>UNIFIED REPORT GENERATOR</div>
          <div style={{ fontFamily: "Outfit, sans-serif", fontSize: 12, color: "#8899bb", marginTop: 4 }}>Assemble, sign, and export full-session security assessment reports</div>
        </div>
        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#44ffaa", background: "#44ffaa11", border: "1px solid #44ffaa33", borderRadius: 4, padding: "4px 10px" }}>
          {queue.length} SECTION{queue.length !== 1 ? "S" : ""} QUEUED
        </div>
      </div>

      <div style={{ display: "flex", gap: 4, marginBottom: 20 }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{ ...STYLE.btn(activeTab === t.id ? "#c9a84c" : "#8899bb"), background: activeTab === t.id ? "#c9a84c11" : "transparent" }}>{t.label}</button>
        ))}
      </div>

      {error && <div style={{ background: "#ff224411", border: "1px solid #ff224433", borderRadius: 4, padding: "10px 14px", fontFamily: "Outfit, sans-serif", fontSize: 12, color: "#ff6666", marginBottom: 16 }}>{error}</div>}

      {activeTab === "builder" && (
        <div>
          <div style={STYLE.panel}>
            <div style={STYLE.label}>REPORT CONFIGURATION</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 200px", gap: 12, marginBottom: 0 }}>
              <div>
                <div style={{ ...STYLE.label, fontSize: 10, marginBottom: 4 }}>REPORT TITLE</div>
                <input style={STYLE.input} value={title} onChange={e => setTitle(e.target.value)} placeholder="Enter report title..." />
              </div>
              <div>
                <div style={{ ...STYLE.label, fontSize: 10, marginBottom: 4 }}>CLASSIFICATION</div>
                <select style={{ ...STYLE.input, cursor: "pointer" }} value={classification} onChange={e => setClassification(e.target.value)}>
                  <option value="UNCLASSIFIED">UNCLASSIFIED</option>
                  <option value="CUI">CUI</option>
                  <option value="CONFIDENTIAL">CONFIDENTIAL</option>
                </select>
              </div>
            </div>
          </div>

          <div style={STYLE.panel}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
              <div style={STYLE.label}>REPORT SECTIONS ({queue.length})</div>
              <button onClick={() => setActiveTab("add")} style={STYLE.btn("#00d4ff")}>+ ADD SECTION</button>
            </div>
            {queue.length === 0 ? (
              <div style={{ textAlign: "center", padding: "32px 0", color: "#8899bb", fontFamily: "Outfit, sans-serif", fontSize: 13 }}>
                No sections yet. Use the <strong style={{ color: "#c9a84c" }}>ADD SECTION</strong> tab or click <strong style={{ color: "#c9a84c" }}>Add to Report</strong> on any operational tab.
              </div>
            ) : (
              queue.map((s, i) => (
                <SectionCard key={s.id} section={s} index={i} total={queue.length}
                  onRemove={() => removeSection(s.id)}
                  onMoveUp={() => moveSection(i, -1)}
                  onMoveDown={() => moveSection(i, 1)} />
              ))
            )}
          </div>

          <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
            <button onClick={() => { if(window.confirm("Clear all sections?")) api.del(`${API}/report/queue/session/${sessionId}`).then(fetchQueue) }} style={STYLE.btn("#ff4444")} disabled={queue.length === 0}>CLEAR ALL</button>
            <button onClick={buildReport} disabled={loading || queue.length === 0} style={{ ...STYLE.btn("#44ffaa"), background: loading ? "transparent" : "#44ffaa11" }}>
              {loading ? "GENERATING..." : "GENERATE REPORT"}
            </button>
          </div>
        </div>
      )}

      {activeTab === "add" && (
        <div style={STYLE.panel}>
          <div style={STYLE.label}>ADD SECTION MANUALLY</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 140px", gap: 12, marginBottom: 12 }}>
            <div>
              <div style={{ ...STYLE.label, fontSize: 10, marginBottom: 4 }}>SOURCE TAB</div>
              <select style={{ ...STYLE.input, cursor: "pointer" }} value={addForm.tab_name} onChange={e => setAddForm(p => ({ ...p, tab_name: e.target.value }))}>
                {["SECURITY","FORENSICS","REMEDIATION","THREAT INTEL","ADVERSARIAL","PLAYBOOK","ASSETS","WATCHLIST","METASPLOIT","SIGNAL","TOPOLOGY","COMPLIANCE"].map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <div style={{ ...STYLE.label, fontSize: 10, marginBottom: 4 }}>OPERATION TYPE</div>
              <input style={STYLE.input} value={addForm.operation_type} onChange={e => setAddForm(p => ({ ...p, operation_type: e.target.value }))} placeholder="e.g. Nmap Scan, CVE Lookup..." />
            </div>
            <div>
              <div style={{ ...STYLE.label, fontSize: 10, marginBottom: 4 }}>SEVERITY</div>
              <select style={{ ...STYLE.input, cursor: "pointer" }} value={addForm.severity} onChange={e => setAddForm(p => ({ ...p, severity: e.target.value }))}>
                {["INFO","LOW","MEDIUM","HIGH","CRITICAL"].map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>
          <div style={{ marginBottom: 12 }}>
            <div style={{ ...STYLE.label, fontSize: 10, marginBottom: 4 }}>SUMMARY</div>
            <input style={STYLE.input} value={addForm.summary} onChange={e => setAddForm(p => ({ ...p, summary: e.target.value }))} placeholder="Brief description of the operation and findings..." />
          </div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ ...STYLE.label, fontSize: 10, marginBottom: 4 }}>DETAIL (optional)</div>
            <textarea style={{ ...STYLE.input, minHeight: 100, resize: "vertical" }} value={addForm.detail} onChange={e => setAddForm(p => ({ ...p, detail: e.target.value }))} placeholder="Full output, findings, or notes..." />
          </div>
          <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
            <button onClick={() => setActiveTab("builder")} style={STYLE.btn("#8899bb")}>CANCEL</button>
            <button onClick={addManual} disabled={adding} style={{ ...STYLE.btn("#44ffaa"), background: "#44ffaa11" }}>{adding ? "ADDING..." : "ADD TO REPORT"}</button>
          </div>
        </div>
      )}

      {activeTab === "preview" && (
        <div>
          {!report ? (
            <div style={{ textAlign: "center", padding: "48px 0", color: "#8899bb", fontFamily: "Outfit, sans-serif", fontSize: 13 }}>
              No report generated yet. Go to <strong style={{ color: "#c9a84c" }}>REPORT BUILDER</strong> and click <strong style={{ color: "#44ffaa" }}>GENERATE REPORT</strong>.
            </div>
          ) : (
            <div>
              <div style={{ display: "flex", gap: 12, justifyContent: "flex-end", marginBottom: 16 }}>
                <button onClick={exportHTML} style={{ ...STYLE.btn("#c9a84c"), background: "#c9a84c11" }}>⬇ EXPORT HTML</button>
                <button onClick={exportPDF} style={{ ...STYLE.btn("#00d4ff"), background: "#00d4ff11" }}>⬇ EXPORT PDF</button>
              </div>
              <ReportPreview report={report} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
