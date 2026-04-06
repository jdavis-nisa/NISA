import os
import sys
import wave
import subprocess
import time
import numpy as np
import sounddevice as sd
import webrtcvad
import requests

# ── Configuration ────────────────────────────────────────────────
PYTHON        = "/opt/homebrew/bin/python3.11"
WHISPER_CLI   = "/opt/homebrew/bin/whisper-cli"
WHISPER_MODEL = os.path.expanduser("~/NISA/models/whisper/ggml-base.en.bin")
PIPER_MODEL   = os.path.expanduser("~/NISA/models/piper/en_GB-alba-medium.onnx")
NISA_API      = "http://localhost:8081/chat"

SAMPLE_RATE     = 16000
FRAME_DURATION  = 30
CHANNELS        = 1
SILENCE_TIMEOUT = 2.0
INPUT_DEVICE    = 0
OUTPUT_DEVICE   = 1
IN_PATH         = "/tmp/nisaba_input.wav"


# ── Text to Speech ───────────────────────────────────────────────
def speak(text: str):
    print(f"\nNisaba: {text}\n")
    try:
        piper = subprocess.Popen(
            [PYTHON, "-m", "piper",
             "--model", PIPER_MODEL,
             "--output-raw"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        raw_audio, _ = piper.communicate(input=text.encode() + b"\n")

        if raw_audio:
            # Write raw audio to WAV file with proper headers
            with wave.open("/tmp/nisaba_out.wav", "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(22050)
                wf.writeframes(raw_audio)
            subprocess.run(["afplay", "/tmp/nisaba_out.wav"])
        else:
            print("[TTS] No audio generated")

    except Exception as e:
        print(f"[TTS] Exception: {e}")


# ── Speech to Text ───────────────────────────────────────────────
def transcribe(audio_data: np.ndarray) -> str:
    try:
        with wave.open(IN_PATH, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(
                (audio_data * 32767).astype(np.int16).tobytes())

        result = subprocess.run(
            [WHISPER_CLI,
             "--model",    WHISPER_MODEL,
             "--file",     IN_PATH,
             "--no-timestamps",
             "--language", "en"],
            capture_output=True,
            text=True
        )

        lines = [
            l.strip() for l in result.stdout.split("\n")
            if l.strip() and not l.strip().startswith("[")
        ]
        return " ".join(lines)

    except Exception as e:
        print(f"[STT] Error: {e}")
        return ""
    finally:
        if os.path.exists(IN_PATH):
            os.unlink(IN_PATH)


# ── NLU API ──────────────────────────────────────────────────────
def ask_nisaba(text: str) -> str:
    try:
        r = requests.post(
            NISA_API,
            json={"message": text, "max_tokens": 200},
            timeout=60
        )
        if r.status_code == 200:
            return r.json()["response"]
        return "I encountered an issue processing that."
    except Exception as e:
        return f"Connection error: {e}"


# ── Main Loop ────────────────────────────────────────────────────
def listen_and_respond():
    vad           = webrtcvad.Vad(3)
    frame_size    = int(SAMPLE_RATE * FRAME_DURATION / 1000)
    silence_limit = int(SILENCE_TIMEOUT * 1000 / FRAME_DURATION)

    print("=" * 50)
    print("  NISA Voice Pipeline — Online")
    print("  Nisaba is listening...")
    print("  Press Ctrl+C to stop")
    print("=" * 50)

    speak("I am online. Speak to me.")

    audio_buffer  = []
    silent_frames = 0
    speaking      = False

    def callback(indata, frames, time_info, status):
        nonlocal silent_frames, speaking, audio_buffer

        chunk = indata[:, 0].copy()
        pcm   = (chunk * 32767).astype(np.int16).tobytes()

        try:
            is_speech = vad.is_speech(pcm, SAMPLE_RATE)
        except Exception:
            is_speech = False

        if is_speech:
            if not speaking:
                print("\n[Listening...]")
                speaking = True
            audio_buffer.append(chunk)
            silent_frames = 0

        elif speaking:
            audio_buffer.append(chunk)
            silent_frames += 1

            if silent_frames >= silence_limit:
                speaking      = False
                audio_data    = np.concatenate(audio_buffer)
                audio_buffer.clear()
                silent_frames = 0

                print("[Processing...]")
                transcript = transcribe(audio_data)

                if transcript and len(transcript.strip()) > 2:
                    print(f"You: {transcript}")
                    response = ask_nisaba(transcript)
                    speak(response)
                else:
                    print("[Could not transcribe — try again]")

                print("\nNisaba is listening...")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        blocksize=frame_size,
        device=INPUT_DEVICE,
        callback=callback
    ):
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nNisaba offline.")


# ── Entry Point ──────────────────────────────────────────────────
if __name__ == "__main__":
    for path, label in [
        (WHISPER_MODEL, "Whisper model"),
        (PIPER_MODEL,   "Piper model")
    ]:
        if not os.path.exists(os.path.expanduser(path)):
            print(f"{label} not found: {path}")
            sys.exit(1)

    listen_and_respond()