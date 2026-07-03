# Configuration File

This document describes the configuration file used by the Myo Open Door 3DOF Demo.

The main configuration file is:

```text
configs/demo_3dof.json
```

This file allows changing important parameters without editing the Python script directly.

---

## 1. Purpose

The configuration file defines:

- Myo SDK settings
- Session information
- Output folder
- LabVIEW UDP communication
- Calibration duration
- Shoulder parameters
- Elbow parameters
- Rotation parameters
- Logging options
- Real-time plot options

This makes the demo easier to adapt to another computer, user, network or LabVIEW setup.

---

## 2. Running the Script with a Config File

The demo can be executed with:

```powershell
python scripts\myo_3dof_hombro_imu_codo_emg_rot_exoaxis_lv.py --config configs\demo_3dof.json
```

If no `--config` argument is provided, the script uses the default configuration path:

```text
configs/demo_3dof.json
```

---

## 3. Project Section

```json
"project": {
  "name": "Myo Open Door 3DOF Demo",
  "description": "Real-time Myo Armband demo for 3-DOF upper-limb setpoint generation and LabVIEW UDP communication."
}
```

This section provides general metadata about the project.

It does not affect signal processing or communication behavior.

---

## 4. Myo Section

```json
"myo": {
  "sdk_path_env": "MYO_SDK_PATH",
  "default_sdk_path": "C:\\SDKs\\myo-sdk-win-0.9.0\\myo-sdk-win-0.9.0",
  "imu_fs_hz": 50.0
}
```

### `sdk_path_env`

Name of the environment variable used to locate the Myo SDK.

Default:

```text
MYO_SDK_PATH
```

The script first checks this environment variable.

### `default_sdk_path`

Fallback path used if the environment variable is not defined.

This should be a generic path, not a personal user path.

Recommended local setup:

```powershell
$env:MYO_SDK_PATH="C:\path\to\myo-sdk-win-0.9.0"
```

### `imu_fs_hz`

Approximate IMU sampling frequency used internally by the script.

Default:

```text
50.0 Hz
```

---

## 5. Session Section

```json
"session": {
  "base_dir": "outputs",
  "user": "puertas_abiertas",
  "exercise": "demo_3dof",
  "notes": ""
}
```

### `base_dir`

Base folder where output files are saved.

Default:

```text
outputs
```

### `user`

Session user name used to organize output files.

### `exercise`

Exercise or demo name used to organize output files.

### `notes`

Optional notes saved in the session metadata JSON file.

---

## 6. LabVIEW Section

```json
"labview": {
  "host": "172.22.11.2",
  "port": 5005,
  "enabled": true,
  "payload": "<q_shoulder_rad>,<q_elbow_rad>,<q_rot_rad>\\n"
}
```

### `host`

IP address of the LabVIEW receiver.

Default:

```text
172.22.11.2
```

This value must match the LabVIEW computer or network interface.

### `port`

UDP port used by LabVIEW.

Default:

```text
5005
```

Python and LabVIEW must use the same port.

### `enabled`

Enables or disables UDP communication.

Use:

```json
true
```

to send values to LabVIEW.

Use:

```json
false
```

to run the demo without sending UDP packets.

### `payload`

Human-readable description of the UDP message format.

The actual values are sent in this order:

```text
q_shoulder_rad,q_elbow_rad,q_rot_rad
```

---

## 7. Calibration Section

```json
"calibration": {
  "duration_sec": 2.0
}
```

### `duration_sec`

Approximate duration of each calibration stage.

Default:

```text
2.0 seconds
```

The demo uses two calibration stages:

1. Rest calibration
2. Maximum EMG calibration

---

## 8. Shoulder Section

```json
"shoulder": {
  "tilt_axis": "tilt_z",
  "sign": -1.0,
  "min_deg": -20.0,
  "max_deg": 140.0,
  "tau_gravity_sec": 0.60,
  "tau_setpoint_sec": 0.22,
  "deadband_deg": 0.6,
  "rate_limit_dps": 120.0
}
```

This section controls shoulder flexion/extension estimation from IMU tilt.

### `tilt_axis`

Tilt axis used for shoulder estimation.

Possible values depend on the script implementation:

```text
tilt_x
tilt_y
tilt_z
```

### `sign`

Direction correction for shoulder movement.

Use:

```text
1.0
```

or:

```text
-1.0
```

If shoulder flexion appears inverted, change this sign.

### `min_deg` and `max_deg`

