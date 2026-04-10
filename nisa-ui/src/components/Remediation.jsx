import { useState, useEffect } from "react"
import { pushContext } from "../SessionContext"
import { useLocation } from "react-router-dom"
import { Shield, CheckCircle, AlertTriangle, Lock, Play, ChevronRight, Download } from "lucide-react"
import api, { NISA_API_KEY } from "../api"
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter"
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism"

const REM_API = "http://localhost:8086"

const panelStyle = {
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: "4px",
  padding: "16px",
  marginBottom: "16px",
}

const labelStyle = {
  fontFamily: "Rajdhani, sans-serif",
  fontWeight: 600,
  fontSize: "10px",
  letterSpacing: "0.15em",
  color: "var(--text-dim)",
  marginBottom: "6px",
  display: "block",
}

const inputStyle = {
  width: "100%",
  background: "var(--bg-primary)",
  border: "1px solid var(--border)",
  borderRadius: "2px",
  padding: "8px 10px",
  color: "var(--text-primary)",
  fontFamily: "JetBrains Mono, monospace",
  fontSize: "12px",
  outline: "none",
  boxSizing: "border-box",
}

const btnStyle = (color = "var(--accent-gold)") => ({
  padding: "10px 20px",
  background: "transparent",
  border: `1px solid ${color}`,
  borderRadius: "2px",
  color: color,
  fontFamily: "Rajdhani, sans-serif",
  fontWeight: 700,
  fontSize: "11px",
  letterSpacing: "0.15em",
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  gap: "6px",
})

