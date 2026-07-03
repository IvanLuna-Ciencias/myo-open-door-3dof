#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Myo demo (puertas abiertas): HOMBRO (IMU tilt) + CODO (EMG amplitud) + ROT exo (quat, eje fijo) -> 3 setpoints a LabVIEW (UDP)

- Hombro flex/ext: IMU (event.acceleration) -> tilt por gravedad (on_orientation ~50 Hz)
- Codo flex/ext: EMG (8ch) -> RMS envelope normalizado (rest vs max) -> ángulo 0..ELB_MAX

UDP payload a LabVIEW:
    "<q_shoulder_rad>,<q_elbow_rad>,<q_rot_rad>\\n"

Calibración (2 etapas):
1) Etapa 1/2: brazo abajo RELAJADO ~2 s  -> tilt0 + emg_rest
2) Etapa 2/2: flexiona bíceps fuerte ~2 s -> emg_max (percentil 95)
   * Cierra por EMG (n_max) y/o por tiempo real (robusto)

Teclas:
- R     = recalibrar completo
- Space = HOLD (congela setpoints)
- Esc   = detener

Ajustes rápidos:
- Si hombro va al revés: cambia SIGN_SHO a +1/-1
- Si tilt correcto no es z: cambia TILT_AXIS a tilt_x/tilt_y
"""

import sys, os, re, csv, json, datetime, math, socket, time, argparse
from pathlib import Path
from threading import Lock
from collections import deque

import myo
from myo import UnlockType, LockingPolicy, VibrationType

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QKeySequence
import pyqtgraph as pg
import numpy as np

# ========= CONFIG FIJA (sin prompts) =========
SDK_PATH = os.environ.get(
    "MYO_SDK_PATH",
    r"C:\Users\Ivan Luna\Downloads\myo-sdk-win-0.9.0\myo-sdk-win-0.9.0"
)

BASE_DIR = Path("Myo_PuertasAbiertas_3DOF")
USUARIO = "puertas_abiertas"
EJERCICIO = "demo_3dof"
NOTAS = ""

LV_HOST = "172.22.11.2"
LV_PORT = 5005
LV_ENABLED = True

# ========= Parámetros demo =========
IMU_FS = 50.0

# hombro flex/ext
TILT_AXIS = "tilt_z"
SIGN_SHO = -1          # (hacia adelante bajaba) -> invertimos
SHO_MIN_DEG, SHO_MAX_DEG = -20.0,  140.0            #------------------------------------------------------------------------------------------------

# codo por EMG amplitude
ELB_MIN_DEG, ELB_MAX_DEG = 0.0, 100.0               #------------------------------------------------------------------------------------------------

# rotación de hombro (twist) por quaternion (una sola Myo)
# NOTA: ARM_AXIS_LOCAL define el eje longitudinal del brazo en el marco del sensor Myo.
# Si la rotación sale rara/invertida, probar (1,0,0) o (0,0,1) o cambiar SIGN_ROT.
ROBOT_AXIS_WORLD = (0.0, 0.0, 1.0)  # eje FIJO del motor de rotación del exo en marco 'global' (ajustar: (1,0,0)/(0,1,0)/(0,0,1))
SIGN_ROT = -1.0                    # invertir si rota al revés
ROT_MIN_DEG = -40.0                # límites del motor (deg)
ROT_MAX_DEG = 40.0                 # límites del motor (deg)
TAU_ROT_SEC = 0.20                # suavizado setpoint rotación
DEADBAND_ROT_DEG = 0.8
RATE_ROT_DPS = 180.0



CALIB_SEC = 2.0         # duración de cada etapa

# filtros (tau)
TAU_G_SEC   = 0.60      # gravedad
TAU_SHO_SEC = 0.22      # hombro setpoint
TAU_EMG_SEC = 0.15      # envelope EMG (a 200 Hz)
TAU_ELB_SEC = 0.20      # codo setpoint

# robustez
DEADBAND_SHO_DEG = 0.6
DEADBAND_ELB_DEG = 0.6
RATE_SHO_DPS = 120.0
RATE_ELB_DPS = 220.0

# ========= CONFIG FILE SUPPORT =========
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "configs" / "demo_3dof.json"

FLUSH_EVERY = 50
PLOT_RING_LEN = 1500
PLOT_WINDOW_SEC = 12.0
PLOT_UPDATE_MS = 50


def load_config(config_path=None):
    """Load JSON configuration file. If it does not exist, keep script defaults."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    if not path.exists():
        print(f"[WARN] Config file not found: {path}. Using script defaults.", flush=True)
        return {}, path

    with open(path, "r", encoding="utf-8-sig") as f:
        cfg = json.load(f)

    return cfg, path


