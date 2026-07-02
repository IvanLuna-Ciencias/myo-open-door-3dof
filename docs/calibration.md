# Calibration Procedure

This document describes the calibration routine used by the Myo Open Door 3DOF Demo.

The calibration is required before sending active setpoints to LabVIEW. It defines the initial posture reference and normalizes the EMG signal used for elbow control.

---

## 1. Calibration Overview

The demo uses a two-stage calibration process:

1. Rest calibration
2. Maximum EMG calibration

After both stages are completed, the system starts sending setpoints to LabVIEW through UDP.

---

## 2. Stage 1: Rest Calibration

During the first stage, the user should keep the arm down and relaxed for approximately 2 seconds.

This stage estimates:

- Initial shoulder tilt
- Rest EMG level
- Initial orientation quaternion

The initial shoulder tilt is used as the reference position for shoulder flexion/extension.

The rest EMG level is used as the baseline for elbow activation.

The initial quaternion is used as the reference orientation for the rotation setpoint.

---

## 3. Stage 1 User Instruction

The user should:

1. Wear the Myo Armband correctly.
2. Keep the arm down.
3. Keep the muscles relaxed.
4. Avoid moving the shoulder or elbow.
5. Wait until the script finishes Stage 1.

Expected console message:

```text
[CAL] Etapa 1/2: brazo abajo RELAJADO ~2 s
```

After Stage 1 is completed, the script will continue to Stage 2.

---

## 4. Stage 2: Maximum EMG Calibration

During the second stage, the user should perform a strong biceps contraction for approximately 2 seconds.

This stage estimates the maximum EMG envelope level.

The maximum EMG level is used to normalize the elbow control signal between rest and maximum contraction.

---

## 5. Stage 2 User Instruction

The user should:

1. Keep the shoulder as still as possible.
2. Flex the biceps strongly.
3. Avoid large arm movements.
4. Hold the contraction until the script finishes Stage 2.

Expected console message:

```text
[CAL] Etapa 2/2: FLEXIONA bíceps fuerte
```

After Stage 2 is completed, the system becomes ready.

Expected console message:

```text
[CAL] OK etapa 2. listo
```

---

## 6. What Happens After Calibration

After calibration, the script starts estimating and sending three setpoints:

| Setpoint | Source | Meaning |
|---|---|---|
| `q_shoulder_rad` | IMU tilt | Shoulder flexion/extension |
| `q_elbow_rad` | EMG envelope | Elbow flexion/extension |
| `q_rot_rad` | Orientation quaternion | Shoulder/exoskeleton rotation |

All setpoints are sent in radians.

---

## 7. Recalibration

Press `R` to restart the calibration routine.

Recalibration is useful when:

- The Myo Armband moved on the arm.
- The initial posture was incorrect.
- The EMG baseline changed.
- The user changed position.
- The setpoints appear shifted or unstable.

---

## 8. Hold Mode

Press `Space` to activate or deactivate hold mode.

When hold mode is active, the current setpoints are frozen.

This can be useful for:

- Pausing the demo.
- Checking LabVIEW behavior.
- Avoiding unwanted setpoint changes during testing.

---

## 9. Stop the Demo

Press `Esc` to stop the demo.

When the demo stops, the script closes the session and saves the generated CSV and JSON files.

---

## 10. Practical Recommendations

For a more stable calibration:

- Place the Myo Armband firmly on the arm.
- Avoid moving during Stage 1.
- Keep the biceps contraction strong but controlled during Stage 2.
- Repeat calibration if the signal looks unstable.
- Check that Myo Connect is working correctly before starting.
- Check that the LabVIEW VI is already running before active control.

---

## 11. Common Calibration Problems

### Shoulder setpoint starts shifted

Possible causes:

- The arm was not relaxed during Stage 1.
- The initial posture was not correct.
- The Myo Armband moved.

Suggested solution:

```text
Press R and repeat calibration.
```

### Elbow setpoint does not reach high values

Possible causes:

- The maximum biceps contraction during Stage 2 was too weak.
- The Myo Armband was not detecting EMG correctly.
- The armband was not placed firmly.

Suggested solution:

```text
Repeat calibration with a stronger biceps contraction.
```

### Rotation setpoint appears inverted

Possible causes:

- The selected rotation sign is inverted.
- The fixed exoskeleton axis does not match the desired direction.

Suggested solution:

```text
Check SIGN_ROT and ROBOT_AXIS_WORLD in the Python script.
```

### Shoulder flexion appears inverted

Possible cause:

- The shoulder tilt sign is inverted.

Suggested solution:

```text
Check SIGN_SHO in the Python script.
```

---

## 12. Calibration Summary

| Stage | Duration | User Action | Estimated Values |
|---|---:|---|---|
| Stage 1 | ~2 s | Arm down and relaxed | Initial tilt, rest EMG, initial quaternion |
| Stage 2 | ~2 s | Strong biceps contraction | Maximum EMG envelope |
