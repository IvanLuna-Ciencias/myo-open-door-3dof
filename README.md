\# Myo Open Door 3DOF Demo



This repository contains a real-time demo using a Myo Armband to generate three upper-limb setpoints for a LabVIEW-based exoskeleton interface.



\## Overview



The system estimates:



\- Shoulder flexion/extension from IMU tilt.

\- Elbow flexion/extension from Myo EMG amplitude.

\- Shoulder/exoskeleton rotation from quaternion-based twist estimation.



The setpoints are sent to LabVIEW through UDP.



\## UDP Payload



```text

<q\_shoulder\_rad>,<q\_elbow\_rad>,<q\_rot\_rad>\\n


## Requirements

- Windows
- Python 3.10 virtual environment
- Myo SDK for Windows
- Myo Connect running
- Myo Armband paired and connected
- LabVIEW VI configured to receive UDP packets

##================ Running the Demo ========================

Activate the Python virtual environment:

```powershell
& "path\to\env310\Scripts\Activate.ps1"


Run the script:
python scripts\myo_3dof_hombro_imu_codo_emg_rot_exoaxis_lv.py



##================ Calibration ==============================

1. Keep the arm down and relaxed for approximately 2 seconds.
2. Flex the biceps strongly for approximately 2 seconds.
3. The system starts sending setpoints to LabVIEW.

## Keyboard Controls

- `R`: recalibrate
- `Space`: hold setpoints
- `Esc`: stop



##==================== Troubleshooting ==================
If this error appears:
	Unable to connect to Myo Connect. Is Myo Connect running?

check that:
-Myo Connect is open.
-The Myo Armband is charged.
-The Myo Armband is paired.
-The Bluetooth adapter is connected.
-The Myo SDK path is correctly configured.
