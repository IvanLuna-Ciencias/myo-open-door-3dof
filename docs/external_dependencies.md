# External Dependencies

This project depends on external software and hardware that are not included in this repository.

These dependencies must be installed and configured separately before running the Myo Open Door 3DOF Demo.

---

## 1. Myo Connect

Myo Connect is required to pair the Myo Armband and provide the background service used by the Myo SDK.

The Myo SDK directory alone is not sufficient. Myo Connect must be installed and running before launching the Python script.

### Download Source

The Windows installer used for this project can be obtained from the archived `myo-python` release:

- [Myo Connect for Windows 1.0.1 — myo-python v1.0.4](https://github.com/NiklasRosenstein/myo-python/releases/tag/v1.0.4)

Open the release page, expand the **Assets** section and download the asset corresponding to:

```text
Myo Connect for Windows 1.0.1
```

> **Important:** This is a community-maintained historical archive. It is not maintained or distributed by this repository.

Because Myo Connect is legacy external software:

1. Scan the downloaded installer with Microsoft Defender or another trusted antivirus.
2. Install it on Windows.
3. Connect the original Myo USB dongle.
4. Open Myo Connect.
5. Pair the Myo Armband.
6. Leave Myo Connect running in the Windows system tray before starting Python.

Tested version:

```text
Myo Connect for Windows: 1.0.1
```

Myo Connect is external software and remains subject to its own license. It is not distributed under the MIT License of this repository.

---

## 2. Myo SDK

The project uses the Myo SDK for Windows 0.9.0.

The SDK used during development was obtained from:

- [pcernek/MyoSDK](https://github.com/pcernek/MyoSDK)

The SDK should be installed outside this repository.

Recommended installation location:

```text
C:\SDKs\MyoSDK\myo-sdk-win-0.9.0
```

The repository can be cloned with:

```powershell
mkdir C:\SDKs
cd C:\SDKs
git clone https://github.com/pcernek/MyoSDK.git
```

After cloning, verify that the SDK exists at:

```text
C:\SDKs\MyoSDK\myo-sdk-win-0.9.0
```

Configure the SDK path for the current PowerShell session:

```powershell
$env:MYO_SDK_PATH="C:\SDKs\MyoSDK\myo-sdk-win-0.9.0"
```

Verify the path:

```powershell
Test-Path $env:MYO_SDK_PATH
```

Expected result:

```text
True
```

To configure the environment variable permanently:

```powershell
setx MYO_SDK_PATH "C:\SDKs\MyoSDK\myo-sdk-win-0.9.0"
```

After using `setx`, close and reopen PowerShell.

The Myo SDK is external software and remains subject to its own license. It is not distributed under the MIT License of this repository.

---

## 3. Python Environment

The project was developed and tested using:

```text
Python 3.10.11
```

A virtual environment can be created with:

```powershell
py -3.10 -m venv env310
```

Activate it with:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\env310\Scripts\Activate.ps1
```

Install the required Python packages:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Verify the main dependencies:

```powershell
python -c "import myo, PyQt5, pyqtgraph, numpy; print('Dependencies OK')"
```

Expected output:

```text
Dependencies OK
```

---

## 4. Myo Hardware

The following hardware is required:

- Myo Armband
- Original Myo USB dongle
- Compatible USB port
- Bluetooth and USB drivers installed by Myo Connect

Before running the Python script, verify that:

- The Myo Armband is charged.
- The original USB dongle is connected.
- Myo Connect is open.
- The armband is paired and connected.
- The Myo Connect icon appears in the Windows system tray.

---

## 5. LabVIEW

LabVIEW is used as the UDP receiver and exoskeleton interface.

The Python script sends three setpoints:

```text
q_shoulder_rad,q_elbow_rad,q_rot_rad
```

Default UDP configuration:

```text
Host: 172.22.11.2
Port: 5005
```

The LabVIEW VI must use the same port and must interpret all three values in radians.

The complete laboratory-specific LabVIEW, NI driver, cRIO and exoskeleton configuration is not included in this repository.

A separate repository will be created later to document the full LabVIEW and exoskeleton control environment.

---

## 6. NI Drivers and Hardware Configuration

Depending on the laboratory setup, the following may also be required:

- LabVIEW
- NI CompactRIO drivers
- NI-RIO
- LabVIEW Real-Time
- LabVIEW FPGA
- Device-specific drivers
- cRIO configuration
- Exoskeleton motor and encoder interfaces

The exact versions depend on the laboratory hardware and are not installed automatically by this repository.

---

## 7. Dependency Flow

The complete Myo software chain is:

```text
Myo Armband
    -> Myo USB dongle
        -> Myo Connect
            -> Myo SDK 0.9.0
                -> Python myo package
                    -> Project script
                        -> UDP
                            -> LabVIEW
```

Myo Connect must be installed and running. Installing only the SDK is not sufficient.

---

## 8. Troubleshooting

### Myo Connect is not installed

The script may display:

```text
Unable to connect to Myo Connect. Is Myo Connect running?
```

Install Myo Connect for Windows 1.0.1 from the archived release and leave it running in the Windows system tray.

### Myo Connect is installed but the error remains

Verify:

- Myo Connect is open.
- The original Myo USB dongle is connected.
- The armband is paired.
- The firewall is not blocking communication.
- The Myo SDK path is correct.
- Python is running from the expected virtual environment.

### Myo SDK path is invalid

Check:

```powershell
$env:MYO_SDK_PATH
Test-Path $env:MYO_SDK_PATH
```

The second command should return:

```text
True
```

### Python cannot import the Myo package

Run:

```powershell
python -c "import myo; print('Myo Python package OK')"
```

If the import fails, reinstall the dependencies from:

```powershell
python -m pip install -r requirements.txt
```

---

## 9. Licensing

The MIT License included in this repository applies only to the original source code, configuration files and documentation developed for this project.

The following external components remain subject to their own licenses:

- Myo Connect
- Myo SDK
- Myo Python packages
- LabVIEW
- NI drivers and modules
- cRIO software and firmware
- Third-party Python dependencies

External installers, SDK files and proprietary software are not redistributed in this repository.