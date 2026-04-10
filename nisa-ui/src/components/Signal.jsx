import { useState } from "react"
import { pushContext } from "../SessionContext"
import api from "../api"

const API = "http://localhost:8088"

const GOLD = "var(--accent-gold)"
const DIM = "var(--text-dim)"
const SEC = "var(--text-secondary)"
const BORDER = "var(--border)"
const BG2 = "var(--bg-secondary)"
const BG3 = "var(--bg-tertiary)"

export default function Signal() {
  const [activeTab, setActiveTab] = useState("waveform")

  const tabs = [
    { id: "waveform", label: "WAVEFORM" },
    { id: "fft", label: "FFT ANALYSIS" },
    { id: "library", label: "WAVEFORM LIBRARY" },
    { id: "rdmap", label: "RANGE-DOPPLER" },
    { id: "filter", label: "FILTER DESIGN" },
    { id: "ambiguity", label: "AMBIGUITY" },
    { id: "octave", label: "OCTAVE" },
    { id: "ew", label: "EW THREAT ANALYSIS" },
  ]

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "20px",
            fontWeight: 700, letterSpacing: "0.15em", color: GOLD, margin: 0 }}>
            SIGNAL PROCESSING
          </h2>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
            color: DIM, letterSpacing: "0.1em", marginTop: "2px" }}>
            Radar Waveform Analysis + GNU Octave Sandbox
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: "4px", borderBottom: `1px solid ${BORDER}`,
        paddingBottom: "8px" }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            padding: "6px 14px", border: "none", cursor: "pointer",
            fontFamily: "Rajdhani, sans-serif", fontWeight: 600,
            fontSize: "11px", letterSpacing: "0.1em",
            background: activeTab === t.id ? "var(--accent-gold-glow)" : "transparent",
            color: activeTab === t.id ? GOLD : DIM,
            borderBottom: activeTab === t.id ? `2px solid ${GOLD}` : "2px solid transparent",
          }}>{t.label}</button>
        ))}
      </div>

      {activeTab === "waveform" && <WaveformTab />}
      {activeTab === "fft" && <FFTTab />}
      {activeTab === "filter" && <FilterTab />}
      {activeTab === "ambiguity" && <AmbiguityTab />}
      {activeTab === "octave" && <OctaveTab />}
      {activeTab === "library" && <WaveformLibraryTab />}
      {activeTab === "rdmap" && <RangeDopplerTab />}
      {activeTab === "ew" && <EWThreatTab />}
    </div>
  )
}

function ResultImage({ image, title }) {
  if (!image) return null
  return (
    <div style={{ marginTop: "16px" }}>
      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
        color: DIM, marginBottom: "8px" }}>{title}</div>
      <img src={`data:image/png;base64,${image}`} alt={title}
        style={{ width: "100%", borderRadius: "4px", border: `1px solid ${BORDER}` }} />
    </div>
  )
}

function Field({ label, value, onChange, type = "number", step }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
      <label style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
        color: DIM, letterSpacing: "0.1em" }}>{label}</label>
      <input type={type} value={value} onChange={e => onChange(e.target.value)}
        step={step}
        style={{ background: BG3, border: `1px solid ${BORDER}`, borderRadius: "4px",
          padding: "6px 10px", color: "var(--text-primary)",
          fontFamily: "JetBrains Mono, monospace", fontSize: "12px",
          outline: "none", width: "100%" }} />
    </div>
  )
}

function Select({ label, value, onChange, options }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
      <label style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
        color: DIM, letterSpacing: "0.1em" }}>{label}</label>
      <select value={value} onChange={e => onChange(e.target.value)}
        style={{ background: BG3, border: `1px solid ${BORDER}`, borderRadius: "4px",
          padding: "6px 10px", color: "var(--text-primary)",
          fontFamily: "JetBrains Mono, monospace", fontSize: "12px",
          outline: "none", width: "100%" }}>
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  )
}

function RunButton({ onClick, loading, label = "GENERATE" }) {
  return (
    <button onClick={onClick} disabled={loading} style={{
      padding: "8px 24px", background: loading ? "transparent" : "var(--accent-gold-glow)",
      border: `1px solid ${GOLD}`, borderRadius: "4px", cursor: loading ? "wait" : "pointer",
      fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px",
      letterSpacing: "0.15em", color: GOLD, marginTop: "8px",
    }}>{loading ? "PROCESSING..." : label}</button>
  )
}

function InfoBox({ data }) {
  if (!data) return null
  return (
    <div style={{ background: BG2, border: `1px solid ${BORDER}`, borderRadius: "4px",
      padding: "12px", marginTop: "8px", display: "flex", gap: "24px", flexWrap: "wrap" }}>
      {Object.entries(data).filter(([k]) => k !== "image").map(([k, v]) => (
        <div key={k}>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
            color: DIM, letterSpacing: "0.1em" }}>{k.toUpperCase().replace(/_/g, " ")}</div>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "12px",
            color: GOLD, marginTop: "2px" }}>{typeof v === "number" ? v.toFixed(2) : String(v)}</div>
        </div>
      ))}
    </div>
  )
}

