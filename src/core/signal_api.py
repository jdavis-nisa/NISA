#!/usr/bin/env python3.11
"""
NISA Signal Processing API - Port 8088
Radar and EW signal analysis sandbox
Integrates NumPy, SciPy, Matplotlib, and GNU Octave
"""
import os
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/NISA/.env"))
import sys
import json
import base64
import tempfile
import subprocess
import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fastapi import HTTPException, FastAPI, Request, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI(title="NISA Signal Processing API", version="1.0.0")

# ── API Key Authentication ────────────────────────────────────────
NISA_API_KEY = os.environ.get("NISA_API_KEY", "")

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if request.url.path in ("/health", "/waveform_types") or request.method == "OPTIONS":
        return await call_next(request)
    if NISA_API_KEY:
        key = request.headers.get("X-NISA-API-Key", "")
        if key != NISA_API_KEY:
            return JSONResponse(status_code=403, content={"error": "Invalid or missing API key"})
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ────────────────────────────────────────────────────────

class WaveformRequest(BaseModel):
    waveform_type: str  # sine, chirp, pulse, lfm, barker
    frequency: float = 1000.0
    duration: float = 0.01
    sample_rate: float = 100000.0
    amplitude: float = 1.0
    bandwidth: Optional[float] = None  # for chirp/LFM
    pulse_width: Optional[float] = None  # for pulse

class FFTRequest(BaseModel):
    waveform_type: str = "sine"
    frequency: float = 1000.0
    duration: float = 0.01
    sample_rate: float = 100000.0
    amplitude: float = 1.0
    bandwidth: Optional[float] = None

class FilterRequest(BaseModel):
    filter_type: str  # lowpass, highpass, bandpass, bandstop
    cutoff_freq: float
    sample_rate: float = 100000.0
    order: int = 5
    cutoff_freq2: Optional[float] = None  # for bandpass/bandstop

class AmbiguityRequest(BaseModel):
    waveform_type: str = "lfm"
    frequency: float = 1000.0
    bandwidth: float = 5000.0
    duration: float = 0.001
    sample_rate: float = 100000.0

class OctaveRequest(BaseModel):
    code: str
    description: Optional[str] = ""

# ── Helpers ───────────────────────────────────────────────────────

