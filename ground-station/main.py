"""
ORNITHOPTER — Estação de Solo (Raspberry Pi 4)

Seguimento por visão (OpenCV/ArUco) + PID externo + máquina de estados.
Envia setpoints ao ESP32 (firmware esp-drone) por UDP, protocolo estilo CRTP.

Executar na RPi:
    pip install fastapi uvicorn opencv-contrib-python numpy
    uvicorn main:app --host 0.0.0.0 --port 8000

Painel: http://<ip-da-rpi>:8000
"""
from __future__ import annotations

import asyncio
import math
import threading
import time
import socket
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket
from fastapi.responses import StreamingResponse, HTMLResponse

# ============================ Configuração ============================

DRONE_IP = "192.168.4.1"      # IP do AP do ESP32 (esp-drone)
DRONE_PORT = 2390             # porta UDP de comandos (padrão esp-drone)
MARKER_MM = 40.0              # lado real do marcador ArUco (mm)
CAM_INDEX = 0                 # índice da câmara (CSI=0, USB pode ser 1)
TARGET_ALT_MM = 500.0         # altitude alvo (mm)
MAX_ALT_MM = 1500.0           # geofence
MAX_XY_MM = 1000.0            # geofence
LOST_TIMEOUT_S = 1.0          # perdeu o marcador > 1 s → LAND automático
BATT_LOW_V = 3.4

# ============================ Estado partilhado ============================


class Mode(str, Enum):
    IDLE = "IDLE"
    TAKEOFF = "TAKEOFF"
    HOVER = "HOVER"
    GOTO = "GOTO"
    LAND = "LAND"
    EMERGENCY = "EMERGENCY"


@dataclass
class DroneState:
    x_mm: float = 0.0
    y_mm: float = 0.0
    z_mm: float = 0.0
    yaw_deg: float = 0.0
    roll_deg: float = 0.0        # da telemetria do IMU (CRTP)
    pitch_deg: float = 0.0
    battery_v: float = 0.0
    lost: bool = True
    last_seen: float = field(default_factory=time.time)
    mode: Mode = Mode.IDLE
    target: tuple = (0.0, 0.0, TARGET_ALT_MM)


STATE = DroneState()
LOCK = threading.Lock()
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ============================ PID simples ============================


class PID:
    def __init__(self, kp: float, ki: float, kd: float, limit: float):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.limit = limit
        self._i = 0.0
        self._prev = None

    def update(self, error: float, dt: float) -> float:
        self._i = max(-self.limit, min(self.limit, self._i + error * dt))
        d = 0.0 if self._prev is None else (error - self._prev) / dt
        self._prev = error
        out = self.kp * error + self.ki * self._i + self.kd * d
        return max(-self.limit, min(self.limit, out))


pid_x = PID(0.06, 0.01, 0.03, limit=8.0)     # graus de pitch desejados
pid_y = PID(0.06, 0.01, 0.03, limit=8.0)     # graus de roll desejados
pid_z = PID(0.0009, 0.0003, 0.0004, limit=6.0)  # thrust extra


# ============================ Visão (ArUco) ============================


def open_camera():
    cap = cv2.VideoCapture(CAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
    cap.set(cv2.CAP_PROP_FPS, 30)
    return cap


def detect_marker(frame):
    """Devolve (rvecs, tvecs, corners) ou (None, None, None)."""
    aruco = cv2.aruco
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = aruco.detectMarkers(gray, dictionary)
    if ids is None:
        return None, None, None
    rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
        corners, MARKER_MM)  # tvecs em mm (eixo z = distância à câmara)
    return rvecs, tvecs, corners[0][0]


def marker_yaw(corners) -> float:
    """Yaw aproximado a partir da orientação do quadrilátero detetado."""
    pts = np.array(corners, dtype=np.float32)
    top = (pts[0] + pts[1]) / 2
    bottom = (pts[3] + pts[2]) / 2
    return math.degrees(math.atan2((bottom - top)[0], (bottom - top)[1]))


def vision_loop():
    global STATE
    cap = open_camera()
    objp = np.array([[-MARKER_MM/2, MARKER_MM/2, 0], [MARKER_MM/2, MARKER_MM/2, 0],
                     [MARKER_MM/2, -MARKER_MM/2, 0], [-MARKER_MM/2, -MARKER_MM/2, 0]],
                    dtype=np.float32)
    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.05)
            continue
        rvecs, tvecs, corners = detect_marker(frame)
        now = time.time()
        with LOCK:
            if tvecs is not None:
                t = tvecs[0][0]
                STATE.x_mm, STATE.y_mm, STATE.z_mm = float(t[0]), float(-t[1]), float(t[2])
                STATE.yaw_deg = marker_yaw(corners)
                STATE.last_seen = now
                STATE.lost = False
            else:
                if now - STATE.last_seen > LOST_TIMEOUT_S:
                    STATE.lost = True
        time.sleep(0.01)


# ============================ Controlo ============================