def apply_config(cfg):
    """Apply configuration values to the existing global parameters."""
    global SDK_PATH, BASE_DIR, USUARIO, EJERCICIO, NOTAS
    global LV_HOST, LV_PORT, LV_ENABLED
    global IMU_FS
    global TILT_AXIS, SIGN_SHO, SHO_MIN_DEG, SHO_MAX_DEG
    global ELB_MIN_DEG, ELB_MAX_DEG
    global ROBOT_AXIS_WORLD, SIGN_ROT, ROT_MIN_DEG, ROT_MAX_DEG
    global TAU_ROT_SEC, DEADBAND_ROT_DEG, RATE_ROT_DPS
    global CALIB_SEC
    global TAU_G_SEC, TAU_SHO_SEC, TAU_EMG_SEC, TAU_ELB_SEC
    global DEADBAND_SHO_DEG, DEADBAND_ELB_DEG, RATE_SHO_DPS, RATE_ELB_DPS
    global FLUSH_EVERY, PLOT_RING_LEN, PLOT_WINDOW_SEC, PLOT_UPDATE_MS

    myo_cfg = cfg.get("myo", {})
    sdk_path_env = myo_cfg.get("sdk_path_env", "MYO_SDK_PATH")
    default_sdk_path = myo_cfg.get("default_sdk_path", SDK_PATH)
    SDK_PATH = os.environ.get(sdk_path_env, default_sdk_path)
    IMU_FS = float(myo_cfg.get("imu_fs_hz", IMU_FS))

    session_cfg = cfg.get("session", {})
    BASE_DIR = Path(session_cfg.get("base_dir", str(BASE_DIR)))
    USUARIO = session_cfg.get("user", USUARIO)
    EJERCICIO = session_cfg.get("exercise", EJERCICIO)
    NOTAS = session_cfg.get("notes", NOTAS)

    lv_cfg = cfg.get("labview", {})
    LV_HOST = lv_cfg.get("host", LV_HOST)
    LV_PORT = int(lv_cfg.get("port", LV_PORT))
    LV_ENABLED = bool(lv_cfg.get("enabled", LV_ENABLED))

    cal_cfg = cfg.get("calibration", {})
    CALIB_SEC = float(cal_cfg.get("duration_sec", CALIB_SEC))

    shoulder_cfg = cfg.get("shoulder", {})
    TILT_AXIS = shoulder_cfg.get("tilt_axis", TILT_AXIS)
    SIGN_SHO = float(shoulder_cfg.get("sign", SIGN_SHO))
    SHO_MIN_DEG = float(shoulder_cfg.get("min_deg", SHO_MIN_DEG))
    SHO_MAX_DEG = float(shoulder_cfg.get("max_deg", SHO_MAX_DEG))
    TAU_G_SEC = float(shoulder_cfg.get("tau_gravity_sec", TAU_G_SEC))
    TAU_SHO_SEC = float(shoulder_cfg.get("tau_setpoint_sec", TAU_SHO_SEC))
    DEADBAND_SHO_DEG = float(shoulder_cfg.get("deadband_deg", DEADBAND_SHO_DEG))
    RATE_SHO_DPS = float(shoulder_cfg.get("rate_limit_dps", RATE_SHO_DPS))

    elbow_cfg = cfg.get("elbow", {})
    ELB_MIN_DEG = float(elbow_cfg.get("min_deg", ELB_MIN_DEG))
    ELB_MAX_DEG = float(elbow_cfg.get("max_deg", ELB_MAX_DEG))
    TAU_EMG_SEC = float(elbow_cfg.get("tau_emg_sec", TAU_EMG_SEC))
    TAU_ELB_SEC = float(elbow_cfg.get("tau_setpoint_sec", TAU_ELB_SEC))
    DEADBAND_ELB_DEG = float(elbow_cfg.get("deadband_deg", DEADBAND_ELB_DEG))
    RATE_ELB_DPS = float(elbow_cfg.get("rate_limit_dps", RATE_ELB_DPS))

    rotation_cfg = cfg.get("rotation", {})
    ROBOT_AXIS_WORLD = tuple(rotation_cfg.get("robot_axis_world", ROBOT_AXIS_WORLD))
    SIGN_ROT = float(rotation_cfg.get("sign", SIGN_ROT))
    ROT_MIN_DEG = float(rotation_cfg.get("min_deg", ROT_MIN_DEG))
    ROT_MAX_DEG = float(rotation_cfg.get("max_deg", ROT_MAX_DEG))
    TAU_ROT_SEC = float(rotation_cfg.get("tau_setpoint_sec", TAU_ROT_SEC))
    DEADBAND_ROT_DEG = float(rotation_cfg.get("deadband_deg", DEADBAND_ROT_DEG))
    RATE_ROT_DPS = float(rotation_cfg.get("rate_limit_dps", RATE_ROT_DPS))

    logging_cfg = cfg.get("logging", {})
    FLUSH_EVERY = int(logging_cfg.get("flush_every_samples", FLUSH_EVERY))

    plot_cfg = cfg.get("plot", {})
    PLOT_RING_LEN = int(plot_cfg.get("ring_length_samples", PLOT_RING_LEN))
    PLOT_WINDOW_SEC = float(plot_cfg.get("window_sec", PLOT_WINDOW_SEC))
    PLOT_UPDATE_MS = int(plot_cfg.get("update_ms", PLOT_UPDATE_MS))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Myo Open Door 3DOF Demo: Myo IMU/EMG to LabVIEW UDP setpoints."
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to the JSON configuration file."
    )
    return parser.parse_args()