export default function Remediation() {
  const [step, setStep] = useState("authorize")
  const location = useLocation()
  const [session, setSession] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [applyFile, setApplyFile] = useState("")
  const [applyResult, setApplyResult] = useState(null)
  const [applying, setApplying] = useState(false)

  const applyPatch = async () => {
    if (!applyFile.trim()) return
    setApplying(true)
    try {
      const res = await api.post(`${REM_API}/apply`, {
        session_id: session.session_id,
        remediation_id: result.remediation_id,
        target_file: applyFile,
        backup: true
      })
      setApplyResult(res.data)
    } catch (e) {
      setApplyResult({ error: e.response?.data?.detail || e.message })
    }
    setApplying(false)
  }

  const [authForm, setAuthForm] = useState({
    target: "",
    scope: "",
    authorized_by: "",
    authorization_date: new Date().toISOString().split("T")[0],
    engagement_type: "vulnerability_assessment"
  })

  useEffect(() => {
    const prefill = location?.state?.prefill
    if (prefill) {
      setVulnForm(prev => ({
        ...prev,
        vulnerability: prefill.vulnerability || prev.vulnerability,
        affected_component: prefill.component || prev.affected_component,
        language: prefill.language || prev.language
      }))
      // Pre-populate the auth form target from topology scan
      if (prefill.component) {
        const ip = prefill.component.split(':')[0]
        setAuthForm(prev => ({
          ...prev,
          target: ip,
          scope: prefill.vulnerability || prev.scope
        }))
      }
    }
  }, [])

  const [vulnForm, setVulnForm] = useState({
    vulnerability: "",
    affected_component: "",
    language: "python"
  })

  const authorize = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.post(`${REM_API}/authorize`, authForm)
      setSession(res.data)
      setStep("remediate")
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  const remediate = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await api.post(`${REM_API}/remediate`, {
        session_id: session.session_id,
        ...vulnForm
      })
      setResult(res.data)
      setStep("results")
      pushContext({ tab: 'Remediation', operation: 'Patch Generation', summary: `Patch generated for ${vulnForm.language || 'unknown'} - ${res.data.test_status || 'complete'}. ${res.data.summary || ''}`.trim(), detail: null })
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  const reset = () => {
    setStep("authorize")
    setSession(null)
    setResult(null)
    setError(null)
    setVulnForm({ vulnerability: "", affected_component: "", language: "python" })
  }

  const sevColor = { CRITICAL: "var(--danger)", HIGH: "#ff6b35", MEDIUM: "var(--warning)", LOW: "var(--accent-cyan)" }

  return (
    <div className="fade-in" style={{ maxWidth: "900px", margin: "0 auto" }}>
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
          <Shield size={20} color="var(--accent-gold)" />
          <h1 style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "24px", letterSpacing: "0.2em", color: "var(--text-primary)", margin: 0 }}>
            REMEDIATION
          </h1>
        </div>
        <p style={{ fontFamily: "Outfit, sans-serif", fontSize: "13px", color: "var(--text-dim)", margin: 0 }}>
          Autonomous vulnerability analysis, patch generation, and sandbox testing
        </p>
      </div>

      {/* Step indicators */}
      <div style={{ display: "flex", gap: "8px", marginBottom: "24px" }}>
        {[
          { id: "authorize", label: "01 AUTHORIZE" },
          { id: "remediate", label: "02 ANALYZE" },
          { id: "results", label: "03 RESULTS" }
        ].map(s => (
          <div key={s.id} style={{
            padding: "6px 14px",
            border: `1px solid ${step === s.id ? "var(--accent-gold)" : "var(--border)"}`,
            borderRadius: "2px",
            fontFamily: "Rajdhani, sans-serif",
            fontWeight: 600,
            fontSize: "10px",
            letterSpacing: "0.15em",
            color: step === s.id ? "var(--accent-gold)" : "var(--text-dim)",
          }}>{s.label}</div>
        ))}
      </div>

      {error && (
        <div style={{ ...panelStyle, borderColor: "var(--danger)", marginBottom: "16px" }}>
          <span style={{ color: "var(--danger)", fontFamily: "JetBrains Mono, monospace", fontSize: "12px" }}>{error}</span>
        </div>
      )}

      {step === "authorize" && (
        <div style={panelStyle}>
          <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px", letterSpacing: "0.15em", color: "var(--accent-gold)", marginBottom: "16px", display: "flex", alignItems: "center", gap: "6px" }}>
            <Lock size={12} /> AUTHORIZATION REQUIRED
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "16px" }}>
            {[
              { key: "target", label: "TARGET (IP/DOMAIN)" },
              { key: "authorized_by", label: "AUTHORIZED BY" },
              { key: "authorization_date", label: "AUTHORIZATION DATE", type: "date" },
              { key: "engagement_type", label: "ENGAGEMENT TYPE" },
            ].map(f => (
              <div key={f.key}>
                <label style={labelStyle}>{f.label}</label>
                <input
                  type={f.type || "text"}
                  value={authForm[f.key]}
                  onChange={e => setAuthForm(p => ({ ...p, [f.key]: e.target.value }))}
                  style={inputStyle}
                />
              </div>
            ))}
          </div>
          <div style={{ marginBottom: "16px" }}>
            <label style={labelStyle}>SCOPE OF ENGAGEMENT</label>
            <textarea
              value={authForm.scope}
              onChange={e => setAuthForm(p => ({ ...p, scope: e.target.value }))}
              placeholder="Describe the authorized scope of this security assessment..."
              style={{ ...inputStyle, height: "80px", resize: "vertical" }}
            />
          </div>
          <button onClick={authorize} disabled={loading || !authForm.target || !authForm.authorized_by} style={btnStyle()}>
            <Lock size={12} />
            {loading ? "AUTHORIZING..." : "AUTHORIZE ENGAGEMENT"}
          </button>
        </div>
      )}

      {step === "remediate" && session && (
        <div>
          <div style={{ ...panelStyle, borderColor: "var(--success)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
              <CheckCircle size={12} color="var(--success)" />
              <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "11px", letterSpacing: "0.15em", color: "var(--success)" }}>SESSION AUTHORIZED</span>
            </div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)" }}>
              Target: {session.target} | Token: {session.authorization_token} | By: {session.message?.split("by ")[1]}
            </div>
          </div>

          <div style={panelStyle}>
            <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px", letterSpacing: "0.15em", color: "var(--accent-gold)", marginBottom: "16px" }}>
              VULNERABILITY DETAILS
            </div>
            <div style={{ marginBottom: "12px" }}>
              <label style={labelStyle}>VULNERABILITY DESCRIPTION</label>
              <textarea
                value={vulnForm.vulnerability}
                onChange={e => setVulnForm(p => ({ ...p, vulnerability: e.target.value }))}
                placeholder="Describe the vulnerability in detail..."
                style={{ ...inputStyle, height: "100px", resize: "vertical" }}
              />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "16px" }}>
              <div>
                <label style={labelStyle}>AFFECTED COMPONENT</label>
                <input value={vulnForm.affected_component} onChange={e => setVulnForm(p => ({ ...p, affected_component: e.target.value }))} style={inputStyle} placeholder="file.py - function_name" />
              </div>
              <div>
                <label style={labelStyle}>LANGUAGE</label>
                <select value={vulnForm.language} onChange={e => setVulnForm(p => ({ ...p, language: e.target.value }))} style={{ ...inputStyle, cursor: "pointer" }}>
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                  <option value="typescript">TypeScript</option>
                  <option value="java">Java</option>
                  <option value="bash">Bash</option>
                  <option value="powershell">PowerShell</option>
                  <option value="go">Go</option>
                  <option value="rust">Rust</option>
                  <option value="cpp">C/C++</option>
                  <option value="ruby">Ruby</option>
                  <option value="php">PHP</option>
                  <option value="sql">SQL</option>
                  <option value="matlab">MATLAB</option>
                  <option value="r">R</option>
                </select>
              </div>
            </div>
            <button onClick={remediate} disabled={loading || !vulnForm.vulnerability} style={btnStyle()}>
              <Play size={12} />
              {loading ? "ANALYZING & PATCHING..." : "GENERATE PATCH & TEST"}
            </button>
          </div>
        </div>
      )}

      {step === "results" && result && (
        <div>
          <div style={{ ...panelStyle, borderColor: sevColor[result.severity] || "var(--border)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                {result.sandbox_passed ? <CheckCircle size={14} color="var(--success)" /> : <AlertTriangle size={14} color="var(--danger)" />}
                <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "13px", letterSpacing: "0.1em", color: result.sandbox_passed ? "var(--success)" : "var(--danger)" }}>
                  {result.sandbox_passed ? "SANDBOX PASSED — PATCH VERIFIED" : "SANDBOX FAILED — PATCH NEEDS REVIEW"}
                </span>
              </div>
              <div style={{ display: "flex", gap: "8px" }}>
                <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: sevColor[result.severity], border: `1px solid ${sevColor[result.severity]}`, padding: "2px 8px", borderRadius: "2px" }}>
                  {result.severity}
                </span>
                <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)", border: "1px solid var(--border)", padding: "2px 8px", borderRadius: "2px" }}>
                  CVSS {result.cvss_score}
                </span>
              </div>
            </div>
            <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6" }}>
              {result.explanation}
            </div>
          </div>

          <div style={panelStyle}>
            <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "11px", letterSpacing: "0.15em", color: "var(--accent-gold)", marginBottom: "12px" }}>PATCH CODE</div>
            <SyntaxHighlighter language={result.affected_component?.includes(".py") ? "python" : "text"} style={vscDarkPlus} customStyle={{ borderRadius: "4px", fontSize: "12px" }}>
              {result.patch_code || "No patch generated"}
            </SyntaxHighlighter>
          </div>

          {result.implementation_steps?.length > 0 && (
            <div style={panelStyle}>
              <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "11px", letterSpacing: "0.15em", color: "var(--accent-gold)", marginBottom: "12px" }}>IMPLEMENTATION STEPS</div>
              {result.implementation_steps.map((step, i) => (
                <div key={i} style={{ display: "flex", gap: "10px", marginBottom: "8px" }}>
                  <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--accent-gold)", minWidth: "24px" }}>0{i+1}</span>
                  <span style={{ fontFamily: "Outfit, sans-serif", fontSize: "13px", color: "var(--text-secondary)" }}>{step}</span>
                </div>
              ))}
            </div>
          )}

          {result.references?.length > 0 && (
            <div style={panelStyle}>
              <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "11px", letterSpacing: "0.15em", color: "var(--accent-gold)", marginBottom: "8px" }}>REFERENCES</div>
              {result.references.map((ref, i) => (
                <div key={i} style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: "var(--accent-cyan)", marginBottom: "4px" }}>{ref}</div>
              ))}
            </div>
          )}

          {result.sandbox_passed && (
            <div style={panelStyle}>
              <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "11px", letterSpacing: "0.15em", color: "var(--warning)", marginBottom: "12px" }}>
                ⚠ APPLY PATCH TO FILE (OPTIONAL)
              </div>
              <div style={{ marginBottom: "10px" }}>
                <label style={labelStyle}>TARGET FILE PATH</label>
                <input value={applyFile} onChange={e => setApplyFile(e.target.value)}
                  placeholder="/path/to/your/login.py"
                  style={inputStyle} />
              </div>
              <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "11px", color: "var(--text-dim)", marginBottom: "10px" }}>
                A backup will be created automatically before applying the patch.
              </div>
              <button onClick={applyPatch} disabled={applying || !applyFile.trim()} style={btnStyle("var(--warning)")}>
                <Play size={12} /> {applying ? "APPLYING..." : "APPLY PATCH TO FILE"}
              </button>
              {applyResult && (
                <div style={{ marginTop: "10px", padding: "10px", background: "var(--bg-primary)", border: `1px solid ${applyResult.error ? "var(--danger)" : "var(--success)"}`, borderRadius: "2px" }}>
                  <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: applyResult.error ? "var(--danger)" : "var(--success)" }}>
                    {applyResult.error || applyResult.message}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* SSH Remote Patch Panel */}
          <SSHPatchPanel session={session} result={result} />

          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <button onClick={async () => {
              try {
                const url = `${REM_API}/report/${session.session_id}/${result.remediation_id}`
                const res = await fetch(url, {
                  headers: { "X-NISA-API-Key": NISA_API_KEY }
                })
                if (!res.ok) throw new Error(`HTTP ${res.status}`)
                const blob = await res.blob()
                const a = document.createElement("a")
                a.href = URL.createObjectURL(blob)
                a.download = `NISA_Remediation_Report_${result.remediation_id}.pdf`
                a.click()
                URL.revokeObjectURL(a.href)
              } catch(e) {
                alert("PDF download failed: " + e.message)
              }
            }} style={btnStyle("var(--success)")}>
              <Download size={12} /> DOWNLOAD PDF REPORT
            </button>
            <button onClick={() => setStep("remediate")} style={btnStyle("var(--accent-cyan)")}>
              <ChevronRight size={12} /> NEW VULNERABILITY
            </button>
            <button onClick={reset} style={btnStyle("var(--text-dim)")}>
              NEW SESSION
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function SSHPatchPanel({ session, result }) {
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ host: "", port: "22", username: "", password: "", key_path: "", remote_file_path: "" })
  const [authMethod, setAuthMethod] = useState("password")
  const [loading, setLoading] = useState(false)
  const [patchResult, setPatchResult] = useState(null)
  const [error, setError] = useState("")

  const run = async () => {
    setLoading(true)
    setError("")
    setPatchResult(null)
    try {
      const payload = {
        session_id: session.session_id,
        remediation_id: result.remediation_id,
        host: form.host,
        port: parseInt(form.port) || 22,
        username: form.username,
        remote_file_path: form.remote_file_path,
      }
      if (authMethod === "password") payload.password = form.password
      else payload.key_path = form.key_path
      const res = await api.post(`${REM_API}/ssh/patch`, payload)
      setPatchResult(res.data)
    } catch(e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  const fl = (label, key, placeholder, type="text") => (
    <div style={{ flex: 1, minWidth: "140px" }}>
      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", letterSpacing: "0.1em", marginBottom: "3px" }}>{label}</div>
      <input type={type} value={form[key]} onChange={e => setForm({...form, [key]: e.target.value})}
        placeholder={placeholder}
        style={{ width: "100%", background: "var(--bg-primary)", border: "1px solid var(--border)", borderRadius: "3px",
          color: "var(--text-primary)", fontFamily: "JetBrains Mono, monospace", fontSize: "11px",
          padding: "6px 8px", outline: "none", boxSizing: "border-box" }} />
    </div>
  )

  return (
    <div style={{ border: "1px solid var(--border)", borderRadius: "4px", marginBottom: "12px", overflow: "hidden" }}>
      <button onClick={() => setOpen(o => !o)} style={{
        width: "100%", background: "var(--bg-secondary)", border: "none", borderBottom: open ? "1px solid var(--border)" : "none",
        color: "var(--text-secondary)", cursor: "pointer", padding: "10px 14px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px", letterSpacing: "0.15em"
      }}>
        <span>SSH REMOTE PATCH (OPTIONAL)</span>
        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)" }}>{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div style={{ padding: "14px", background: "var(--bg-primary)", display: "flex", flexDirection: "column", gap: "10px" }}>
          <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "11px", color: "var(--text-dim)", lineHeight: 1.5 }}>
            Apply this patch directly to a remote host over SSH. Credentials are never stored. A backup is created automatically before any change.
          </div>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {fl("HOST / IP", "host", "192.168.86.25")}
            {fl("SSH PORT", "port", "22")}
            {fl("USERNAME", "username", "admin")}
          </div>
          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", letterSpacing: "0.1em" }}>AUTH METHOD</div>
            {["password", "key"].map(m => (
              <button key={m} onClick={() => setAuthMethod(m)} style={{
                background: authMethod === m ? "var(--accent-gold-glow)" : "transparent",
                border: `1px solid ${authMethod === m ? "var(--accent-gold)" : "var(--border)"}`,
                color: authMethod === m ? "var(--accent-gold)" : "var(--text-dim)",
                borderRadius: "3px", padding: "3px 10px", cursor: "pointer",
                fontFamily: "JetBrains Mono, monospace", fontSize: "10px", textTransform: "uppercase"
              }}>{m}</button>
            ))}
          </div>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {authMethod === "password"
              ? fl("PASSWORD", "password", "••••••••", "password")
              : fl("KEY FILE PATH", "key_path", "/Users/you/.ssh/id_rsa")}
            {fl("REMOTE FILE PATH", "remote_file_path", "/etc/app/config.py")}
          </div>
          {error && <div style={{ color: "var(--danger)", fontFamily: "JetBrains Mono, monospace", fontSize: "11px" }}>{error}</div>}
          {patchResult && (
            <div style={{ background: "rgba(34,197,94,0.08)", border: "1px solid var(--success)", borderRadius: "3px", padding: "10px 12px" }}>
              <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px", color: "var(--success)", letterSpacing: "0.1em", marginBottom: "4px" }}>
                PATCH APPLIED SUCCESSFULLY
              </div>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                Host: {patchResult.host}<br />
                File: {patchResult.remote_file}<br />
                Backup: {patchResult.backup_path}<br />
                Verified: {patchResult.verified ? "Yes" : "No"}<br />
                Bytes written: {patchResult.bytes_written}
              </div>
            </div>
          )}
          <button onClick={run} disabled={loading || !form.host || !form.username || !form.remote_file_path} style={{
            background: loading ? "transparent" : "var(--accent-gold)",
            border: "1px solid var(--accent-gold)",
            color: loading ? "var(--accent-gold)" : "var(--bg-primary)",
            borderRadius: "3px", padding: "8px 18px", cursor: loading ? "not-allowed" : "pointer",
            fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "13px", letterSpacing: "0.1em",
            alignSelf: "flex-start"
          }}>{loading ? "CONNECTING..." : "APPLY PATCH VIA SSH"}</button>
        </div>
      )}
    </div>
  )
}