def send_setpoints(roll: float, pitch: float, thrust: float, yawrate: float):
    """Pacote estilo CRTP simplificado — ajustar ao formato do esp-drone."""
    payload = f"SP,{roll:.2f},{pitch:.2f},{thrust:.2f},{yawrate:.2f}\n"
    sock.sendto(payload.encode(), (DRONE_IP, DRONE_PORT))


def control_loop():
    global STATE
    last = time.time()
    while True:
        now = time.time()
        dt = max(1e-3, now - last)
        last = now
        with LOCK:
            s = STATE
            if s.mode == Mode.EMERGENCY:
                send_setpoints(0, 0, 0, 0)
                continue
            if s.lost and s.mode != Mode.IDLE:
                s.mode = Mode.LAND
            tgt_x, tgt_y, tgt_z = s.target
            if s.mode == Mode.TAKEOFF:
                if s.z_mm >= tgt_z * 0.95:
                    s.mode = Mode.HOVER
            elif s.mode == Mode.LAND:
                tgt_z = 0.0
                if s.z_mm <= 20.0:
                    s.mode = Mode.IDLE
                    send_setpoints(0, 0, 0, 0)
                    continue
            elif s.mode == Mode.GOTO and math.hypot(s.x_mm - tgt_x, s.y_mm - tgt_y) < 40:
                s.mode = Mode.HOVER
            # geofence
            tgt_x = max(-MAX_XY_MM, min(MAX_XY_MM, tgt_x))
            tgt_z = min(MAX_ALT_MM, tgt_z)
            ex, ey = s.x_mm - tgt_x, s.y_mm - tgt_y
            ez = s.z_mm - tgt_z
            hover_thrust = 48.0  # % (~razão empuxo/peso 2 => hover ~50%)
            thrust = max(0.0, min(100.0, hover_thrust - pid_z.update(ez, dt)))
            pitch_cmd = pid_x.update(ex, dt)
            roll_cmd = pid_y.update(ey, dt)
            yawrate = max(-90.0, min(90.0, -0.8 * s.yaw_deg))
            if s.mode in (Mode.TAKEOFF, Mode.HOVER, Mode.GOTO, Mode.LAND):
                send_setpoints(roll_cmd, pitch_cmd, thrust, yawrate)
        time.sleep(0.03)  # ~30 Hz loop externo


# ============================ FastAPI ============================

app = FastAPI(title="Ornithopter Ground Station")

PANEL = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Ornithopter GS</title>
<style>body{background:#14100b;color:#e8dcc8;font-family:system-ui;padding:24px}
h1{color:#e8a765;letter-spacing:.3em;font-weight:200}button{background:#ff7b24;color:#14100b;
border:0;padding:10px 18px;margin:6px;border-radius:6px;font-weight:700;cursor:pointer}
#telem{white-space:pre;background:#1e1810;border:1px solid #3a2f22;border-radius:8px;padding:14px;margin-top:14px}</style>
</head><body><h1>ORNITHOPTER — GROUND STATION</h1>
<button onclick="fetch('/takeoff',{method:'POST'})">TAKEOFF</button>
<button onclick="fetch('/land',{method:'POST'})">LAND</button>
<button onclick="fetch('/emergency',{method:'POST'})" style="background:#c43d3d">EMERGENCY</button>
<div id="telem">a ligar…</div>
<script>const t=document.getElementById('telem');const ws=new WebSocket(`ws://${location.host}/ws/telemetry`);
ws.onmessage=e=>t.textContent=e.data;</script></body></html>"""


@app.on_event("startup")
def startup():
    threading.Thread(target=vision_loop, daemon=True).start()
    threading.Thread(target=control_loop, daemon=True).start()


@app.get("/", response_class=HTMLResponse)
def panel():
    return PANEL


@app.post("/takeoff")
def takeoff():
    with LOCK:
        STATE.target = (0.0, 0.0, TARGET_ALT_MM)
        STATE.mode = Mode.TAKEOFF
    return {"mode": STATE.mode}


@app.post("/land")
def land():
    with LOCK:
        STATE.mode = Mode.LAND
    return {"mode": STATE.mode}


@app.post("/goto")
def goto(x: float = 0.0, y: float = 0.0, z: float = TARGET_ALT_MM):
    with LOCK:
        STATE.target = (x, y, z)
        STATE.mode = Mode.GOTO
    return {"mode": STATE.mode, "target": STATE.target}


@app.post("/emergency")
def emergency():
    with LOCK:
        STATE.mode = Mode.EMERGENCY
    send_setpoints(0, 0, 0, 0)
    return {"mode": STATE.mode}


@app.websocket("/ws/telemetry")
async def telemetry(ws: WebSocket):
    await ws.accept()
    while True:
        with LOCK:
            s = STATE
            msg = (f"modo={s.mode.value}  pos=({s.x_mm:.0f}, {s.y_mm:.0f}, {s.z_mm:.0f}) mm\n"
                   f"yaw={s.yaw_deg:.1f}°  roll={s.roll_deg:.1f}°  pitch={s.pitch_deg:.1f}°\n"
                   f"bateria={s.battery_v:.2f} V  marcador={'OK' if not s.lost else 'PERDIDO'}")
        await ws.send_text(msg)
        await asyncio.sleep(0.2)