# -------------------- utils --------------------
def sanitize_name(s: str) -> str:
    s = (s or "").strip().lower().replace(" ", "_")
    s = re.sub(r"[^a-z0-9_\-]+", "", s)
    return s or "na"

def next_series_for(user_s: str, ex_s: str) -> int:
    dir_path = BASE_DIR / user_s / ex_s
    dir_path.mkdir(parents=True, exist_ok=True)
    max_n = 0
    for f in dir_path.glob("*.csv"):
        m = re.search(r"_serie(\d+)_", f.name)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1

def alpha_from_tau(dt: float, tau: float) -> float:
    return dt / (tau + dt)

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def deadband(delta, band):
    return 0.0 if abs(delta) < band else delta

def rate_limit(prev, x, max_rate_dps, dt):
    max_delta = max_rate_dps * dt
    d = x - prev
    if d > max_delta:
        return prev + max_delta
    if d < -max_delta:
        return prev - max_delta
    return x

def tilt_from_g(gx, gy, gz):
    eps = 1e-12
    tilt_x = math.degrees(math.atan2(gx, math.sqrt(gy*gy + gz*gz) + eps))
    tilt_y = math.degrees(math.atan2(gy, math.sqrt(gx*gx + gz*gz) + eps))
    tilt_z = math.degrees(math.atan2(gz, math.sqrt(gx*gx + gy*gy) + eps))
    return {"tilt_x": tilt_x, "tilt_y": tilt_y, "tilt_z": tilt_z}


def quat_conj(q):
    x, y, z, w = q
    return (-x, -y, -z, w)

def quat_mul(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 - x1*z2 + y1*w2 + z1*x2
    z = w1*z2 + x1*y2 - y1*x2 + z1*w2
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    return (x, y, z, w)

def quat_norm(q):
    x, y, z, w = q
    return math.sqrt(x*x + y*y + z*z + w*w)

def quat_normalize(q):
    n = quat_norm(q)
    if n < 1e-12:
        return (0.0, 0.0, 0.0, 1.0)
    x, y, z, w = q
    return (x/n, y/n, z/n, w/n)

def vec_dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def vec_norm(v):
    return math.sqrt(vec_dot(v, v))

def vec_scale(v, s):
    return (v[0]*s, v[1]*s, v[2]*s)

def twist_angle_deg(q_rel, axis_local):
    q_rel = quat_normalize(q_rel)
    ax = axis_local
    an = vec_norm(ax)
    if an < 1e-9:
        ax = (0.0, 1.0, 0.0)
        an = 1.0
    ax = (ax[0]/an, ax[1]/an, ax[2]/an)

    x, y, z, w = q_rel
    v = (x, y, z)
    proj = vec_scale(ax, vec_dot(v, ax))
    q_twist = (proj[0], proj[1], proj[2], w)
    q_twist = quat_normalize(q_twist)

    tx, ty, tz, tw = q_twist
    vmag = math.sqrt(tx*tx + ty*ty + tz*tz)
    ang = 2.0 * math.atan2(vmag, max(1e-12, tw))
    sign = 1.0
    if (tx*ax[0] + ty*ax[1] + tz*ax[2]) < 0:
        sign = -1.0
    return math.degrees(ang) * sign

def unwrap_deg(prev_deg, new_deg):
    d = new_deg - prev_deg
    while d > 180.0:
        new_deg -= 360.0
        d = new_deg - prev_deg
    while d < -180.0:
        new_deg += 360.0
        d = new_deg - prev_deg
    return new_deg


# -------------------- LabVIEW UDP --------------------
class LVUDPSender:
    def __init__(self, host: str, port: int, enabled: bool = True):
        self.host = host
        self.port = int(port)
        self.enabled = bool(enabled)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, q_sh_rad: float, q_elb_rad: float, q_rot_rad: float):
        if not self.enabled:
            return
        msg = f"{q_sh_rad:.6f},{q_elb_rad:.6f},{q_rot_rad:.6f}\n".encode("utf-8")
        self.sock.sendto(msg, (self.host, self.port))

