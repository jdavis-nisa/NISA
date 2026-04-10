const MON_API = "http://localhost:8099"
function MonitoringPanel() {
  const [status, setStatus] = useState(null)
  const [config, setConfig] = useState({ interval_minutes: 15, scan_type: "quick", use_asset_inventory: true, targets: [] })
  const [deltas, setDeltas] = useState([])
  const [loading, setLoading] = useState(false)
  const [toggling, setToggling] = useState(false)
  const [newTarget, setNewTarget] = useState("")
  useEffect(() => { fetchAll() }, [])
  const fetchAll = async () => {
    try { const sr = await api.get(MON_API + "/monitoring/status"); setStatus(sr.data); setConfig(p => ({ ...p, interval_minutes: sr.data.interval_minutes, scan_type: sr.data.scan_type, use_asset_inventory: sr.data.use_asset_inventory })) } catch(e) {}
    try { const dr = await api.get(MON_API + "/monitoring/deltas"); setDeltas(dr.data.deltas || []) } catch(e) {}
  }
  const toggle = async () => { setToggling(true); try { if (status && status.enabled) { await api.post(MON_API + "/monitoring/stop") } else { await api.put(MON_API + "/monitoring/config", config); await api.post(MON_API + "/monitoring/start") }; await fetchAll() } catch(e) {}; setToggling(false) }
  const runNow = async () => { setLoading(true); try { await api.put(MON_API + "/monitoring/config", config); await api.post(MON_API + "/monitoring/run_now"); await fetchAll() } catch(e) {}; setLoading(false) }
  const ackAll = async () => { try { await api.post(MON_API + "/monitoring/deltas/acknowledge"); await fetchAll() } catch(e) {} }
  const addTarget = () => { const t = newTarget.trim(); if (!t) return; setConfig(p => ({ ...p, targets: [...(p.targets||[]), t] })); setNewTarget("") }
  const removeTarget = (t) => setConfig(p => ({ ...p, targets: p.targets.filter(x => x !== t) }))
  const sc = (s) => ({ critical: "var(--danger)", high: "#f59e0b", medium: "var(--accent-cyan, #00d4ff)", info: "var(--text-dim)" })[s] || "var(--text-dim)"
  const isEnabled = status && status.enabled
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <Panel title="CONTINUOUS MONITORING">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
          <div>
            <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "13px", color: "var(--text-secondary)", marginBottom: "4px" }}>{isEnabled ? "Monitoring active" : "Monitoring disabled"}</div>
            {status && status.last_run && <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)" }}>Last: {new Date(status.last_run).toLocaleString()}</div>}
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button onClick={runNow} disabled={loading} style={{ background: "transparent", border: "1px solid var(--border)", color: "var(--text-dim)", borderRadius: "3px", padding: "6px 12px", cursor: "pointer", fontFamily: "JetBrains Mono, monospace", fontSize: "10px", display: "flex", alignItems: "center", gap: "5px" }}><RefreshCw size={11} /> RUN NOW</button>
            <button onClick={toggle} disabled={toggling} style={{ background: isEnabled ? "rgba(239,68,68,0.1)" : "rgba(34,197,94,0.1)", border: isEnabled ? "1px solid var(--danger)" : "1px solid var(--success)", color: isEnabled ? "var(--danger)" : "var(--success)", borderRadius: "3px", padding: "8px 20px", cursor: "pointer", fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "14px", letterSpacing: "0.1em", display: "flex", alignItems: "center", gap: "8px" }}>{isEnabled ? "STOP" : "START"}</button>
          </div>
        </div>
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", padding: "12px", background: "var(--bg-primary)", borderRadius: "3px", border: "1px solid var(--border)" }}>
          <div><FieldLabel>INTERVAL</FieldLabel><select value={config.interval_minutes} onChange={e => setConfig({...config, interval_minutes: parseInt(e.target.value)})} style={inputStyle}>{[5,15,30,60].map(m => <option key={m} value={m}>{m} min</option>)}</select></div>
          <div><FieldLabel>SCAN TYPE</FieldLabel><select value={config.scan_type} onChange={e => setConfig({...config, scan_type: e.target.value})} style={inputStyle}>{["quick","standard","full"].map(s => <option key={s} value={s}>{s}</option>)}</select></div>
          <div><FieldLabel>USE ASSET INVENTORY</FieldLabel><button onClick={() => setConfig({...config, use_asset_inventory: !config.use_asset_inventory})} style={{ background: config.use_asset_inventory ? "rgba(34,197,94,0.1)" : "transparent", border: config.use_asset_inventory ? "1px solid var(--success)" : "1px solid var(--border)", color: config.use_asset_inventory ? "var(--success)" : "var(--text-dim)", borderRadius: "3px", padding: "6px 12px", cursor: "pointer", fontFamily: "JetBrains Mono, monospace", fontSize: "10px" }}>{config.use_asset_inventory ? "YES" : "NO"}</button></div>
        </div>
        <div style={{ marginTop: "10px" }}>
          <FieldLabel>ADDITIONAL TARGETS</FieldLabel>
          <div style={{ display: "flex", gap: "8px", marginBottom: "6px" }}>
            <input value={newTarget} onChange={e => setNewTarget(e.target.value)} onKeyDown={e => { if (e.key === "Enter") addTarget() }} placeholder="e.g. 192.168.86.0/24" style={{ ...inputStyle, flex: 1 }} />
            <button onClick={addTarget} style={{ background: "var(--accent-gold)", border: "none", color: "var(--bg-primary)", borderRadius: "3px", padding: "6px 12px", cursor: "pointer", fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px" }}>ADD</button>
          </div>
          <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
            {(config.targets||[]).map(t => (<span key={t} style={{ background: "var(--bg-primary)", border: "1px solid var(--border)", borderRadius: "10px", padding: "2px 10px", fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "5px" }}>{t}<button onClick={() => removeTarget(t)} style={{ background: "none", border: "none", color: "var(--danger)", cursor: "pointer", padding: 0 }}>x</button></span>))}
          </div>
        </div>
      </Panel>
      <Panel title="CHANGE DETECTION">
        {deltas.length > 0 && <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "8px" }}><button onClick={ackAll} style={{ background: "transparent", border: "1px solid var(--border)", color: "var(--text-dim)", borderRadius: "3px", padding: "4px 10px", cursor: "pointer", fontFamily: "JetBrains Mono, monospace", fontSize: "9px", display: "flex", alignItems: "center", gap: "4px" }}><CheckCircle size={10} /> ACK ALL</button></div>}
        {deltas.length === 0 && <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-dim)", padding: "8px" }}>No changes detected. Run a scan to establish baseline.</div>}
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          {deltas.map(d => (<div key={d.id} style={{ padding: "10px 12px", borderRadius: "3px", opacity: d.acknowledged ? 0.4 : 1, background: sc(d.severity) + "11", border: "1px solid " + sc(d.severity) + "44", display: "flex", alignItems: "center", gap: "10px" }}><AlertTriangle size={13} color={sc(d.severity)} /><div style={{ flex: 1 }}><div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: sc(d.severity) }}>{d.detail}</div><div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", marginTop: "2px" }}>{new Date(d.scan_at).toLocaleString()}</div></div><span style={{ background: sc(d.severity) + "22", border: "1px solid " + sc(d.severity), borderRadius: "2px", padding: "1px 6px", fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: sc(d.severity), textTransform: "uppercase" }}>{d.severity}</span></div>))}
        </div>
      </Panel>
    </div>
  )
}