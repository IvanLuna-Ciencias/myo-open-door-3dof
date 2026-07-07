# Windows Setup

This document describes the basic setup required to run the **Myo Open Door 3DOF Demo** on Windows.

The demo uses a **Myo Armband** to estimate three upper-limb setpoints and send them to LabVIEW through UDP.

---

## 1. Required Software

The following software is required:

- Windows
- Python 3.10
- Myo SDK for Windows
- Myo Connect
- LabVIEW
- Git

The Myo Armband must be charged, paired and connected through Myo Connect before running the Python script.

---

## 2. Obtaining the Myo SDK

This project requires the Myo SDK for Windows version 0.9.0.

The SDK used during development was obtained from the following third-party repository:

- [pcernek/MyoSDK](https://github.com/pcernek/MyoSDK)

> **Important:** This is a third-party repository containing an adaptation or archived copy of the Myo SDK. It is not maintained as part of this project and should not be considered an official distribution by this repository's author.

To obtain the files, either download the repository as a ZIP file from GitHub or clone it:

```powershell
cd C:\SDKs
git clone https://github.com/pcernek/MyoSDK.git
```

After cloning, the expected SDK folder is:

```text
C:\SDKs\MyoSDK\myo-sdk-win-0.9.0
```

Configure the SDK path for the current PowerShell session:

```powershell
$env:MYO_SDK_PATH="C:\SDKs\MyoSDK\myo-sdk-win-0.9.0"
```

The Myo SDK is external software and remains subject to its own license agreement. It is not distributed under the MIT License of this repository.
---

## 3. Repository Location

Recommended local repository location:

```text
C:\GitHub\myo-open-door-3dof
```

Open PowerShell and move to the repository folder:

```powershell
cd C:\GitHub\myo-open-door-3dof
```

---

## 4. Python Virtual Environment

This project was tested using a Python 3.10 virtual environment.

To activate the environment, use:

```powershell
& "C:\path\to\env310\Scripts\Activate.ps1"
```

Example:

```powershell
& "C:\Users\YourUser\Documents\env310\Scripts\Activate.ps1"
```

After activation, PowerShell should show the environment name at the beginning of the line:

```text
(env310) PS C:\GitHub\myo-open-door-3dof>
```

---

## 5. Install Python Dependencies

With the virtual environment activated, install the required Python packages:

```powershell
pip install -r requirements.txt
```

To verify that the main dependencies are available, run:

```powershell
python -c "import myo, PyQt5, pyqtgraph, numpy; print('Dependencies OK')"
```

Expected output:

```text
Dependencies OK
```

---

## 6. Myo SDK Path

The Python script requires the Myo SDK for Windows.

The recommended method is to define the `MYO_SDK_PATH` environment variable.

Example for the current PowerShell session:

```powershell
$env:MYO_SDK_PATH="C:\path\to\myo-sdk-win-0.9.0"
```

For a permanent Windows configuration, add `MYO_SDK_PATH` as a user environment variable using:

```text
System Properties > Environment Variables > User variables
```

Example value:

```text
C:\SDKs\myo-sdk-win-0.9.0
```

The Python script first checks the `MYO_SDK_PATH` environment variable. If the variable is not defined, it uses the default SDK path written inside the script.

---

## 7. Myo Connect

Before running the demo:

1. Open Myo Connect.
2. Connect the Myo Armband.
3. Verify that the armband is paired.
4. Keep the armband charged.
5. Make sure the Bluetooth adapter is connected.

If Myo Connect is not running, the script may show the following error:

```text
Unable to connect to Myo Connect. Is Myo Connect running?
```

---

## 8. LabVIEW Setup

The LabVIEW VI must be open and configured to receive UDP packets.

Default UDP configuration:

```text
Host: 172.22.11.2
Port: 5005
```

The Python script sends three setpoints using the following UDP payload format:

```text
<q_shoulder_rad>,<q_elbow_rad>,<q_rot_rad>\n
```

All values are sent in radians.

---

## 9. Running the Demo

From the repository folder, run:

```powershell
python scripts\myo_3dof_hombro_imu_codo_emg_rot_exoaxis_lv.py
```

The script will:

1. Connect to the Myo Armband.
2. Start IMU and EMG acquisition.
3. Open a real-time visualization window.
4. Perform the calibration routine.
5. Send three setpoints to LabVIEW through UDP.
6. Save session outputs as CSV and JSON files.

---

## 10. Calibration Procedure

The demo uses a two-stage calibration process.

### Stage 1: Rest Calibration

Keep the arm down and relaxed for approximately 2 seconds.

This stage estimates:

- Initial shoulder tilt
- Rest EMG level
- Initial orientation quaternion

### Stage 2: Maximum EMG Calibration

Flex the biceps strongly for approximately 2 seconds.

This stage estimates:

- Maximum EMG envelope level

After this calibration, the system starts sending setpoints to LabVIEW.

---

## 11. Keyboard Controls

| Key | Function |
|---|---|
| `R` | Recalibrate |
| `Space` | Hold setpoints |
| `Esc` | Stop the demo |

---

## 12. Output Files

The script generates session files in CSV and JSON format.

Generated acquisition outputs are ignored by Git to avoid uploading experimental data or temporary files.

---

## 13. Troubleshooting

### Myo Connect error

Error:

```text
Unable to connect to Myo Connect. Is Myo Connect running?
```

Possible solutions:

- Open Myo Connect.
- Pair the Myo Armband.
- Check the Bluetooth adapter.
- Charge the Myo Armband.
- Restart Myo Connect.
- Restart the Python script.

### Python package error

Error example:

```text
ModuleNotFoundError: No module named 'pyqtgraph'
```

Solution:

```powershell
pip install -r requirements.txt
```

### Wrong Python environment

Check the Python executable being used:

```powershell
where.exe python
```

The first path should point to the active virtual environment:

```text
...\env310\Scripts\python.exe
```

---

## 14. Basic Verification Checklist

Before running the demo, verify:

- The virtual environment is activated.
- Python dependencies are installed.
- Myo Connect is open.
- The Myo Armband is paired and connected.
- The Myo SDK path is configured.
- The LabVIEW VI is open.
- The UDP host and port match between Python and LabVIEW.