const WAVEFORM_OPTIONS = [
  { value: "sine", label: "Sine Wave" },
  { value: "chirp", label: "Chirp" },
  { value: "lfm", label: "LFM (Linear Frequency Modulated)" },
  { value: "pulse", label: "Pulse" },
  { value: "barker", label: "Barker Code (13-chip)" },
]

function WaveformTab() {
  const [form, setForm] = useState({ waveform_type: "lfm", frequency: 10000,
    duration: 0.001, sample_rate: 100000, amplitude: 1.0, bandwidth: 5000 })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const run = async () => {
    setLoading(true); setError("")
    try {
      const res = await api.post(`${API}/waveform`, {
        ...form,
        frequency: parseFloat(form.frequency),
        duration: parseFloat(form.duration),
        sample_rate: parseFloat(form.sample_rate),
        amplitude: parseFloat(form.amplitude),
        bandwidth: parseFloat(form.bandwidth),
      })
      setResult(res.data)
      pushContext({ tab: 'Signal', operation: `Waveform Generation`, summary: `Waveform generated - type: ${form.waveform_type || 'LFM'}, sample rate: ${form.sample_rate} Hz, bandwidth: ${form.bandwidth} Hz`, detail: null })
    } catch(e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "24px" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <Select label="WAVEFORM TYPE" value={form.waveform_type}
          onChange={v => set("waveform_type", v)} options={WAVEFORM_OPTIONS} />
        <Field label="FREQUENCY (Hz)" value={form.frequency}
          onChange={v => set("frequency", v)} />
        <Field label="BANDWIDTH (Hz)" value={form.bandwidth}
          onChange={v => set("bandwidth", v)} />
        <Field label="DURATION (s)" value={form.duration}
          onChange={v => set("duration", v)} step="0.0001" />
        <Field label="SAMPLE RATE (Hz)" value={form.sample_rate}
          onChange={v => set("sample_rate", v)} />
        <Field label="AMPLITUDE" value={form.amplitude}
          onChange={v => set("amplitude", v)} step="0.1" />
        <RunButton onClick={run} loading={loading} />
        {error && <div style={{ color: "var(--danger)", fontSize: "11px",
          fontFamily: "JetBrains Mono, monospace" }}>{error}</div>}
      </div>
      <div>
        <InfoBox data={result} />
        <ResultImage image={result?.image} title="WAVEFORM PLOT" />
      </div>
    </div>
  )
}

function FFTTab() {
  const [form, setForm] = useState({ waveform_type: "lfm", frequency: 10000,
    duration: 0.001, sample_rate: 100000, amplitude: 1.0, bandwidth: 5000 })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const run = async () => {
    setLoading(true); setError("")
    try {
      const res = await api.post(`${API}/fft`, {
        ...form,
        frequency: parseFloat(form.frequency),
        duration: parseFloat(form.duration),
        sample_rate: parseFloat(form.sample_rate),
        amplitude: parseFloat(form.amplitude),
        bandwidth: parseFloat(form.bandwidth),
      })
      setResult(res.data)
    } catch(e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "24px" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <Select label="WAVEFORM TYPE" value={form.waveform_type}
          onChange={v => set("waveform_type", v)} options={WAVEFORM_OPTIONS} />
        <Field label="FREQUENCY (Hz)" value={form.frequency}
          onChange={v => set("frequency", v)} />
        <Field label="BANDWIDTH (Hz)" value={form.bandwidth}
          onChange={v => set("bandwidth", v)} />
        <Field label="DURATION (s)" value={form.duration}
          onChange={v => set("duration", v)} step="0.0001" />
        <Field label="SAMPLE RATE (Hz)" value={form.sample_rate}
          onChange={v => set("sample_rate", v)} />
        <RunButton onClick={run} loading={loading} label="RUN FFT" />
        {error && <div style={{ color: "var(--danger)", fontSize: "11px",
          fontFamily: "JetBrains Mono, monospace" }}>{error}</div>}
      </div>
      <div>
        <InfoBox data={result} />
        <ResultImage image={result?.image} title="TIME + FREQUENCY DOMAIN" />
      </div>
    </div>
  )
}

function FilterTab() {
  const [form, setForm] = useState({ filter_type: "lowpass", cutoff_freq: 5000,
    cutoff_freq2: 15000, sample_rate: 100000, order: 5 })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const run = async () => {
    setLoading(true); setError("")
    try {
      const res = await api.post(`${API}/filter`, {
        ...form,
        cutoff_freq: parseFloat(form.cutoff_freq),
        cutoff_freq2: parseFloat(form.cutoff_freq2),
        sample_rate: parseFloat(form.sample_rate),
        order: parseInt(form.order),
      })
      setResult(res.data)
    } catch(e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "24px" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <Select label="FILTER TYPE" value={form.filter_type}
          onChange={v => set("filter_type", v)} options={[
            { value: "lowpass", label: "Low Pass" },
            { value: "highpass", label: "High Pass" },
            { value: "bandpass", label: "Band Pass" },
            { value: "bandstop", label: "Band Stop" },
          ]} />
        <Field label="CUTOFF FREQ (Hz)" value={form.cutoff_freq}
          onChange={v => set("cutoff_freq", v)} />
        <Field label="CUTOFF FREQ 2 (Hz) - bandpass/stop"
          value={form.cutoff_freq2} onChange={v => set("cutoff_freq2", v)} />
        <Field label="SAMPLE RATE (Hz)" value={form.sample_rate}
          onChange={v => set("sample_rate", v)} />
        <Field label="FILTER ORDER" value={form.order}
          onChange={v => set("order", v)} />
        <RunButton onClick={run} loading={loading} label="DESIGN FILTER" />
        {error && <div style={{ color: "var(--danger)", fontSize: "11px",
          fontFamily: "JetBrains Mono, monospace" }}>{error}</div>}
      </div>
      <div>
        <InfoBox data={result} />
        <ResultImage image={result?.image} title="FILTER FREQUENCY RESPONSE" />
      </div>
    </div>
  )
}

function AmbiguityTab() {
  const [form, setForm] = useState({ waveform_type: "lfm", frequency: 10000,
    bandwidth: 5000, duration: 0.001, sample_rate: 100000 })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const run = async () => {
    setLoading(true); setError("")
    try {
      const res = await api.post(`${API}/ambiguity`, {
        ...form,
        frequency: parseFloat(form.frequency),
        bandwidth: parseFloat(form.bandwidth),
        duration: parseFloat(form.duration),
        sample_rate: parseFloat(form.sample_rate),
      })
      setResult(res.data)
    } catch(e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "24px" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <Select label="WAVEFORM TYPE" value={form.waveform_type}
          onChange={v => set("waveform_type", v)} options={WAVEFORM_OPTIONS} />
        <Field label="CENTER FREQUENCY (Hz)" value={form.frequency}
          onChange={v => set("frequency", v)} />
        <Field label="BANDWIDTH (Hz)" value={form.bandwidth}
          onChange={v => set("bandwidth", v)} />
        <Field label="DURATION (s)" value={form.duration}
          onChange={v => set("duration", v)} step="0.0001" />
        <Field label="SAMPLE RATE (Hz)" value={form.sample_rate}
          onChange={v => set("sample_rate", v)} />
        <RunButton onClick={run} loading={loading} label="COMPUTE AMBIGUITY" />
        {error && <div style={{ color: "var(--danger)", fontSize: "11px",
          fontFamily: "JetBrains Mono, monospace" }}>{error}</div>}
        <div style={{ background: BG2, border: `1px solid ${BORDER}`, borderRadius: "4px",
          padding: "10px", marginTop: "8px" }}>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
            color: DIM, lineHeight: 1.6 }}>
            The ambiguity function shows range-Doppler resolution. Narrow ridges indicate
            high resolution. LFM produces a characteristic diagonal ridge — the radar
            designer trades range vs Doppler resolution via bandwidth and duration.
          </div>
        </div>
      </div>
      <div>
        <InfoBox data={result} />
        <ResultImage image={result?.image} title="AMBIGUITY FUNCTION - RANGE/DOPPLER" />
      </div>
    </div>
  )
}

function OctaveTab() {
  const [code, setCode] = useState(`% GNU Octave Signal Processing Example
pkg load signal;
% LFM Waveform Generation and Analysis
fs = 100000;          % Sample rate (Hz)
T = 0.001;            % Duration (s)
f0 = 5000;            % Start frequency (Hz)
f1 = 15000;           % End frequency (Hz)
t = 0:1/fs:T-1/fs;    % Time vector

% Generate LFM chirp
s = chirp(t, f0, T, f1);

% Compute FFT
N = length(s);
S = abs(fft(s));
f = (0:N-1) * fs / N;

% Display results
disp(["Samples: ", num2str(N)]);
disp(["Freq range: ", num2str(f0), " - ", num2str(f1), " Hz"]);
disp(["Peak magnitude: ", num2str(max(S))]);
disp(["Time-bandwidth product: ", num2str((f1-f0)*T)]);`)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const run = async () => {
    setLoading(true); setError("")
    try {
      const res = await api.post(`${API}/octave`, { code, description: "Octave execution" })
      setResult(res.data)
    } catch(e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
        color: DIM, letterSpacing: "0.1em" }}>
        GNU OCTAVE 11.1.0 — MATLAB-COMPATIBLE SIGNAL PROCESSING SANDBOX
      </div>
      <textarea value={code} onChange={e => setCode(e.target.value)}
        rows={16} style={{
          background: BG3, border: `1px solid ${BORDER}`, borderRadius: "4px",
          padding: "12px", color: "var(--text-primary)",
          fontFamily: "JetBrains Mono, monospace", fontSize: "12px",
          outline: "none", width: "100%", resize: "vertical", lineHeight: 1.6,
        }} />
      <RunButton onClick={run} loading={loading} label="RUN OCTAVE" />
      {error && <div style={{ color: "var(--danger)", fontSize: "11px",
        fontFamily: "JetBrains Mono, monospace" }}>{error}</div>}
      {result && (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {result.stdout && (
            <div>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                color: DIM, marginBottom: "4px" }}>OUTPUT</div>
              <pre style={{ background: BG2, border: `1px solid ${BORDER}`,
                borderRadius: "4px", padding: "12px", margin: 0,
                fontFamily: "JetBrains Mono, monospace", fontSize: "12px",
                color: "var(--success)", overflowX: "auto" }}>{result.stdout}</pre>
            </div>
          )}
          {result.stderr && (
            <div>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                color: DIM, marginBottom: "4px" }}>STDERR</div>
              <pre style={{ background: BG2, border: `1px solid ${BORDER}`,
                borderRadius: "4px", padding: "12px", margin: 0,
                fontFamily: "JetBrains Mono, monospace", fontSize: "12px",
                color: "var(--warning)", overflowX: "auto" }}>{result.stderr}</pre>
            </div>
          )}
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
            color: result.returncode === 0 ? "var(--success)" : "var(--danger)" }}>
            EXIT CODE: {result.returncode}
          </div>
        </div>
      )}
    </div>
  )
}