def fig_to_base64(fig):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        fig.savefig(f.name, dpi=150, bbox_inches="tight",
                    facecolor="#0a0e1a", edgecolor="none")
        tmp = f.name
    with open(tmp, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    os.unlink(tmp)
    plt.close(fig)
    return data

def generate_waveform(req):
    t = np.linspace(0, req.duration, int(req.sample_rate * req.duration))
    bw = req.bandwidth or req.frequency * 2

    if req.waveform_type == "sine":
        y = req.amplitude * np.sin(2 * np.pi * req.frequency * t)
    elif req.waveform_type == "chirp":
        y = req.amplitude * signal.chirp(t, f0=req.frequency,
                f1=req.frequency + bw, t1=req.duration, method="linear")
    elif req.waveform_type == "lfm":
        y = req.amplitude * signal.chirp(t, f0=req.frequency - bw/2,
                f1=req.frequency + bw/2, t1=req.duration, method="linear")
    elif req.waveform_type == "pulse":
        pw = req.pulse_width or req.duration * 0.1
        y = req.amplitude * (t < pw).astype(float)
    elif req.waveform_type == "barker":
        barker13 = np.array([1,1,1,1,1,-1,-1,1,1,-1,1,-1,1])
        chip_len = max(1, len(t) // 13)
        y = np.repeat(barker13, chip_len)[:len(t)] * req.amplitude
    else:
        y = req.amplitude * np.sin(2 * np.pi * req.frequency * t)
    return t, y

# ── Endpoints ─────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "online", "service": "signal_processing_api", "port": 8088}

@app.post("/waveform")
def generate_waveform_plot(req: WaveformRequest):
    try:
        t, y = generate_waveform(req)
        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor("#0a0e1a")
        ax.set_facecolor("#0d1224")
        ax.plot(t * 1000, y, color="#c9a84c", linewidth=1.2)
        ax.set_xlabel("Time (ms)", color="#8899bb")
        ax.set_ylabel("Amplitude", color="#8899bb")
        ax.set_title(f"{req.waveform_type.upper()} Waveform - {req.frequency:.0f} Hz",
                     color="#c9a84c", fontsize=13)
        ax.tick_params(colors="#8899bb")
        for spine in ax.spines.values():
            spine.set_edgecolor("#1e2d4a")
        ax.grid(True, color="#1e2d4a", alpha=0.6)
        img = fig_to_base64(fig)
        return {
            "image": img,
            "samples": len(t),
            "duration_ms": req.duration * 1000,
            "sample_rate": req.sample_rate,
            "waveform_type": req.waveform_type,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fft")
def compute_fft(req: FFTRequest):
    try:
        wr = WaveformRequest(**req.dict())
        t, y = generate_waveform(wr)
        N = len(y)
        yf = np.abs(fft(y))[:N//2]
        xf = fftfreq(N, 1/req.sample_rate)[:N//2]
        peak_idx = np.argmax(yf)
        peak_freq = xf[peak_idx]

        fig, axes = plt.subplots(2, 1, figsize=(10, 7))
        fig.patch.set_facecolor("#0a0e1a")
        for ax in axes:
            ax.set_facecolor("#0d1224")
            ax.tick_params(colors="#8899bb")
            for spine in ax.spines.values():
                spine.set_edgecolor("#1e2d4a")
            ax.grid(True, color="#1e2d4a", alpha=0.6)

        axes[0].plot(t * 1000, y, color="#c9a84c", linewidth=1.0)
        axes[0].set_xlabel("Time (ms)", color="#8899bb")
        axes[0].set_ylabel("Amplitude", color="#8899bb")
        axes[0].set_title("Time Domain", color="#c9a84c")

        axes[1].plot(xf / 1000, yf, color="#4c9ac9", linewidth=1.0)
        axes[1].axvline(peak_freq / 1000, color="#c9a84c",
                        linestyle="--", alpha=0.7, label=f"Peak: {peak_freq:.0f} Hz")
        axes[1].set_xlabel("Frequency (kHz)", color="#8899bb")
        axes[1].set_ylabel("Magnitude", color="#8899bb")
        axes[1].set_title("Frequency Domain (FFT)", color="#c9a84c")
        axes[1].legend(facecolor="#0d1224", labelcolor="#c9a84c")

        plt.tight_layout()
        img = fig_to_base64(fig)
        return {
            "image": img,
            "peak_frequency_hz": float(peak_freq),
            "num_samples": N,
            "frequency_resolution_hz": float(req.sample_rate / N),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/filter")
def design_filter(req: FilterRequest):
    try:
        nyq = req.sample_rate / 2
        if req.filter_type in ("bandpass", "bandstop"):
            if not req.cutoff_freq2:
                raise HTTPException(status_code=400,
                    detail="cutoff_freq2 required for bandpass/bandstop")
            Wn = [req.cutoff_freq / nyq, req.cutoff_freq2 / nyq]
        else:
            Wn = req.cutoff_freq / nyq

        b, a = signal.butter(req.order, Wn, btype=req.filter_type)
        w, h = signal.freqz(b, a, worN=2048)
        freqs = w * req.sample_rate / (2 * np.pi)
        magnitude_db = 20 * np.log10(np.abs(h) + 1e-12)

        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor("#0a0e1a")
        ax.set_facecolor("#0d1224")
        ax.plot(freqs / 1000, magnitude_db, color="#c9a84c", linewidth=1.5)
        ax.axhline(-3, color="#4c9ac9", linestyle="--",
                   alpha=0.7, label="-3 dB cutoff")
        ax.set_xlabel("Frequency (kHz)", color="#8899bb")
        ax.set_ylabel("Magnitude (dB)", color="#8899bb")
        ax.set_title(f"Butterworth {req.filter_type.upper()} Filter - Order {req.order}",
                     color="#c9a84c", fontsize=13)
        ax.tick_params(colors="#8899bb")
        for spine in ax.spines.values():
            spine.set_edgecolor("#1e2d4a")
        ax.grid(True, color="#1e2d4a", alpha=0.6)
        ax.legend(facecolor="#0d1224", labelcolor="#8899bb")
        ax.set_ylim(-80, 5)
        img = fig_to_base64(fig)
        return {
            "image": img,
            "filter_type": req.filter_type,
            "order": req.order,
            "cutoff_hz": req.cutoff_freq,
            "sample_rate": req.sample_rate,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ambiguity")
def compute_ambiguity(req: AmbiguityRequest):
    try:
        t = np.linspace(0, req.duration,
                        int(req.sample_rate * req.duration))
        bw = req.bandwidth
        s = signal.chirp(t, f0=req.frequency - bw/2,
                         f1=req.frequency + bw/2,
                         t1=req.duration, method="linear")
        s = s * np.hanning(len(s))
        N = len(s)
        delays = np.arange(-N//4, N//4)
        dopplers = np.linspace(-bw, bw, 64)
        chi = np.zeros((len(dopplers), len(delays)))
        for i, fd in enumerate(dopplers):
            doppler_shift = np.exp(1j * 2 * np.pi * fd * t)
            s_shifted = s * doppler_shift
            for j, tau in enumerate(delays):
                s_delayed = np.roll(s, tau)
                chi[i, j] = np.abs(np.dot(s_shifted, s_delayed.conj()))
        chi = chi / chi.max()

        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor("#0a0e1a")
        ax.set_facecolor("#0d1224")
        im = ax.contourf(delays / req.sample_rate * 1e6,
                         dopplers / 1000, chi, levels=20, cmap="plasma")
        plt.colorbar(im, ax=ax, label="Normalized Magnitude")
        ax.set_xlabel("Delay (microseconds)", color="#8899bb")
        ax.set_ylabel("Doppler Shift (kHz)", color="#8899bb")
        ax.set_title(f"Ambiguity Function - {req.waveform_type.upper()}",
                     color="#c9a84c", fontsize=13)
        ax.tick_params(colors="#8899bb")
        for spine in ax.spines.values():
            spine.set_edgecolor("#1e2d4a")
        img = fig_to_base64(fig)
        return {
            "image": img,
            "waveform_type": req.waveform_type,
            "bandwidth_hz": bw,
            "duration_ms": req.duration * 1000,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/octave")
def run_octave(req: OctaveRequest):
    try:
        octave_bin = "/opt/homebrew/bin/octave"
        if not os.path.exists(octave_bin):
            raise HTTPException(status_code=500, detail="Octave not found")
        with tempfile.NamedTemporaryFile(suffix=".m", delete=False,
                                         mode="w") as f:
            f.write(req.code)
            tmp = f.name
        result = subprocess.run(
            [octave_bin, "--no-gui", "--quiet", tmp],
            capture_output=True, text=True, timeout=60
        )
        os.unlink(tmp)
        
        # Check for saved image output
        image_b64 = None
        image_path = "/tmp/nisa_rdmap.png"
        if os.path.exists(image_path):
            with open(image_path, "rb") as img_f:
                image_b64 = base64.b64encode(img_f.read()).decode()
            os.unlink(image_path)
        
        return {
            "output": result.stdout,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "description": req.description,
            "image": image_b64,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Octave execution timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/waveform_types")
def get_waveform_types():
    return {
        "types": [
            {"id": "sine", "name": "Sine Wave", "description": "Basic sinusoidal waveform"},
            {"id": "chirp", "name": "Chirp", "description": "Frequency sweep from f0 to f0+bandwidth"},
            {"id": "lfm", "name": "LFM", "description": "Linear Frequency Modulated - primary radar waveform"},
            {"id": "pulse", "name": "Pulse", "description": "Rectangular pulse waveform"},
            {"id": "barker", "name": "Barker Code", "description": "13-chip Barker code for pulse compression"},
        ]
    }


import io
import csv as csv_module

EW_THREATS = {
    'noise_jamming': {'name': 'Noise Jamming', 'description': 'Broadband noise to mask radar returns', 'vulnerable': ['cw','pulse','sine'], 'resistant': ['lfm','barker','chirp'], 'severity': 'high', 'countermeasure': 'Use LPI waveforms, pulse compression'},
    'spot_jamming': {'name': 'Spot Jamming', 'description': 'High power on specific frequency', 'vulnerable': ['cw','sine','pulse'], 'resistant': ['lfm','chirp','barker'], 'severity': 'high', 'countermeasure': 'Frequency agility, LFM waveforms'},
    'drfm_jamming': {'name': 'DRFM Deceptive Jamming', 'description': 'Records and retransmits modified signal', 'vulnerable': ['pulse','lfm','barker','cw','chirp'], 'resistant': [], 'severity': 'critical', 'countermeasure': 'Randomize waveform parameters per pulse'},
    'range_gate_pulloff': {'name': 'Range Gate Pull-Off', 'description': 'Pulls range gate off true target', 'vulnerable': ['pulse','cw'], 'resistant': ['lfm','barker'], 'severity': 'high', 'countermeasure': 'Leading edge tracking, LFM waveforms'},
    'velocity_gate_pulloff': {'name': 'Velocity Gate Pull-Off', 'description': 'Pulls Doppler gate off true velocity', 'vulnerable': ['cw','pulse'], 'resistant': ['lfm','chirp'], 'severity': 'high', 'countermeasure': 'Wideband Doppler processing'},
    'lpi_detection': {'name': 'LPI Detection Threat', 'description': 'Intercept receivers detect emissions', 'vulnerable': ['pulse','cw','sine'], 'resistant': ['lfm','barker','chirp'], 'severity': 'critical', 'countermeasure': 'Use LPI waveforms, reduce peak power'},
    'chaff': {'name': 'Chaff', 'description': 'Metallic strips creating false returns', 'vulnerable': ['pulse','cw'], 'resistant': ['lfm','chirp'], 'severity': 'medium', 'countermeasure': 'MTI/MTD processing, high range resolution'},
    'sweep_jamming': {'name': 'Sweep Jamming', 'description': 'Jammer sweeps across frequency band', 'vulnerable': ['pulse','cw'], 'resistant': ['lfm','barker'], 'severity': 'high', 'countermeasure': 'Frequency hopping, wideband receivers'},
}

def analyze_ew_threats(waveform_type, bandwidth_hz, frequency_hz, pulse_width_s, prf_hz):
    wt = waveform_type.lower()
    threats = []
    resistant_to = []
    for tid, t in EW_THREATS.items():
        if wt in t['vulnerable']:
            threats.append({'threat_id': tid, 'name': t['name'], 'description': t['description'], 'severity': t['severity'], 'countermeasure': t['countermeasure']})
        elif wt in t['resistant']:
            resistant_to.append(t['name'])
    lpi_score = 0
    if bandwidth_hz > 1e6: lpi_score += 30
    if wt in ['lfm','barker','chirp']: lpi_score += 40
    if pulse_width_s > 0 and pulse_width_s < 1e-6: lpi_score += 15
    if prf_hz > 1000: lpi_score += 15
    lpi_score = min(100, lpi_score)
    critical = sum(1 for t in threats if t['severity'] == 'critical')
    high = sum(1 for t in threats if t['severity'] == 'high')
    overall = 'CRITICAL' if critical > 0 else 'HIGH' if high >= 2 else 'MEDIUM' if high >= 1 else 'LOW'
    return {'waveform_type': waveform_type, 'frequency_hz': frequency_hz, 'bandwidth_hz': bandwidth_hz,
            'pulse_width_s': pulse_width_s, 'prf_hz': prf_hz, 'overall_vulnerability': overall,
            'lpi_score': lpi_score, 'threats_identified': threats, 'resistant_to': resistant_to,
            'recommendations': list(set(t['countermeasure'] for t in threats[:3]))}

class EWAnalysisRequest(BaseModel):
    waveform_type: str = 'pulse'
    bandwidth_hz: float = 1e6
    frequency_hz: float = 9.5e9
    pulse_width_s: float = 1e-6
    prf_hz: float = 1000.0

@app.post('/ew/analyze')
def ew_threat_analysis(req: EWAnalysisRequest):
    return analyze_ew_threats(req.waveform_type, req.bandwidth_hz, req.frequency_hz, req.pulse_width_s, req.prf_hz)

@app.post('/ew/analyze/upload')
async def ew_analyze_upload(file: UploadFile = File(...)):
    content = await file.read()
    fname = file.filename.lower()
    params = {'waveform_type': 'unknown', 'bandwidth_hz': 0.0, 'frequency_hz': 0.0, 'pulse_width_s': 0.0, 'prf_hz': 0.0}
    samples = []
    try:
        if fname.endswith('.csv'):
            text = content.decode('utf-8')
            reader = csv_module.DictReader(io.StringIO(text))
            rows = list(reader)
            if rows:
                cols = list(rows[0].keys())
                amp_col = next((c for c in cols if any(k in c.lower() for k in ['amp','val','y'])), cols[-1])
                time_col = next((c for c in cols if any(k in c.lower() for k in ['time','t','x'])), cols[0])
                times = [float(r[time_col]) for r in rows if r.get(time_col)]
                samples = [float(r[amp_col]) for r in rows if r.get(amp_col)]
                if len(times) > 1:
                    dt = times[1] - times[0]
                    sr = 1.0 / dt if dt > 0 else 1e6
                    params['bandwidth_hz'] = sr / 2
                    params['prf_hz'] = 1000.0
            params['waveform_type'] = 'captured_csv'
        elif fname.endswith('.json'):
            import json as jm
            data = jm.loads(content)
            for k in ['waveform_type','bandwidth_hz','frequency_hz','pulse_width_s','prf_hz']:
                if k in data: params[k] = data[k]
        elif fname.endswith('.wav'):
            import wave, struct
            with wave.open(io.BytesIO(content)) as wf:
                sr = wf.getframerate()
                nf = wf.getnframes()
                raw = wf.readframes(nf)
                samples = list(struct.unpack(str(nf) + 'h', raw[:nf*2]))
                params['bandwidth_hz'] = sr / 2
                params['waveform_type'] = 'captured_wav'
        else:
            raise HTTPException(status_code=400, detail='Unsupported format. Use CSV, JSON, or WAV.')
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=400, detail=f'Parse error: {str(e)}')
    spectral = {}
    if len(samples) > 10:
        try:
            import numpy as np
            arr = np.array(samples, dtype=float)
            fft_vals = np.abs(np.fft.rfft(arr))
            peak_idx = int(np.argmax(fft_vals))
            if params['bandwidth_hz'] > 0:
                freq_res = params['bandwidth_hz'] / len(fft_vals)
                spectral['peak_frequency_hz'] = float(peak_idx * freq_res)
                spectral['spectral_flatness'] = float(np.mean(fft_vals) / (np.max(fft_vals) + 1e-10))
                if params['frequency_hz'] == 0: params['frequency_hz'] = spectral['peak_frequency_hz']
        except Exception: pass
    result = analyze_ew_threats(params['waveform_type'], params['bandwidth_hz'], params['frequency_hz'], params['pulse_width_s'], params['prf_hz'])
    result['source'] = 'file_upload'
    result['filename'] = file.filename
    result['spectral_analysis'] = spectral
    return result

@app.get('/ew/threats')
def get_ew_threats():
    return {'threats': [{'id': k, 'name': v['name'], 'description': v['description']} for k, v in EW_THREATS.items()]}
if __name__ == "__main__":
    print("Starting NISA Signal Processing API on port 8088...")
    uvicorn.run(app, host="127.0.0.1", port=8088, log_level="warning")
