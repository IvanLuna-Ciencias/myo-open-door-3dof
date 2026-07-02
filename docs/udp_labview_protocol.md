# UDP LabVIEW Protocol

This document describes the UDP communication protocol used between the Python Myo demo and the LabVIEW VI.

The Python script sends three upper-limb setpoints to LabVIEW in real time. These setpoints are generated from Myo Armband IMU and EMG signals.

---

## 1. Communication Overview

The communication is performed using UDP.

Python acts as the UDP sender, and LabVIEW acts as the UDP receiver.

```text
Myo Armband -> Python script -> UDP packet -> LabVIEW VI
```

The Python script estimates three setpoints:

- Shoulder flexion/extension setpoint
- Elbow flexion/extension setpoint
- Shoulder/exoskeleton rotation setpoint

These values are sent to LabVIEW as a comma-separated text message.

---

## 2. Default UDP Configuration

Default configuration used by the Python script:

```text
Host: 172.22.11.2
Port: 5005
```

The LabVIEW VI must be configured to listen to the same UDP port.

---

## 3. Payload Format

The UDP message has the following format:

```text
q_shoulder_rad, q_elbow_rad, q_rot_rad
```

Example:

```text
0.523599,0.785398,-0.174533
```

Each packet contains one line of text with three numeric values separated by commas.

---

## 4. Variables

| Variable | Unit | Description |
|---|---:|---|
| `q_shoulder_rad` | rad | Shoulder flexion/extension setpoint |
| `q_elbow_rad` | rad | Elbow flexion/extension setpoint |
| `q_rot_rad` | rad | Shoulder/exoskeleton rotation setpoint |

All values are sent in radians.

---

## 5. Expected LabVIEW Behavior

The LabVIEW VI should:

1. Open a UDP receiver on the configured port.
2. Read the incoming UDP string.
3. Remove the end-of-line character if necessary.
4. Split the message by commas.
5. Convert the three values from string to numeric values.
6. Use the values as joint setpoints.

The expected order is always:

```text
shoulder, elbow, rotation
```

---

## 6. Python Sender Behavior

The Python script sends the UDP packet after calibration is complete and the system is ready.

During normal operation, each UDP packet contains the current setpoints:

```text
q_shoulder_rad, q_elbow_rad, q_rot_rad
```

The values are formatted with six decimal places.

Example:

```text
0.174533,0.349066,0.000000
```

---

## 7. Units and Conversion

Python sends all setpoints in radians.

For reference:

| Degrees | Radians |
|---:|---:|
| 0 deg | 0.000000 rad |
| 10 deg | 0.174533 rad |
| 30 deg | 0.523599 rad |
| 45 deg | 0.785398 rad |
| 90 deg | 1.570796 rad |

If the LabVIEW side requires degrees, the conversion is:

```text
degrees = radians * 180 / pi
```

---

## 8. Timing Notes

The Myo IMU is approximately updated at 50 Hz.

The Python script updates the setpoints in real time and sends UDP packets during active operation.

UDP does not guarantee packet delivery. For this demo, this is acceptable because new setpoints are continuously sent and the most recent packet is the most relevant.

---

## 9. Troubleshooting

### LabVIEW is not receiving data

Check that:

- The LabVIEW VI is running.
- The UDP port matches the Python configuration.
- The computer IP address matches the Python `LV_HOST` value.
- The firewall is not blocking UDP traffic.
- Python and LabVIEW are connected to the same network or interface.

### Values arrive in the wrong order

The correct order is:

```text
q_shoulder_rad, q_elbow_rad, q_rot_rad
```

Make sure the LabVIEW parser uses the same order.

### Values look too small

The values are sent in radians, not degrees.

For example:

```text
90 deg = 1.570796 rad
```

### No packets are sent before calibration

This is expected. The Python script starts sending active setpoints after the calibration routine is complete.

---

## 10. Protocol Summary

| Item | Value |
|---|---|
| Communication type | UDP |
| Sender | Python script |
| Receiver | LabVIEW VI |
| Payload type | Text string |
| Separator | Comma |
| End of message | New line `\n` |
| Units | Radians |
| Number of values | 3 |
| Value order | Shoulder, elbow, rotation |