// ── WAVEFORM LIBRARY ─────────────────────────────────────────────────────────
const WAVEFORM_LIBRARY = [
  {
    id: "lfm",
    name: "Linear FM (Chirp)",
    category: "Pulse Compression",
    description: "Frequency increases linearly across the pulse. Provides range resolution via pulse compression. Widely used in modern radar systems.",
    use_case: "SAR imaging, weather radar, automotive radar",
    params: { waveform_type: "lfm", frequency: 10000, bandwidth: 5000, duration: 0.001, sample_rate: 100000, amplitude: 1.0 },
    properties: ["Good range resolution", "Doppler tolerant", "High time-bandwidth product"]
  },
  {
    id: "barker13",
    name: "Barker Code (13-chip)",
    category: "Phase Coded",
    description: "13-element binary phase code with optimal autocorrelation sidelobe levels of -22.3dB. Maximum length Barker code provides excellent pulse compression.",
    use_case: "Communications, radar altimeters, low-power radar",
    params: { waveform_type: "barker", frequency: 10000, bandwidth: 5000, duration: 0.001, sample_rate: 100000, amplitude: 1.0 },
    properties: ["Low sidelobes (-22.3dB)", "Simple implementation", "Fixed compression ratio 13:1"]
  },
  {
    id: "sine",
    name: "Continuous Wave (CW)",
    category: "Unmodulated",
    description: "Pure sinusoidal waveform. Excellent Doppler measurement but no range resolution. Used in velocity-only applications.",
    use_case: "Speed guns, missile seekers, FMCW base",
    params: { waveform_type: "sine", frequency: 10000, bandwidth: 1000, duration: 0.001, sample_rate: 100000, amplitude: 1.0 },
    properties: ["Perfect Doppler measurement", "No range resolution", "Simple spectrum"]
  },
  {
    id: "pulse",
    name: "Rectangular Pulse",
    category: "Unmodulated",
    description: "Simple on/off pulse. Range resolution determined by pulse width. Trade-off between range resolution and detection sensitivity.",
    use_case: "Air traffic control, early warning radar",
    params: { waveform_type: "pulse", frequency: 10000, bandwidth: 5000, duration: 0.001, sample_rate: 100000, amplitude: 1.0 },
    properties: ["Simple implementation", "Range-sensitivity tradeoff", "High peak power"]
  },
]