# ================== LISTENER ==================
class IMUEMGCollector(myo.DeviceListener):
    def __init__(self, csv_writer, csv_file, lv_sender: LVUDPSender, ring_len=None, flush_every=None):
        super().__init__()
        if ring_len is None:
            ring_len = PLOT_RING_LEN
        if flush_every is None:
            flush_every = FLUSH_EVERY
        self.csv_writer = csv_writer
        self.csv_file = csv_file
        self.lv_sender = lv_sender
        self.flush_every = int(flush_every)

        self.fs_imu = float(IMU_FS)
        self.dt = 1.0 / self.fs_imu

        # hombro config
        self.tilt_axis = TILT_AXIS
        self.sign_sho = float(SIGN_SHO)
        self.sho_min_deg = float(SHO_MIN_DEG)
        self.sho_max_deg = float(SHO_MAX_DEG)

        self.alpha_g = alpha_from_tau(self.dt, TAU_G_SEC)
        self.alpha_sho = alpha_from_tau(self.dt, TAU_SHO_SEC)

        # codo config
        self.elb_min_deg = float(ELB_MIN_DEG)
        self.elb_max_deg = float(ELB_MAX_DEG)
        self.alpha_emg = alpha_from_tau(1.0/200.0, TAU_EMG_SEC)  # EMG ~200 Hz
        self.alpha_elb = alpha_from_tau(self.dt, TAU_ELB_SEC)

        # filtros + robustez
        self.deadband_sho = float(DEADBAND_SHO_DEG)
        self.deadband_elb = float(DEADBAND_ELB_DEG)
        self.deadband_rot = float(DEADBAND_ROT_DEG)
        self.rate_sho_dps = float(RATE_SHO_DPS)
        self.rate_elb_dps = float(RATE_ELB_DPS)
        self.rate_rot_dps = float(RATE_ROT_DPS)
        self.alpha_rot = alpha_from_tau(self.dt, TAU_ROT_SEC)
        self.robot_axis_world = ROBOT_AXIS_WORLD
        self.sign_rot = float(SIGN_ROT)

        # estado gravedad
        self.gx = 0.0; self.gy = 0.0; self.gz = 0.0

        # setpoints
        self.sho_lp = 0.0; self.sho_out = 0.0
        self.elb_lp = 0.0; self.elb_out = 0.0
        self.rot_lp = 0.0; self.rot_out = 0.0
        self.rot_unwrapped = 0.0

        # EMG envelope
        self.emg_env = 0.0

        # calibración
        self.calib_sec = float(CALIB_SEC)
        self._calib_samples_needed = int(self.calib_sec * self.fs_imu)

        self._calib_stage = 0   # 0=rest, 1=max, 2=ready
        self._stage1_start_time = None

        self._calib_vals_tilt = []
        self._calib_vals_quat = []
        self._calib_vals_emg_rest = []
        self._calib_vals_emg_max = []

        self.tilt0 = 0.0
        self.q0 = (0.0, 0.0, 0.0, 1.0)
        self.emg_rest = 0.0
        self.emg_max = 1.0

        self.is_ready = False
        self.hold = False

        # ring buffers plot
        self.lock = Lock()
        self.t_ring = deque(maxlen=ring_len)
        self.sho_ring = deque(maxlen=ring_len)
        self.elb_ring = deque(maxlen=ring_len)
        self.rot_ring = deque(maxlen=ring_len)
        self.emg_ring = deque(maxlen=ring_len)

        self.samples_written = 0
        self.imu_index = 0
        self.device = None

    def on_connected(self, event):
        self.device = event.device
        try:
            event.device.unlock(UnlockType.hold)
        except Exception:
            pass
        try:
            event.device.stream_emg(True)
        except Exception:
            pass
        try:
            event.device.vibrate(VibrationType.short)
        except Exception:
            pass
        print("[INFO] Myo conectado.", flush=True)
        print("[CAL] Etapa 1/2: brazo abajo RELAJADO ~2 s (hombro 0° + EMG base).", flush=True)

    def on_disconnected(self, event):
        print("[INFO] Myo desconectado.", flush=True)

    def toggle_hold(self):
        self.hold = not self.hold
        print("[INFO] HOLD:", self.hold, flush=True)

    def request_recenter(self):
        self._calib_stage = 0
        self._stage1_start_time = None
        self._calib_vals_tilt.clear()
        self._calib_vals_emg_rest.clear()
        self._calib_vals_emg_max.clear()
        self._calib_vals_quat.clear()
        self.rot_lp = 0.0; self.rot_out = 0.0; self.rot_unwrapped = 0.0
        self.is_ready = False
        print("[CAL] Reiniciando calibración.", flush=True)
        print("[CAL] Etapa 1/2: brazo abajo RELAJADO ~2 s (hombro 0° + EMG base).", flush=True)

    def _finish_stage2(self):
        vals = np.array(self._calib_vals_emg_max, dtype=float) if self._calib_vals_emg_max else np.array([self.emg_env], dtype=float)
        self.emg_max = float(np.percentile(vals, 95))
        if self.emg_max <= self.emg_rest + 1e-6:
            self.emg_max = self.emg_rest + 1.0
        self._calib_stage = 2
        self.is_ready = True
        print(f"[CAL] OK etapa 2. emg_max≈{self.emg_max:.2f}  -> listo", flush=True)
        print("[INFO] Control activo. Teclas: R=recenter | Space=hold | Esc=stop", flush=True)

    def on_emg(self, event):
        try:
            emg = list(event.emg)  # 8 ints
        except Exception:
            return

        rms = math.sqrt(sum((float(v) ** 2 for v in emg)) / max(1, len(emg)))
        self.emg_env = self.emg_env + self.alpha_emg * (rms - self.emg_env)

        if self._calib_stage == 0:
            self._calib_vals_emg_rest.append(self.emg_env)

        elif self._calib_stage == 1:
            self._calib_vals_emg_max.append(self.emg_env)

            # cierre robusto por EMG + tiempo (no depende de IMU)
            if self._stage1_start_time is None:
                self._stage1_start_time = time.time()

            elapsed = time.time() - self._stage1_start_time
            need_emg = int(200.0 * self.calib_sec * 0.7)  # ~70% de 2s a 200Hz
            have_emg = len(self._calib_vals_emg_max)

            if have_emg >= max(50, need_emg) and elapsed >= (self.calib_sec * 0.5):
                self._finish_stage2()

    def _update_calibration_stage0(self, tilt_deg: float, quat_xyzw):
        # acumula tilt, quaternion y EMG rest
        self._calib_vals_tilt.append(tilt_deg)
        self._calib_vals_quat.append(quat_xyzw)
        if len(self._calib_vals_tilt) >= self._calib_samples_needed:
            self.tilt0 = float(sum(self._calib_vals_tilt) / len(self._calib_vals_tilt))
            self.emg_rest = float(sum(self._calib_vals_emg_rest) / max(1, len(self._calib_vals_emg_rest)))
            qs = np.array(self._calib_vals_quat, dtype=float) if self._calib_vals_quat else np.array([[0,0,0,1]], dtype=float)
            q_mean = qs.mean(axis=0)
            q_mean = q_mean / (np.linalg.norm(q_mean) + 1e-12)
            self.q0 = (float(q_mean[0]), float(q_mean[1]), float(q_mean[2]), float(q_mean[3]))
            self._calib_stage = 1
            self._stage1_start_time = time.time()
            self._calib_vals_emg_max.clear()

            print(f"[CAL] OK etapa 1. tilt0={self.tilt0:.2f} deg | emg_rest={self.emg_rest:.2f}", flush=True)
            print("[CAL] Etapa 2/2: FLEXIONA bíceps fuerte (sin mover hombro) ~2 s para EMG max.", flush=True)

    def on_orientation(self, event):
        t_rel = self.imu_index / self.fs_imu
        self.imu_index += 1

        o = event.orientation
        quat = (float(o.x), float(o.y), float(o.z), float(o.w))
        a = event.acceleration 
        g = event.gyroscope

        # gravedad LPF
        self.gx = self.gx + self.alpha_g * (float(a.x) - self.gx)
        self.gy = self.gy + self.alpha_g * (float(a.y) - self.gy)
        self.gz = self.gz + self.alpha_g * (float(a.z) - self.gz)

        tilt_deg = tilt_from_g(self.gx, self.gy, self.gz)[self.tilt_axis]

        if not self.is_ready:
            if self._calib_stage == 0:
                self._update_calibration_stage0(tilt_deg, quat)

            raw_sho = self.sign_sho * (tilt_deg - self.tilt0)

                        # ---- Rotación hombro (eje FIJO del exoesqueleto) desde quaternion ----
            # Interpretación: el 3er DOF es giro alrededor del eje del motor del exo (fijo), NO rotación anatómica del húmero.
            q_rel = quat_mul(quat_conj(self.q0), quat)
            raw_rot = self.sign_rot * twist_angle_deg(q_rel, self.robot_axis_world)
            self.rot_unwrapped = unwrap_deg(self.rot_unwrapped, raw_rot)

            if not self.hold:
                dr = self.rot_unwrapped - self.rot_lp
                rot_db = self.rot_lp + deadband(dr, self.deadband_rot)
                self.rot_lp = self.rot_lp + self.alpha_rot * (rot_db - self.rot_lp)

                rot_clamped = clamp(self.rot_lp, ROT_MIN_DEG, ROT_MAX_DEG)
                self.rot_out = rate_limit(self.rot_out, rot_clamped, self.rate_rot_dps, self.dt)

            q_sh_rad = math.radians(self.sho_out)
            q_elb_rad = math.radians(self.elb_out)
            q_rot_rad = math.radians(self.rot_out)

        else:
            # ---- Hombro ----
            raw_sho = self.sign_sho * (tilt_deg - self.tilt0)
            if not self.hold:
                ds = raw_sho - self.sho_lp
                sho_db = self.sho_lp + deadband(ds, self.deadband_sho)
                self.sho_lp = self.sho_lp + self.alpha_sho * (sho_db - self.sho_lp)
                sho_clamped = clamp(self.sho_lp, self.sho_min_deg, self.sho_max_deg)
                self.sho_out = rate_limit(self.sho_out, sho_clamped, self.rate_sho_dps, self.dt)

            # ---- Codo desde EMG amplitude ----
            u = (self.emg_env - self.emg_rest) / (self.emg_max - self.emg_rest + 1e-9)
            u = clamp(u, 0.0, 1.0)
            raw_elb = self.elb_min_deg + u * (self.elb_max_deg - self.elb_min_deg)

            if not self.hold:
                de = raw_elb - self.elb_lp
                elb_db = self.elb_lp + deadband(de, self.deadband_elb)
                self.elb_lp = self.elb_lp + self.alpha_elb * (elb_db - self.elb_lp)
                elb_clamped = clamp(self.elb_lp, self.elb_min_deg, self.elb_max_deg)
                self.elb_out = rate_limit(self.elb_out, elb_clamped, self.rate_elb_dps, self.dt)


                        # ---- Rotación hombro (eje FIJO del exoesqueleto) desde quaternion ----
            # Interpretación: el 3er DOF es giro alrededor del eje del motor del exo (fijo), NO rotación anatómica del húmero.
            q_rel = quat_mul(quat_conj(self.q0), quat)
            raw_rot = self.sign_rot * twist_angle_deg(q_rel, self.robot_axis_world)
            self.rot_unwrapped = unwrap_deg(self.rot_unwrapped, raw_rot)

            if not self.hold:
                dr = self.rot_unwrapped - self.rot_lp
                rot_db = self.rot_lp + deadband(dr, self.deadband_rot)
                self.rot_lp = self.rot_lp + self.alpha_rot * (rot_db - self.rot_lp)

                rot_clamped = clamp(self.rot_lp, ROT_MIN_DEG, ROT_MAX_DEG)
                self.rot_out = rate_limit(self.rot_out, rot_clamped, self.rate_rot_dps, self.dt)

            q_sh_rad = math.radians(self.sho_out)
            q_elb_rad = math.radians(self.elb_out)
            q_rot_rad = math.radians(self.rot_out)

            if (not self.hold) and self.lv_sender is not None:
                try:
                    self.lv_sender.send(q_sh_rad, q_elb_rad, q_rot_rad)
                except Exception:
                    pass

        # CSV row
        row = [
            f"{t_rel:.6f}",
            f"{float(o.x):.8f}", f"{float(o.y):.8f}", f"{float(o.z):.8f}", f"{float(o.w):.8f}",
            f"{float(a.x):.6f}", f"{float(a.y):.6f}", f"{float(a.z):.6f}",
            f"{float(g.x):.6f}", f"{float(g.y):.6f}", f"{float(g.z):.6f}",
            f"{tilt_deg:.3f}", f"{raw_sho:.3f}",
            f"{self.emg_env:.3f}",
            f"{q_sh_rad:.6f}", f"{q_elb_rad:.6f}", f"{q_rot_rad:.6f}",
        ]
        self.csv_writer.writerow(row)
        self.samples_written += 1
        if (self.samples_written % self.flush_every) == 0:
            try:
                self.csv_file.flush()
            except Exception:
                pass

        # buffers plot
        with self.lock:
            self.t_ring.append(t_rel)
            self.sho_ring.append(q_sh_rad)
            self.elb_ring.append(q_elb_rad)
            self.rot_ring.append(q_rot_rad)
            self.emg_ring.append(self.emg_env)

    def get_last(self):
        with self.lock:
            return (list(self.t_ring),
                    list(self.sho_ring),
                    list(self.elb_ring),
                    list(self.rot_ring),
                    list(self.emg_ring),
                    self.is_ready,
                    self.hold,
                    self._calib_stage)

