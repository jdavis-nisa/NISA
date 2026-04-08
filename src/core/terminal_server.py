#!/usr/bin/env python3.11
"""
NISA Terminal Server - Port 8091
WebSocket bridge between browser xterm.js and Kali Linux msfconsole
Uses PTY for proper terminal emulation
"""
import os
import asyncio
import websockets
import subprocess
import pty
import json
import select
import fcntl
import termios
import struct
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/NISA/.env"))

NISA_API_KEY = os.environ.get("NISA_API_KEY", "")
KALI_CONTAINER = "kali_nisa"

async def handle_terminal(websocket):
    try:
        auth_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
        auth_data = json.loads(auth_msg)
        if NISA_API_KEY and auth_data.get("key") != NISA_API_KEY:
            await websocket.send(json.dumps({"type": "error", "data": "Invalid API key\r\n"}))
            return
    except Exception:
        return

    tool = auth_data.get("tool", "msfconsole")

    tool_commands = {
        "msfconsole": ["docker", "exec", "-it", KALI_CONTAINER, "msfconsole"],
        "bash": ["docker", "exec", "-it", KALI_CONTAINER, "bash"],
    }

    cmd = tool_commands.get(tool, tool_commands["msfconsole"])

    await websocket.send(json.dumps({
        "type": "output",
        "data": f"\r\n\033[33mNISA Terminal - Kali Linux\033[0m\r\n\033[90mStarting {tool}...\033[0m\r\n"
    }))

    # Create PTY
    master_fd, slave_fd = pty.openpty()

    # Set terminal size
    winsize = struct.pack("HHHH", 40, 200, 0, 0)
    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)

    process = subprocess.Popen(
        cmd,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        close_fds=True,
    )
    os.close(slave_fd)

    loop = asyncio.get_event_loop()
    stop = asyncio.Event()

    async def read_pty():
        while not stop.is_set():
            try:
                r, _, _ = await loop.run_in_executor(
                    None, select.select, [master_fd], [], [], 0.1
                )
                if r:
                    data = os.read(master_fd, 4096)
                    if data:
                        await websocket.send(json.dumps({
                            "type": "output",
                            "data": data.decode("utf-8", errors="replace")
                        }))
                if process.poll() is not None:
                    stop.set()
            except Exception:
                stop.set()
                break

    async def read_ws():
        try:
            async for message in websocket:
                try:
                    msg = json.loads(message)
                    if msg.get("type") == "input":
                        os.write(master_fd, msg["data"].encode())
                    elif msg.get("type") == "resize":
                        cols = msg.get("cols", 200)
                        rows = msg.get("rows", 40)
                        winsize = struct.pack("HHHH", rows, cols, 0, 0)
                        fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
                except Exception:
                    pass
        except Exception:
            pass
        stop.set()

    await asyncio.gather(read_pty(), read_ws(), return_exceptions=True)

    process.terminate()
    try:
        process.wait(timeout=3)
    except Exception:
        process.kill()
    try:
        os.close(master_fd)
    except Exception:
        pass

async def main():
    print("Starting NISA Terminal Server on port 8091...")
    async with websockets.serve(
        handle_terminal, "127.0.0.1", 8091,
        ping_interval=30, ping_timeout=10,
    ):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
