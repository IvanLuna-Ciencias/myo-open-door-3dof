# Myo Open Door 3DOF Demo

Real-time demo using a **Myo Armband** to generate three upper-limb setpoints for a LabVIEW-based exoskeleton interface.

The system estimates shoulder, elbow and rotation setpoints from Myo IMU and EMG signals, then sends them to LabVIEW through UDP.

---

## Overview

The demo estimates:

- **Shoulder flexion/extension** from IMU tilt.
- **Elbow flexion/extension** from Myo EMG amplitude.
- **Shoulder/exoskeleton rotation** from quaternion-based twist estimation.

The output consists of three joint setpoints in radians:

```text
q_shoulder_rad, q_elbow_rad, q_rot_rad
```

---

## Repository Structure

```text
myo-open-door-3dof/
│
├── scripts/
│   └── myo_3dof_hombro_imu_codo_emg_rot_exoaxis_lv.py
│
├── labview/
│   └── Puertas_Abiertas_3gdL.vi
│
├── data/
│   └── README.md
│
├── docs/
│   └── README.md
│
├── outputs/
│   └── README.md
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Documentation

Additional technical documentation is available in:

- [Windows setup](docs/setup_windows.md)
- [UDP LabVIEW protocol](docs/udp_labview_protocol.md)
- [Calibration procedure](docs/calibration.md)


## Requirements

- Windows
- Python 3.10 virtual environment
- Myo SDK for Windows
- Myo Connect running
- Myo Armband paired and connected
- LabVIEW VI configured to receive UDP packets

Python dependencies are listed in:

```text
requirements.txt
```

---

## Running the Demo

Activate the Python virtual environment:

```powershell
& "path\to\env310\Scripts\Activate.ps1"
```

Run the script:

```powershell
python scripts\myo_3dof_hombro_imu_codo_emg_rot_exoaxis_lv.py
```

The script will open a real-time visualization window and start the Myo acquisition process.

---

## Calibration

The demo uses a two-stage calibration process:

1. Keep the arm down and relaxed for approximately 2 seconds.
2. Flex the biceps strongly for approximately 2 seconds.
3. After calibration, the system starts sending setpoints to LabVIEW.

---

## Keyboard Controls

| Key | Function |
|---|---|
| `R` | Recalibrate |
| `Space` | Hold setpoints |
| `Esc` | Stop the demo |

---

## LabVIEW UDP Communication

The Python script sends the following UDP payload to LabVIEW:

```text
<q_shoulder_rad>,<q_elbow_rad>,<q_rot_rad>\n
```

Default UDP configuration:

```text
Host: 172.22.11.2
Port: 5005
```

These values can be modified directly in the Python script.

---

## Output Files

The script saves session data as `.csv` and `.json` files.

Generated outputs are ignored by Git to avoid uploading experimental data or temporary acquisition files.

---

## Troubleshooting

If this error appears:

```text
Unable to connect to Myo Connect. Is Myo Connect running?
```

Check that:

- Myo Connect is open.
- The Myo Armband is charged.
- The Myo Armband is paired and connected.
- The Bluetooth adapter is connected.
- The Myo SDK path is correctly configured.

---

## Notes

This repository is an initial open-door demo for testing Myo-based acquisition, signal processing and LabVIEW communication before integrating the full multimodal EEG–sEMG–IMU motor intention detection pipeline.