# ================== GUI ==================
class RealtimePlot(QtWidgets.QWidget):
    def __init__(self, collector: IMUEMGCollector):
        super().__init__()
        self.collector = collector
        self.setWindowTitle("Myo 3DOF demo – Hombro(IMU) + Codo(EMG) + Rot(quat) → LabVIEW (UDP)")
        self.resize(1050, 680)

        layout = QtWidgets.QVBoxLayout(self)

        self.plot = pg.PlotWidget(title="Setpoints (rad): hombro, codo, rot")
        self.plot.setLabel('left', 'rad')
        self.plot.setLabel('bottom', 'Tiempo (s)')
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.plot)

        self.curve_sho = self.plot.plot(pen=pg.mkPen(width=2), name="hombro")
        self.curve_elb = self.plot.plot(pen=pg.mkPen(width=2, color=(200, 100, 0)), name="codo")
        self.curve_rot = self.plot.plot(pen=pg.mkPen(width=2, color=(0, 160, 200)), name="rot")

        self.plot2 = pg.PlotWidget(title="EMG envelope (RMS suavizado)")
        self.plot2.setLabel('left', 'a.u.')
        self.plot2.setLabel('bottom', 'Tiempo (s)')
        self.plot2.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.plot2)
        self.curve_emg = self.plot2.plot(pen=pg.mkPen(width=2))

        btn_row = QtWidgets.QHBoxLayout()
        self.btn_recenter = QtWidgets.QPushButton("Recenter (R)")
        self.btn_hold = QtWidgets.QPushButton("Hold (Espacio)")
        self.btn_stop = QtWidgets.QPushButton("Detener (Esc)")
        self.btn_recenter.clicked.connect(self.collector.request_recenter)
        self.btn_hold.clicked.connect(self.collector.toggle_hold)
        self.btn_stop.clicked.connect(self.stop_and_close)
        btn_row.addWidget(self.btn_recenter)
        btn_row.addWidget(self.btn_hold)
        btn_row.addWidget(self.btn_stop)
        layout.addLayout(btn_row)

        self.lbl = QtWidgets.QLabel("Estado: calibración (Etapa 1/2).")
        layout.addWidget(self.lbl)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(int(PLOT_UPDATE_MS))

        QtWidgets.QShortcut(QtCore.Qt.Key_Escape, self, activated=self.stop_and_close)
        QtWidgets.QShortcut(QtCore.Qt.Key_R, self, activated=self.collector.request_recenter)
        QtWidgets.QShortcut(QtCore.Qt.Key_Space, self, activated=self.collector.toggle_hold)

    def update_plot(self):
        t, sho, elb, rot, emg, ready, hold, stage = self.collector.get_last()
        if not t:
            return

        self.curve_sho.setData(t, sho)
        self.curve_elb.setData(t, elb)
        self.curve_rot.setData(t, rot)
        self.curve_emg.setData(t, emg)

        t_max = t[-1]
        window_sec = float(PLOT_WINDOW_SEC)
        t_min = max(0.0, t_max - window_sec)
        self.plot.setXRange(t_min, t_max, padding=0.02)
        self.plot2.setXRange(t_min, t_max, padding=0.02)

        if ready:
            self.lbl.setText(f"Estado: LISTO | HOLD={hold} | UDP -> {LV_HOST}:{LV_PORT}")
        else:
            if stage == 0:
                self.lbl.setText("Calibración Etapa 1/2: brazo abajo RELAJADO...")
            elif stage == 1:
                self.lbl.setText("Calibración Etapa 2/2: flexiona bíceps fuerte (sin mover hombro)...")
            else:
                self.lbl.setText("Calibración...")

    def stop_and_close(self):
        self.timer.stop()
        self.close()

