# Myo Acquisition

This document describes how the Myo Armband is used in the Myo Open Door 3DOF Demo.

The demo uses Myo IMU and EMG signals to estimate three upper-limb setpoints in real time:

- Shoulder flexion/extension
- Elbow flexion/extension
- Shoulder/exoskeleton rotation

These setpoints are displayed in a real-time plot, saved to CSV/JSON files and sent to LabVIEW through UDP.

---

## 1. Acquisition Overview

The Myo Armband provides:

- Orientation quaternion
- Acceleration
- Gyroscope
- 8-channel EMG

The general processing flow is:

```text
Myo Armband
    -> Python listener
        -> IMU processing
        -> EMG processing
        -> Calibration
        -> Setpoint estimation
        -> Real-time plot
        -> CSV/JSON output
        -> UDP message to LabVIEW
```

---

## 2. Signals Used

| Signal | Source | Approximate Rate | Use in Demo |
|---|---|---:|---|
| Orientation quaternion | Myo IMU | 50 Hz | Rotation setpoint |
| Acceleration | Myo IMU | 50 Hz | Shoulder tilt estimation |
| Gyroscope | Myo IMU | 50 Hz | Logged for reference |
| 8-channel EMG | Myo EMG | 200 Hz | Elbow activation estimation |

---

## 3. Shoulder Flexion/Extension from IMU Tilt

Shoulder flexion/extension is estimated from the acceleration signal.

The script applies a low-pass filter to the acceleration components to approximate the gravity vector:

```text
gx, gy, gz
```

Then, a tilt angle is computed from the gravity vector.

The selected tilt axis is defined in the Python script:

```text
TILT_AXIS
```

The shoulder direction can be inverted using:

```text
SIGN_SHO
```

The resulting shoulder angle is limited and smoothed before being converted to radians:

```text
q_shoulder_rad
```

---

## 4. Elbow Flexion/Extension from EMG

Elbow flexion/extension is estimated from the Myo EMG amplitude.

The script reads the 8 EMG channels and computes an RMS value:

```text
EMG RMS envelope
```

The EMG envelope is smoothed and normalized using two calibration values:

| Calibration Value | Meaning |
|---|---|
| `emg_rest` | EMG level during relaxed arm |
| `emg_max` | EMG level during strong biceps contraction |

The normalized EMG activation is mapped to an elbow angle range:

```text
ELB_MIN_DEG to ELB_MAX_DEG
```

The resulting elbow setpoint is converted to radians:

```text
q_elbow_rad
```

---

## 5. Shoulder/Exoskeleton Rotation from Quaternion

The rotation setpoint is estimated from the orientation quaternion.

During calibration, the initial quaternion is stored as:

```text
q0
```

During operation, the relative orientation is computed with respect to the calibrated initial orientation.

A twist angle is then extracted around a fixed exoskeleton axis:

```text
ROBOT_AXIS_WORLD
```

The rotation direction can be inverted using:

```text
SIGN_ROT
```

The rotation setpoint is limited, smoothed and converted to radians:

```text
q_rot_rad
```

---

## 6. Calibration Values Used by Acquisition

The acquisition process depends on the calibration routine.

| Value | Estimated During | Used For |
|---|---|---|
| `tilt0` | Stage 1 | Initial shoulder reference |
| `q0` | Stage 1 | Initial orientation reference |
| `emg_rest` | Stage 1 | EMG baseline |
| `emg_max` | Stage 2 | EMG normalization |

The system starts sending active setpoints to LabVIEW after calibration is complete.

---

## 7. Output Setpoints

The final output of the acquisition and processing pipeline consists of three values:

| Setpoint | Unit | Description |
|---|---:|---|
| `q_shoulder_rad` | rad | Shoulder flexion/extension |
| `q_elbow_rad` | rad | Elbow flexion/extension |
| `q_rot_rad` | rad | Shoulder/exoskeleton rotation |

These values are sent to LabVIEW in the following order:

```text
q_shoulder_rad,q_elbow_rad,q_rot_rad
```

---

## 8. Real-Time Plot

The Python script opens a PyQtGraph window to visualize:

- Shoulder setpoint
- Elbow setpoint
- Rotation setpoint
- EMG envelope

This visualization is useful for checking signal behavior during the demo.

---

## 9. Saved Output Files

The script saves session data in CSV format and metadata in JSON format.

The CSV file includes:

| Column | Description |
|---|---|
| `time_s` | Relative time |
| `quat_x`, `quat_y`, `quat_z`, `quat_w` | Orientation quaternion |
| `accel_x`, `accel_y`, `accel_z` | Acceleration |
| `gyro_x`, `gyro_y`, `gyro_z` | Gyroscope |
| `tilt_deg` | Estimated tilt angle |
| `raw_sho_deg` | Raw shoulder angle |
| `emg_env` | Smoothed EMG envelope |
| `q_sh_rad` | Shoulder setpoint in radians |
| `q_elb_rad` | Elbow setpoint in radians |
| `q_rot_rad` | Rotation setpoint in radians |

Generated acquisition files are ignored by Git.

---

## 10. Important Parameters

Some important parameters are defined directly in the Python script.

| Parameter | Purpose |
|---|---|
| `IMU_FS` | IMU sampling frequency used by the script |
| `TILT_AXIS` | Tilt axis used for shoulder estimation |
| `SIGN_SHO` | Shoulder sign correction |
| `ELB_MIN_DEG` | Minimum elbow angle |
| `ELB_MAX_DEG` | Maximum elbow angle |
| `ROBOT_AXIS_WORLD` | Fixed axis used for rotation estimation |
| `SIGN_ROT` | Rotation sign correction |
| `LV_HOST` | LabVIEW UDP receiver IP |
| `LV_PORT` | LabVIEW UDP receiver port |

---

## 11. Notes and Limitations

This demo is intended as an open-door test for Myo-based acquisition and LabVIEW communication.

Important limitations:

- Shoulder flexion/extension is approximated from IMU tilt.
- Elbow flexion/extension is estimated from EMG amplitude, not from a biomechanical elbow angle sensor.
- Rotation is estimated as a quaternion-based twist around a fixed exoskeleton axis.
- The Myo Armband position on the arm affects the signal quality.
- Recalibration is required if the armband moves.

For more robust experiments, calibration, sensor placement and signal quality should be checked before each session.