function WaveformLibraryTab() {
  const [selected, setSelected] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const GOLD = "var(--accent-gold)"
  const BORDER = "var(--border)"
  const BG2 = "var(--bg-secondary)"
  const BG3 = "var(--bg-tertiary)"
  const DIM = "var(--text-dim)"

  const CATEGORY_COLORS = {
    "Pulse Compression": "#44aaff",
    "Phase Coded": "#c9a84c",
    "Unmodulated": "#44ffaa",
    "Frequency Hopped": "#ff6600"
  }

  const generate = async (waveform) => {
    setSelected(waveform)
    setLoading(true)
    setResult(null)
    try {
      const res = await api.post(`${API}/waveform`, waveform.params)
      setResult(res.data)
    } catch(e) {}
    setLoading(false)
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
        color: DIM }}>
        Standard radar waveform catalog — click any waveform to generate and analyze
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
        {WAVEFORM_LIBRARY.map(w => (
          <div key={w.id} onClick={() => generate(w)}
            style={{
              background: selected?.id === w.id ? "var(--accent-gold-glow)" : BG2,
              border: `1px solid ${selected?.id === w.id ? GOLD : BORDER}`,
              borderRadius: "4px", padding: "16px", cursor: "pointer",
              borderLeft: `4px solid ${CATEGORY_COLORS[w.category] || GOLD}`
            }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
              <div style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700,
                fontSize: "14px", color: GOLD }}>{w.name}</div>
              <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                padding: "2px 6px", borderRadius: "2px",
                color: CATEGORY_COLORS[w.category] || GOLD,
                border: `1px solid ${CATEGORY_COLORS[w.category] || GOLD}`,
                background: (CATEGORY_COLORS[w.category] || "#c9a84c") + "22" }}>
                {w.category}
              </div>
            </div>
            <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "11px",
              color: "var(--text-secondary)", lineHeight: 1.5, marginBottom: "8px" }}>
              {w.description}
            </div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
              color: DIM, marginBottom: "6px" }}>USE CASE: {w.use_case}</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
              {w.properties.map((p, i) => (
                <span key={i} style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                  padding: "2px 6px", borderRadius: "2px",
                  background: BG3, color: DIM, border: `1px solid ${BORDER}` }}>
                  {p}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {selected && (
        <div style={{ background: BG2, border: `1px solid ${BORDER}`, borderRadius: "4px", padding: "16px" }}>
          <div style={{ fontFamily: "Rajdhani, sans-serif", fontSize: "14px",
            fontWeight: 700, color: GOLD, marginBottom: "12px" }}>
            {selected.name} — Generated Waveform
          </div>
          {loading && <div style={{ color: DIM, fontFamily: "JetBrains Mono, monospace",
            fontSize: "11px" }}>Generating waveform...</div>}
          {result?.image && (
            <img src={`data:image/png;base64,${result.image}`}
              style={{ width: "100%", borderRadius: "4px" }} alt="Waveform" />
          )}
          {result && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
              gap: "8px", marginTop: "12px" }}>
              {Object.entries(result).filter(([k]) => k !== "image").map(([k, v]) => (
                <div key={k} style={{ fontFamily: "JetBrains Mono, monospace",
                  fontSize: "9px", color: DIM }}>
                  <div style={{ color: GOLD, textTransform: "uppercase",
                    letterSpacing: "0.05em" }}>{k.replace(/_/g, " ")}</div>
                  <div style={{ color: "var(--text-primary)", marginTop: "2px" }}>
                    {typeof v === "number" ? v.toLocaleString() : String(v)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── RANGE-DOPPLER MAP ────────────────────────────────────────────────────────
function RangeDopplerTab() {
  const [form, setForm] = useState({
    waveform_type: "lfm",
    frequency: 10000,
    bandwidth: 5000,
    duration: 0.001,
    sample_rate: 100000,
    num_pulses: 32,
    prf: 1000,
    target_range: 5000,
    target_velocity: 50,
    snr_db: 20
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const GOLD = "var(--accent-gold)"
  const BORDER = "var(--border)"
  const BG2 = "var(--bg-secondary)"
  const DIM = "var(--text-dim)"

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const run = async () => {
    setLoading(true); setError(""); setResult(null)
    try {
      // Generate ambiguity function as basis for range-doppler
      const res = await api.post(`${API}/ambiguity`, {
        waveform_type: form.waveform_type,
        frequency: parseFloat(form.frequency),
        bandwidth: parseFloat(form.bandwidth),
        duration: parseFloat(form.duration),
        sample_rate: parseFloat(form.sample_rate)
      })
      // Enhance with target overlay via Octave
      const octave_code = `
pkg load signal;
% Range-Doppler Map Simulation
fc = ${form.frequency};
bw = ${form.bandwidth};
T = ${form.duration};
fs = ${form.sample_rate};
N = ${form.num_pulses};
PRF = ${form.prf};
R_target = ${form.target_range};
v_target = ${form.target_velocity};
SNR_dB = ${form.snr_db};

t = (0:round(T*fs)-1)/fs;
c = 3e8;
lambda = c/fc;

% Generate LFM pulse
s = exp(1j*2*pi*(fc*t + bw/(2*T)*t.^2));

% Simulate slow-time returns
slow_time = (0:N-1)/PRF;
R = R_target + v_target*slow_time;
tau = 2*R/c;

% Build range-Doppler matrix
M = zeros(length(t), N);
for n = 1:N
  delay_samples = round(tau(n)*fs);
  if delay_samples < length(t)
    M(delay_samples+1:end, n) = s(1:end-delay_samples);
  end
end

% Add noise
noise = (randn(size(M)) + 1j*randn(size(M))) * 10^(-SNR_dB/20);
M = M + noise;

% Range compression
S_ref = conj(s);
for n = 1:N
  M(:,n) = ifft(fft(M(:,n)) .* fft(S_ref, length(t)));
end

% Doppler processing
RD = fftshift(fft(M, N, 2), 2);
RD_mag = 20*log10(abs(RD) + 1e-10);

% Display
range_axis = (0:length(t)-1)*c/(2*fs);
doppler_axis = (-N/2:N/2-1)*PRF/N * lambda/2;

figure('visible','off');
imagesc(doppler_axis, range_axis(1:200), RD_mag(1:200,:));
colormap jet;
xlabel('Velocity (m/s)');
ylabel('Range (m)');
title(sprintf('Range-Doppler Map: Target at %.0fm, %.1fm/s', R_target, v_target));
colorbar;
set(gca, 'Color', [0.05 0.07 0.12]);
set(gcf, 'Color', [0.05 0.07 0.12]);

% Save
print('-dpng', '-r150', '/tmp/nisa_rdmap.png');
disp('Range-Doppler map generated');
disp(sprintf('Target range: %.0f m', R_target));
disp(sprintf('Target velocity: %.1f m/s', v_target));
disp(sprintf('PRF: %.0f Hz', PRF));
disp(sprintf('Num pulses: %d', N));
`
      const rdRes = await api.post(`${API}/octave`, { code: octave_code })
      setResult({ ...res.data, rdmap_output: rdRes.data.output, rdmap_image: rdRes.data.image })
      pushContext({ tab: 'Signal', operation: 'Range-Doppler Map', summary: `Range-Doppler map generated. ${res.data.waveform_type || ''} waveform, Octave simulation complete.`.trim(), detail: null })
    } catch(e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "24px" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
          color: DIM, letterSpacing: "0.1em" }}>WAVEFORM</div>
        <Select label="TYPE" value={form.waveform_type}
          onChange={v => set("waveform_type", v)} options={WAVEFORM_OPTIONS} />
        <Field label="FREQUENCY (Hz)" value={form.frequency} onChange={v => set("frequency", v)} />
        <Field label="BANDWIDTH (Hz)" value={form.bandwidth} onChange={v => set("bandwidth", v)} />
        <Field label="DURATION (s)" value={form.duration} onChange={v => set("duration", v)} step="0.0001" />

        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
          color: DIM, letterSpacing: "0.1em", marginTop: "8px" }}>RADAR PARAMETERS</div>
        <Field label="NUM PULSES" value={form.num_pulses} onChange={v => set("num_pulses", v)} />
        <Field label="PRF (Hz)" value={form.prf} onChange={v => set("prf", v)} />
        <Field label="SNR (dB)" value={form.snr_db} onChange={v => set("snr_db", v)} />

        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
          color: DIM, letterSpacing: "0.1em", marginTop: "8px" }}>TARGET</div>
        <Field label="RANGE (m)" value={form.target_range} onChange={v => set("target_range", v)} />
        <Field label="VELOCITY (m/s)" value={form.target_velocity} onChange={v => set("target_velocity", v)} />

        <RunButton onClick={run} loading={loading} label="GENERATE R-D MAP" />
        {error && <div style={{ color: "var(--danger)", fontSize: "11px",
          fontFamily: "JetBrains Mono, monospace" }}>{error}</div>}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <div style={{ background: BG2, border: `1px solid ${BORDER}`,
          borderRadius: "4px", padding: "12px" }}>
          <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
            color: DIM, letterSpacing: "0.1em", marginBottom: "8px" }}>
            RANGE-DOPPLER MAP
          </div>
          {!result && !loading && (
            <div style={{ padding: "40px", textAlign: "center",
              fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: DIM }}>
              Configure parameters and click GENERATE R-D MAP
            </div>
          )}
          {loading && (
            <div style={{ padding: "40px", textAlign: "center",
              fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: GOLD }}>
              Computing Range-Doppler map via GNU Octave...
            </div>
          )}
          {result?.rdmap_image && (
            <img src={`data:image/png;base64,${result.rdmap_image}`}
              style={{ width: "100%", borderRadius: "4px" }} alt="Range-Doppler Map" />
          )}
          {result && !result.rdmap_image && result.image && (
            <img src={`data:image/png;base64,${result.image}`}
              style={{ width: "100%", borderRadius: "4px" }} alt="Ambiguity Function" />
          )}
        </div>

        {result?.rdmap_output && (
          <div style={{ background: BG2, border: `1px solid ${BORDER}`,
            borderRadius: "4px", padding: "12px" }}>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
              color: DIM, letterSpacing: "0.1em", marginBottom: "8px" }}>
              SIMULATION OUTPUT
            </div>
            <pre style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "11px",
              color: GOLD, margin: 0, whiteSpace: "pre-wrap" }}>
              {result.rdmap_output}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}


