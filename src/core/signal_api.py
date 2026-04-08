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
from fastapi import HTTPException, FastAPI, Request
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
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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
            capture_output=True, text=True, timeout=30
        )
        os.unlink(tmp)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "description": req.description,
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

if __name__ == "__main__":
    print("Starting NISA Signal Processing API on port 8088...")
    uvicorn.run(app, host="0.0.0.0", port=8088, log_level="warning")
