"""
=============================================================================
Standalone HSV Color Calibrator for Invisibility Cloak
=============================================================================
Use this utility to fine-tune your cloth color detection.
- Click anywhere on the video to sample the cloth's HSV values automatically.
- Adjust sliders to fine-tune tolerance.
- Press 'TAB' to switch between Camera 0 and Camera 1.
- Press 'D' to test on the built-in demo video.
- Press 'S' to save the tuned color range into config.json!
=============================================================================
"""

import cv2
import numpy as np
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DEMO_VIDEO = os.path.join(BASE_DIR, "demo_cloak.mp4")

def empty_callback(x):
    pass

def open_working_camera(preferred=0):
    best_idx = preferred
    best_brightness = -1.0
    best_cap = None
    for idx in [preferred, 0 if preferred != 0 else 1]:
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            ret = False
            frame = None
            for _ in range(5):
                ret, frame = cap.read()
            if ret and frame is not None:
                brightness = float(frame.mean())
                if brightness > best_brightness:
                    if best_cap is not None:
                        best_cap.release()
                    best_brightness = brightness
                    best_idx = idx
                    best_cap = cap
                    continue
            cap.release()
    if best_cap is not None:
        return best_cap, best_idx
    return None, preferred

def main():
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
        except Exception:
            pass

    preferred_cam = config.get("camera_index", 1)
    is_demo = False
    cap, active_cam = open_working_camera(preferred_cam)
    if cap is None:
        print("[!] Live camera not found, opening demo video...")
        cap = cv2.VideoCapture(DEMO_VIDEO)
        is_demo = True

    win_name = "Cloth Color Calibrator"
    cv2.namedWindow(win_name, cv2.WINDOW_AUTOSIZE)

    init_lower = [0, 100, 70]
    init_upper = [15, 255, 255]
    if "presets" in config and "custom" in config["presets"]:
        init_lower = config["presets"]["custom"].get("lower1", init_lower)
        init_upper = config["presets"]["custom"].get("upper1", init_upper)

    cv2.createTrackbar("H_min", win_name, init_lower[0], 180, empty_callback)
    cv2.createTrackbar("H_max", win_name, init_upper[0], 180, empty_callback)
    cv2.createTrackbar("S_min", win_name, init_lower[1], 255, empty_callback)
    cv2.createTrackbar("S_max", win_name, init_upper[1], 255, empty_callback)
    cv2.createTrackbar("V_min", win_name, init_lower[2], 255, empty_callback)
    cv2.createTrackbar("V_max", win_name, init_upper[2], 255, empty_callback)

    last_frame = None

    def on_mouse(event, x, y, flags, param):
        nonlocal last_frame
        if event == cv2.EVENT_LBUTTONDOWN and last_frame is not None:
            h, w = last_frame.shape[:2]
            if x < w // 2:
                patch = last_frame[max(0, y - 3):min(h, y + 4), max(0, x - 3):min(w // 2, x + 4)]
                hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
                avg_h = int(np.median(hsv[:, :, 0]))
                avg_s = int(np.median(hsv[:, :, 1]))
                avg_v = int(np.median(hsv[:, :, 2]))

                if avg_v < 25 or avg_s < 15:
                    print("[!] Clicked region is too dark/black. Click on a well-lit colored cloth.")
                    return

                h_tol, s_tol, v_tol = 14, 60, 70
                cv2.setTrackbarPos("H_min", win_name, max(0, avg_h - h_tol))
                cv2.setTrackbarPos("H_max", win_name, min(180, avg_h + h_tol))
                cv2.setTrackbarPos("S_min", win_name, max(40, avg_s - s_tol))
                cv2.setTrackbarPos("S_max", win_name, min(255, avg_s + s_tol + 30))
                cv2.setTrackbarPos("V_min", win_name, max(35, avg_v - v_tol))
                cv2.setTrackbarPos("V_max", win_name, min(255, avg_v + v_tol + 40))
                print(f"[*] Sampled HSV: H={avg_h}, S={avg_s}, V={avg_v}. Sliders updated!")

    cv2.setMouseCallback(win_name, on_mouse)

    print("\n=======================================================")
    print("  CLOTH COLOR CALIBRATOR")
    print("=======================================================")
    print("  - Click on your cloth in the LEFT window to sample it.")
    print("  - Adjust trackbars to make the cloth completely WHITE on the RIGHT.")
    print("  - Press [TAB] to switch camera (Cam 0 <-> Cam 1)")
    print("  - Press [D] to switch to demo video")
    print("  - Press [S] to save to config.json.")
    print("  - Press [Q] or [ESC] to exit.")
    print("=======================================================\n")

    status_text = "Click cloth in left window | [TAB] Switch Cam | [D] Demo | [S] Save"

    while True:
        ret, frame = cap.read()
        if not ret:
            if is_demo:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            if not ret:
                break
        if not is_demo:
            frame = cv2.flip(frame, 1)

        h_min = cv2.getTrackbarPos("H_min", win_name)
        h_max = cv2.getTrackbarPos("H_max", win_name)
        s_min = cv2.getTrackbarPos("S_min", win_name)
        s_max = cv2.getTrackbarPos("S_max", win_name)
        v_min = cv2.getTrackbarPos("V_min", win_name)
        v_max = cv2.getTrackbarPos("V_max", win_name)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower = np.array([h_min, s_min, v_min], dtype=np.uint8)
        upper = np.array([h_max, s_max, v_max], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
        mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_DILATE, kernel, iterations=2)

        preview = frame.copy()
        preview[mask_clean > 0] = [0, 255, 0] # Highlight green

        mask_bgr = cv2.cvtColor(mask_clean, cv2.COLOR_GRAY2BGR)

        disp_w, disp_h = 640, 360
        left_view = cv2.resize(preview, (disp_w, disp_h))
        right_view = cv2.resize(mask_bgr, (disp_w, disp_h))

        combined = np.hstack([left_view, right_view])
        last_frame = combined

        source_label = "DEMO VIDEO" if is_demo else f"CAMERA {active_cam}"
        cv2.putText(combined, f"ORIGINAL + DETECTED [{source_label}]", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 255), 2)
        cv2.putText(combined, "FILTERED MASK (White = Cloak)", (disp_w + 20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 255), 2)
        cv2.putText(combined, status_text, (20, disp_h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)

        cv2.imshow(win_name, combined)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('\t'): # Switch camera
            cap.release()
            new_cam = 0 if active_cam == 1 else 1
            cap, active_cam = open_working_camera(new_cam)
            is_demo = False
            status_text = f"Switched to Camera {active_cam}!"
        elif key == ord('d') or key == ord('D'):
            cap.release()
            is_demo = not is_demo
            if is_demo:
                cap = cv2.VideoCapture(DEMO_VIDEO)
                status_text = "Switched to Demo Video!"
            else:
                cap, active_cam = open_working_camera(preferred_cam)
                status_text = f"Switched to Camera {active_cam}!"
        elif key == ord('s') or key == ord('S'):
            if "presets" not in config:
                config["presets"] = {}
            config["presets"]["custom"] = {
                "name": "Custom Tuned Cloth",
                "lower1": [h_min, s_min, v_min],
                "upper1": [h_max, s_max, v_max],
                "lower2": None,
                "upper2": None
            }
            config["active_preset"] = "custom"
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
            status_text = f"SAVED! Lower: [{h_min}, {s_min}, {v_min}] Upper: [{h_max}, {s_max}, {v_max}]"
            print(f"[+] {status_text}")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