const inputStyle = { background: "var(--bg-primary)", border: "1px solid var(--border)", borderRadius: "3px", color: "var(--text-primary)", fontFamily: "JetBrains Mono, monospace", fontSize: "12px", padding: "7px 10px", width: "100%", outline: "none", boxSizing: "border-box" }
function Panel({ title, children }) {
  return (
    <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "4px" }}>
      <div style={{ padding: "10px 16px", borderBottom: "1px solid var(--border)" }}>
        <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "12px", letterSpacing: "0.15em", color: "var(--accent-gold)" }}>{title}</span>
      </div>
      <div style={{ padding: "14px 16px" }}>{children}</div>
    </div>
  )
}
function FieldLabel({ children }) {
  return <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--text-dim)", letterSpacing: "0.15em", marginBottom: "4px" }}>{children}</div>
}

const SIG_API = "http://localhost:8088"

function EWThreatTab() {
  const [mode, setMode] = useState("manual")
  const [form, setForm] = useState({ waveform_type: "pulse", bandwidth_hz: 1000000, frequency_hz: 9500000000, pulse_width_s: 0.000001, prf_hz: 1000 })
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const analyze = async () => {
    setLoading(true); setError(""); setResult(null)
    try {
      let res
      if (mode === "upload" && file) {
        const fd = new FormData()
        fd.append("file", file)
        res = await fetch(`${SIG_API}/ew/analyze/upload`, { method: "POST", headers: { "X-NISA-API-Key": import.meta.env.VITE_NISA_API_KEY || "d551fd7e05134c52b84286c201f0f36d8ddeb5e0611ed771ba44d6a4264f39cf" }, body: fd })
        res = await res.json()
      } else {
        const r = await api.post(`${SIG_API}/ew/analyze`, form)
        res = r.data
      }
      setResult(res)
    } catch(e) { setError(e.message) }
    setLoading(false)
  }

  const sevColor = (s) => ({ critical: "var(--danger)", high: "#f59e0b", medium: "var(--accent-cyan, #00d4ff)", low: "var(--success)" })[s] || "var(--text-dim)"
  const vulnColor = (v) => ({ CRITICAL: "var(--danger)", HIGH: "#f59e0b", MEDIUM: "var(--accent-cyan, #00d4ff)", LOW: "var(--success)" })[v] || "var(--text-dim)"

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <Panel title="EW THREAT ANALYSIS">
        <div style={{ marginBottom: "12px", display: "flex", gap: "8px" }}>
          {["manual", "upload"].map(m => (
            <button key={m} onClick={() => setMode(m)} style={{ background: mode === m ? "var(--accent-gold-glow)" : "transparent", border: `1px solid ${mode === m ? GOLD : BORDER}`, color: mode === m ? GOLD : DIM, borderRadius: "3px", padding: "5px 14px", cursor: "pointer", fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "11px", letterSpacing: "0.1em", textTransform: "uppercase" }}>{m === "manual" ? "MANUAL PARAMETERS" : "UPLOAD WAVEFORM FILE"}</button>
          ))}
        </div>
        {mode === "manual" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
              <div style={{ flex: 1, minWidth: "140px" }}>
                <FieldLabel>WAVEFORM TYPE</FieldLabel>
                <select value={form.waveform_type} onChange={e => setForm({...form, waveform_type: e.target.value})} style={inputStyle}>
                  {["pulse","lfm","chirp","barker","cw","sine"].map(w => <option key={w} value={w}>{w.toUpperCase()}</option>)}
                </select>
              </div>
              <div style={{ flex: 1, minWidth: "140px" }}>
                <FieldLabel>FREQUENCY (Hz)</FieldLabel>
                <input type="number" value={form.frequency_hz} onChange={e => setForm({...form, frequency_hz: parseFloat(e.target.value)})} style={inputStyle} />
              </div>
              <div style={{ flex: 1, minWidth: "140px" }}>
                <FieldLabel>BANDWIDTH (Hz)</FieldLabel>
                <input type="number" value={form.bandwidth_hz} onChange={e => setForm({...form, bandwidth_hz: parseFloat(e.target.value)})} style={inputStyle} />
              </div>
              <div style={{ flex: 1, minWidth: "140px" }}>
                <FieldLabel>PULSE WIDTH (s)</FieldLabel>
                <input type="number" value={form.pulse_width_s} onChange={e => setForm({...form, pulse_width_s: parseFloat(e.target.value)})} style={inputStyle} />
              </div>
              <div style={{ flex: 1, minWidth: "140px" }}>
                <FieldLabel>PRF (Hz)</FieldLabel>
                <input type="number" value={form.prf_hz} onChange={e => setForm({...form, prf_hz: parseFloat(e.target.value)})} style={inputStyle} />
              </div>
            </div>
          </div>
        )}
        {mode === "upload" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <FieldLabel>UPLOAD WAVEFORM FILE (CSV, JSON, WAV)</FieldLabel>
            <input type="file" accept=".csv,.json,.wav" onChange={e => setFile(e.target.files[0])} style={{ ...inputStyle, padding: "6px" }} />
            {file && <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--success)" }}>Selected: {file.name}</div>}
          </div>
        )}
        {error && <div style={{ color: "var(--danger)", fontFamily: "JetBrains Mono, monospace", fontSize: "11px", marginTop: "8px" }}>{error}</div>}
        <button onClick={analyze} disabled={loading || (mode === "upload" && !file)} style={{ marginTop: "12px", background: loading ? "transparent" : GOLD, border: `1px solid ${GOLD}`, color: loading ? GOLD : "var(--bg-primary)", borderRadius: "3px", padding: "8px 20px", cursor: "pointer", fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "13px", letterSpacing: "0.1em" }}>{loading ? "ANALYZING..." : "ANALYZE EW THREATS"}</button>
      </Panel>

      {result && (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <Panel title="THREAT ASSESSMENT">
            <div style={{ display: "flex", gap: "16px", marginBottom: "12px", flexWrap: "wrap" }}>
              <div style={{ textAlign: "center", padding: "10px 16px", background: "var(--bg-primary)", borderRadius: "3px", border: `1px solid ${vulnColor(result.overall_vulnerability)}` }}>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "20px", fontWeight: 700, color: vulnColor(result.overall_vulnerability) }}>{result.overall_vulnerability}</div>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: DIM, marginTop: "2px" }}>OVERALL VULNERABILITY</div>
              </div>
              <div style={{ textAlign: "center", padding: "10px 16px", background: "var(--bg-primary)", borderRadius: "3px", border: "1px solid var(--border)" }}>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "20px", fontWeight: 700, color: result.lpi_score >= 60 ? "var(--success)" : result.lpi_score >= 30 ? "#f59e0b" : "var(--danger)" }}>{result.lpi_score}</div>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: DIM, marginTop: "2px" }}>LPI SCORE</div>
              </div>
              <div style={{ textAlign: "center", padding: "10px 16px", background: "var(--bg-primary)", borderRadius: "3px", border: "1px solid var(--border)" }}>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "20px", fontWeight: 700, color: "var(--danger)" }}>{result.threats_identified?.length || 0}</div>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: DIM, marginTop: "2px" }}>THREATS FOUND</div>
              </div>
              <div style={{ textAlign: "center", padding: "10px 16px", background: "var(--bg-primary)", borderRadius: "3px", border: "1px solid var(--success)" }}>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "20px", fontWeight: 700, color: "var(--success)" }}>{result.resistant_to?.length || 0}</div>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: DIM, marginTop: "2px" }}>RESISTANT TO</div>
              </div>
            </div>
            {result.threats_identified?.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <FieldLabel>IDENTIFIED THREATS</FieldLabel>
                {result.threats_identified.map(t => (
                  <div key={t.threat_id} style={{ padding: "10px 12px", background: "var(--bg-primary)", borderRadius: "3px", border: `1px solid ${sevColor(t.severity)}44` }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                      <span style={{ fontFamily: "Rajdhani, sans-serif", fontWeight: 700, fontSize: "13px", color: sevColor(t.severity) }}>{t.name}</span>
                      <span style={{ background: sevColor(t.severity) + "22", border: `1px solid ${sevColor(t.severity)}`, borderRadius: "2px", padding: "1px 6px", fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: sevColor(t.severity), textTransform: "uppercase" }}>{t.severity}</span>
                    </div>
                    <div style={{ fontFamily: "Outfit, sans-serif", fontSize: "11px", color: "var(--text-secondary)", marginBottom: "4px" }}>{t.description}</div>
                    <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--accent-cyan, #00d4ff)" }}>REC: {t.countermeasure}</div>
                  </div>
                ))}
              </div>
            )}
            {result.resistant_to?.length > 0 && (
              <div style={{ marginTop: "10px" }}>
                <FieldLabel>RESISTANT TO</FieldLabel>
                <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "4px" }}>
                  {result.resistant_to.map(r => (
                    <span key={r} style={{ background: "rgba(34,197,94,0.1)", border: "1px solid var(--success)", borderRadius: "10px", padding: "2px 10px", fontFamily: "JetBrains Mono, monospace", fontSize: "9px", color: "var(--success)" }}>{r}</span>
                  ))}
                </div>
              </div>
            )}
            {result.spectral_analysis && Object.keys(result.spectral_analysis).length > 0 && (
              <div style={{ marginTop: "10px" }}>
                <FieldLabel>SPECTRAL ANALYSIS</FieldLabel>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "var(--text-secondary)", marginTop: "4px" }}>
                  {result.spectral_analysis.peak_frequency_hz && <div>Peak Frequency: {(result.spectral_analysis.peak_frequency_hz / 1e6).toFixed(3)} MHz</div>}
                  {result.spectral_analysis.spectral_flatness !== undefined && <div>Spectral Flatness: {result.spectral_analysis.spectral_flatness.toFixed(4)}</div>}
                </div>
              </div>
            )}
          </Panel>
        </div>
      )}
    </div>
  )
}