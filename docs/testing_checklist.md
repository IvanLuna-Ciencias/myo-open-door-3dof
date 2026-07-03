# Testing Checklist

This checklist is used to verify that the Myo Open Door 3DOF Demo is correctly configured and ready to run.

Use this document before running a real session with the Myo Armband and LabVIEW.

---

## 1. Repository Status

Verify that the repository is clean and updated.

```powershell
git status
```

Expected result:

```text
nothing to commit, working tree clean
```

---

## 2. Python Environment

Activate the Python virtual environment.

```powershell
& "C:\path\to\env310\Scripts\Activate.ps1"
```

Verify the Python executable:

```powershell
where.exe python
```

The first path should point to the active virtual environment:

```text
...\env310\Scripts\python.exe
```

---

## 3. Python Dependencies

Verify that the main dependencies are installed.

```powershell
python -c "import myo, PyQt5, pyqtgraph, numpy; print('Dependencies OK')"
```

Expected output:

```text
Dependencies OK
```

---

## 4. Script Help Test

Verify that the script recognizes the configuration argument.

```powershell
python scripts\myo_3dof_hombro_imu_codo_emg_rot_exoaxis_lv.py --help
```

Expected result:

- The script prints the help message.
- The `--config` option appears.

---

## 5. Configuration File Test

Run the script with the default configuration file.

```powershell
python scripts\myo_3dof_hombro_imu_codo_emg_rot_exoaxis_lv.py --config configs\demo_3dof.json
```

If the Myo Armband is not connected, the expected error is:

```text
Unable to connect to Myo Connect. Is Myo Connect running?
```

This means that the script loaded the configuration and reached the Myo connection step.

---

## 6. Myo Connect Check

Before running a real test, verify:

- Myo Connect is open.
- The Myo Armband is charged.
- The Myo Armband is paired.
- The Bluetooth adapter is connected.
- The Myo SDK path is correctly configured.

---

## 7. LabVIEW Check

Before running the Python script, verify:

- The LabVIEW VI is open.
- The UDP receiver is running.
- The UDP port matches the Python configuration.
- The LabVIEW computer IP matches the Python `LV_HOST` value.
- The expected value order is shoulder, elbow and rotation.
- Values are interpreted in radians.

---

## 8. Real Acquisition Test

With Myo Connect and LabVIEW ready, run:

```powershell
python scripts\myo_3dof_hombro_imu_codo_emg_rot_exoaxis_lv.py --config configs\demo_3dof.json
```

Expected behavior:

1. The script connects to the Myo Armband.
2. A real-time visualization window opens.
3. The calibration routine starts.
4. The user completes Stage 1 and Stage 2 calibration.
5. The script starts sending UDP setpoints to LabVIEW.
6. CSV and JSON output files are generated.

---

## 9. Calibration Test

Verify that the calibration follows this sequence:

| Stage | User Action | Expected Result |
|---|---|---|
| Stage 1 | Arm down and relaxed | Initial tilt, rest EMG and initial quaternion are estimated |
| Stage 2 | Strong biceps contraction | Maximum EMG envelope is estimated |
| Ready | Move/activate arm | Setpoints are updated and sent to LabVIEW |

---

## 10. Keyboard Control Test

Verify the keyboard controls:

| Key | Expected Behavior |
|---|---|
| `R` | Recalibration starts |
| `Space` | Setpoints are held/frozen |
| `Esc` | Demo stops and files are saved |

---

## 11. UDP Output Test

Verify in LabVIEW that values arrive in this order:

```text
q_shoulder_rad,q_elbow_rad,q_rot_rad
```

Check that:

- Shoulder movement changes the first value.
- EMG activation changes the second value.
- Rotation movement changes the third value.
- Values are received in radians.

---

## 12. Output Files Test

After stopping the demo, verify that output files were created.

Expected output types:

```text
.csv
.json
```

The generated files should be saved under the configured output folder.

Default:

```text
outputs
```

---

## 13. Final Validation

The demo can be considered ready when:

- The Python environment works.
- The script loads the JSON configuration.
- The Myo Armband connects correctly.
- The real-time plot opens.
- Calibration completes.
- UDP packets are received by LabVIEW.
- Output files are saved.
- The repository remains clean after ignoring generated outputs.
