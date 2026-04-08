import { useState } from "react"
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
    { id: "filter", label: "FILTER DESIGN" },
    { id: "ambiguity", label: "AMBIGUITY" },
    { id: "octave", label: "OCTAVE" },
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