Minimum and maximum shoulder setpoint limits in degrees.

### `tau_gravity_sec`

Low-pass filter time constant used to estimate the gravity vector from acceleration.

### `tau_setpoint_sec`

Smoothing time constant for the shoulder setpoint.

### `deadband_deg`

Small changes below this threshold are ignored.

### `rate_limit_dps`

Maximum shoulder setpoint change rate in degrees per second.

---

## 9. Elbow Section

```json
"elbow": {
  "min_deg": 0.0,
  "max_deg": 100.0,
  "tau_emg_sec": 0.15,
  "tau_setpoint_sec": 0.20,
  "deadband_deg": 0.6,
  "rate_limit_dps": 220.0
}
```

This section controls elbow flexion/extension estimation from Myo EMG amplitude.

### `min_deg` and `max_deg`

Minimum and maximum elbow setpoint limits in degrees.

### `tau_emg_sec`

Smoothing time constant for the EMG envelope.

### `tau_setpoint_sec`

Smoothing time constant for the elbow setpoint.

### `deadband_deg`

Small setpoint changes below this value are ignored.

### `rate_limit_dps`

Maximum elbow setpoint change rate in degrees per second.

---

## 10. Rotation Section

```json
"rotation": {
  "robot_axis_world": [0.0, 0.0, 1.0],
  "sign": -1.0,
  "min_deg": -40.0,
  "max_deg": 40.0,
  "tau_setpoint_sec": 0.20,
  "deadband_deg": 0.8,
  "rate_limit_dps": 180.0
}
```

This section controls the shoulder/exoskeleton rotation setpoint estimated from the orientation quaternion.

### `robot_axis_world`

Fixed axis used to extract the quaternion-based twist angle.

Example:

```json
[0.0, 0.0, 1.0]
```

### `sign`

Direction correction for the rotation setpoint.

If rotation appears inverted, change this sign.

### `min_deg` and `max_deg`

Minimum and maximum rotation setpoint limits in degrees.

### `tau_setpoint_sec`

Smoothing time constant for the rotation setpoint.

### `deadband_deg`

Small rotation changes below this value are ignored.

### `rate_limit_dps`

Maximum rotation setpoint change rate in degrees per second.

---

## 11. Logging Section

```json
"logging": {
  "flush_every_samples": 50
}
```

### `flush_every_samples`

Defines how often the CSV file is flushed during acquisition.

Lower values save data more frequently but may slightly increase disk activity.

---

## 12. Plot Section

```json
"plot": {
  "ring_length_samples": 1500,
  "window_sec": 12.0,
  "update_ms": 50
}
```

### `ring_length_samples`

Number of recent samples kept in the real-time plot buffer.

### `window_sec`

Time window shown in the real-time plot.

### `update_ms`

Plot update interval in milliseconds.

---

## 13. Local Configuration Files

Machine-specific configuration files should not be committed to GitHub.

For local experiments, use files such as:

```text
configs/demo_3dof.local.json
```

These files are ignored by Git if `.gitignore` includes:

```text
configs/*.local.json
```

This allows each computer to have its own local configuration without modifying the public repository configuration.

---

## 14. Recommended Workflow

For general use:

1. Keep `configs/demo_3dof.json` as the public example configuration.
2. Create a local copy if needed:

```powershell
copy configs\demo_3dof.json configs\demo_3dof.local.json
```

3. Modify the local file with computer-specific values.
4. Run the script using the local config:

```powershell
python scripts\myo_3dof_hombro_imu_codo_emg_rot_exoaxis_lv.py --config configs\demo_3dof.local.json
```

The local file will not be uploaded to GitHub.

---

## 15. Configuration Summary

| Section | Purpose |
|---|---|
| `project` | General project metadata |
| `myo` | Myo SDK and IMU settings |
| `session` | Output folder and session metadata |
| `labview` | UDP host, port and enable flag |
| `calibration` | Calibration duration |
| `shoulder` | Shoulder setpoint parameters |
| `elbow` | Elbow setpoint parameters |
| `rotation` | Rotation setpoint parameters |
| `logging` | CSV writing behavior |
| `plot` | Real-time plot behavior |

---

## 16. Important Notes

The configuration file improves portability, but it does not remove the need for correct hardware setup.

Before running the demo, verify:

- Myo Connect is open.
- The Myo Armband is paired.
- The Myo SDK path is valid.
- The LabVIEW VI is open.
- The UDP host and port are correct.
- The selected signs and axes match the physical setup.