# ================== MAIN ==================
def main():
    args = parse_args()
    cfg, cfg_path = load_config(args.config)
    apply_config(cfg)
    print(f"[INFO] Config -> {cfg_path}", flush=True)

    usuario = sanitize_name(USUARIO)
    ejercicio = sanitize_name(EJERCICIO)
    serie = next_series_for(usuario, ejercicio)

    myo.init(sdk_path=SDK_PATH)
    hub = myo.Hub()
    try:
        hub.set_locking_policy(LockingPolicy.none)
    except Exception:
        pass

    ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = BASE_DIR / usuario / ejercicio
    out_dir.mkdir(parents=True, exist_ok=True)

    base_name = f"myo_{usuario}_{ejercicio}_serie{serie:03d}_{ts_str}"
    csv_path  = out_dir / f"{base_name}.csv"
    json_path = out_dir / f"{base_name}.json"

    csv_file = open(csv_path, "w", newline="")
    csv_writer = csv.writer(csv_file)

    header = [
        "time_s",
        "quat_x","quat_y","quat_z","quat_w",
        "accel_x","accel_y","accel_z",
        "gyro_x","gyro_y","gyro_z",
        "tilt_deg","raw_sho_deg",
        "emg_env",
        "q_sh_rad","q_elb_rad","q_rot_rad"
    ]
    csv_writer.writerow(header)
    csv_file.flush()

    meta = {
        "user": usuario,
        "exercise": ejercicio,
        "serie": serie,
        "timestamp_start": ts_str,
        "config_file": str(cfg_path.resolve()) if cfg_path.exists() else str(cfg_path),
        "csv_file": str(csv_path.resolve()),
        "notes": NOTAS,
        "labview_udp": {"enabled": LV_ENABLED, "host": LV_HOST, "port": LV_PORT},
        "fs_imu_hz": IMU_FS,
        "emg_control": "RMS envelope normalized (rest vs max)",
        "payload_udp": "<q_shoulder_rad>,<q_elbow_rad>,<q_rot_rad>\\n"
    }
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(meta, jf, ensure_ascii=False, indent=2)

    lv_sender = LVUDPSender(LV_HOST, LV_PORT, enabled=LV_ENABLED)
    collector = IMUEMGCollector(csv_writer, csv_file, lv_sender)

    print("[INFO] Demo 3DOF listo. Teclas: R=recenter | Space=hold | Esc=stop", flush=True)
    print(f"       UDP -> {LV_HOST}:{LV_PORT}", flush=True)
    print(f"       CSV -> {csv_path}", flush=True)

    try:
        with hub.run_in_background(collector.on_event):
            app = QtWidgets.QApplication(sys.argv)
            win = RealtimePlot(collector)
            win.show()
            app.exec_()
    finally:
        try:
            hub.stop()
        except Exception:
            pass
        try:
            csv_file.flush()
            csv_file.close()
        except Exception:
            pass
        try:
            meta["timestamp_end"] = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(meta, jf, ensure_ascii=False, indent=2)
        except Exception:
            pass

    print(f"[OK] Sesión finalizada. CSV guardado en: {csv_path}", flush=True)

if __name__ == "__main__":
    main()