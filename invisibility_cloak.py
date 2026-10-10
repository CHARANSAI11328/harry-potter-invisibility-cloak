"""
=============================================================================
Harry Potter Invisibility Cloak - Advanced OpenCV Implementation
=============================================================================
Features:
- Auto Camera Discovery & Live Switching (Press TAB to switch Camera 0 <-> 1)
- Built-in Interactive Demo Mode (Press 'D' to test with Hogwarts demo video)
- Smart Black-Screen Detector & Guided Help Overlay
- Dynamic Color Presets (Red [double hue wrap], Blue, Green, Custom)
- Interactive Eyedropper: Click directly on your cloth to auto-sample color
- Live HSV Calibration Sliders (press 'C' to open live tuning panel)
- Median Frame Background Capture: 30-frame noise-free background plate
- Feathered Alpha Blending: Seamless Gaussian edge blending (no harsh pixels)
- Picture-in-Picture (PiP) Mask Monitor: Real-time detection monitor ('M')
- Snapshot Capture ('S' key) & On-Screen Display HUD ('H' key)
=============================================================================
"""

import cv2
import numpy as np
import json
import os
import sys
import time
import argparse

# Suppress stderr warnings
os.environ["PYTHONWARNINGS"] = "ignore"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DEMO_VIDEO = os.path.join(BASE_DIR, "demo_cloak.mp4")
DEMO_BG = os.path.join(BASE_DIR, "demo_background.jpg")

def load_config():
    default_config = {
        "active_preset": "red",
        "presets": {
            "red": {
                "name": "Red Cloak",
                "lower1": [0, 120, 70],
                "upper1": [10, 255, 255],
                "lower2": [170, 120, 70],
                "upper2": [180, 255, 255]
            },
            "blue": {
                "name": "Blue Cloak",
                "lower1": [90, 80, 50],
                "upper1": [130, 255, 255],
                "lower2": None,
                "upper2": None
            },
            "green": {
                "name": "Green Cloak",
                "lower1": [35, 60, 50],
                "upper1": [85, 255, 255],
                "lower2": None,
                "upper2": None
            },
            "custom": {
                "name": "Custom Tuned",
                "lower1": [0, 100, 70],
                "upper1": [15, 255, 255],
                "lower2": None,
                "upper2": None
            }
        },
        "camera_index": 1,
        "morph_kernel_size": 3,
        "open_iterations": 2,
        "dilate_iterations": 2,
        "feather_blur_size": 7
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
                default_config.update(saved)
        except Exception:
            pass
    return default_config

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save config: {e}")

class InvisibilityCloak:
    def __init__(self, camera_index=None, video_path=None, start_demo=False):
        self.config = load_config()
        self.active_preset_key = self.config.get("active_preset", "red")
        if self.active_preset_key not in self.config["presets"]:
            self.active_preset_key = "red"
        self.active_preset = self.config["presets"][self.active_preset_key]
        
        # Camera configuration
        self.preferred_camera = camera_index if camera_index is not None else self.config.get("camera_index", 1)
        self.current_camera_index = self.preferred_camera
        self.video_path = video_path
        self.is_demo_mode = start_demo or (video_path is not None)
        
        self.cap = None
        self.background = None
        self.show_hud = True
        self.pip_mode = True
        self.show_calibrator = False
        self.freeze_frame = False
        
        self.status_msg = "Ready! Step out when countdown starts | Press 'B' to recapture BG"
        self.status_timer = time.time() + 6.0
        
        self.window_name = "Harry Potter Invisibility Cloak"
        self.calib_window = "Color Tuning (HSV)"
        self.last_frame = None
        self.dark_frame_counter = 0

    def find_working_camera(self):
        """Attempts preferred camera, and falls back to other camera indices."""
        indices = [self.preferred_camera]
        for alt in [1, 0, 2]:
            if alt not in indices:
                indices.append(alt)
                
        for idx in indices:
            print(f"[*] Testing camera index {idx}...")
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                # Read warm-up frames
                ret = False
                for _ in range(5):
                    ret, test_frame = cap.read()
                if ret and test_frame is not None:
                    cap.release()
                    print(f"[+] Found working camera at index {idx}!")
                    return idx
                cap.release()
        return self.preferred_camera

    def open_video_source(self):
        if self.is_demo_mode:
            target = self.video_path if self.video_path else DEMO_VIDEO
            if not os.path.exists(target):
                print(f"[*] Demo video not found at {target}, generating demo video...")
                try:
                    from create_demo_video import generate_demo_video
                    generate_demo_video()
                except Exception as e:
                    print(f"[!] Could not generate demo: {e}")
            print(f"[*] Opening demo video source: {target}")
            self.cap = cv2.VideoCapture(target)
            return self.cap.isOpened()
        
        # Open live webcam
        self.current_camera_index = self.find_working_camera()
        print(f"[*] Opening live camera index: {self.current_camera_index}")
        self.cap = cv2.VideoCapture(self.current_camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.current_camera_index)
            
        if not self.cap.isOpened():
            print(f"[!] Error: Could not open camera {self.current_camera_index}.")
            return False
            
        # Try setting 1280x720 (if supported)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Warmup sensor so auto-exposure stabilizes
        for _ in range(10):
            self.cap.read()
            
        return True

    def switch_camera(self):
        """Toggles between Camera 0 and Camera 1 on the fly."""
        if self.is_demo_mode:
            self.is_demo_mode = False
            self.status_msg = "Switched to Live Camera!"
        else:
            new_idx = 0 if self.current_camera_index == 1 else 1
            self.current_camera_index = new_idx
            self.config["camera_index"] = new_idx
            save_config(self.config)
            self.status_msg = f"Switched to Camera {new_idx}!"
            
        if self.cap is not None:
            self.cap.release()
            
        self.open_video_source()
        self.capture_background_countdown(countdown_sec=2, num_frames=20)
        self.status_timer = time.time() + 4.0

    def toggle_demo_mode(self):
        """Switches between live camera and demo video."""
        self.is_demo_mode = not self.is_demo_mode
        if self.cap is not None:
            self.cap.release()
        self.open_video_source()
        if self.is_demo_mode:
            self.status_msg = "DEMO MODE ACTIVE: Testing with Hogwarts video!"
        else:
            self.status_msg = "LIVE CAMERA ACTIVE!"
        self.status_timer = time.time() + 4.0
        self.capture_background_countdown(countdown_sec=1, num_frames=15)

    def capture_background_countdown(self, countdown_sec=3, num_frames=25):
        """
        Visual countdown on screen.
        If camera is black, falls back to demo room plate so user is never stuck in darkness!
        """
        print("[*] Capturing background plate...")
        start_time = time.time()
        
        while time.time() - start_time < countdown_sec:
            ret, frame = self.cap.read()
            if not ret:
                if self.is_demo_mode:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
                if not ret:
                    continue
            if not self.is_demo_mode:
                frame = cv2.flip(frame, 1)
                
            time_left = max(0, countdown_sec - int(time.time() - start_time))
            h, w = frame.shape[:2]
            
            # Prominent banner
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 140), (20, 20, 25), -1)
            cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
            
            cv2.putText(frame, "STEP OUT OF THE CAMERA VIEW!", (int(w * 0.15), 50),
                        cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 215, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, f"Capturing reference background in: {time_left}s", (int(w * 0.22), 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
            
            cv2.imshow(self.window_name, frame)
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q') or key == 27:
                return False

        # Collect frames for median
        frames = []
        for i in range(num_frames):
            ret, frame = self.cap.read()
            if not ret:
                if self.is_demo_mode:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
                if not ret:
                    continue
            if not self.is_demo_mode:
                frame = cv2.flip(frame, 1)
            frames.append(frame)
            cv2.waitKey(10)

        if len(frames) > 0:
            bg_plate = np.median(frames, axis=0).astype(np.uint8)
            # If camera captured pitch black, fall back to virtual room background!
            if bg_plate.mean() < 2.5 and os.path.exists(DEMO_BG):
                print("[!] Camera is black! Loading Hogwarts fallback background plate...")
                fallback_bg = cv2.imread(DEMO_BG)
                if fallback_bg is not None:
                    h, w = bg_plate.shape[:2]
                    self.background = cv2.resize(fallback_bg, (w, h))
                    self.status_msg = "Note: Camera is dark. Using room background plate."
                    self.status_timer = time.time() + 5.0
                    return True
            self.background = bg_plate
            self.status_msg = "Background locked! Put on your cloak."
            self.status_timer = time.time() + 4.0
            return True
        return False

    def on_mouse_click(self, event, x, y, flags, param):
        """Eyedropper: Left-click cloth on screen to lock in custom color."""
        if event == cv2.EVENT_LBUTTONDOWN and self.last_frame is not None:
            h, w = self.last_frame.shape[:2]
            x_min, x_max = max(0, x - 3), min(w, x + 4)
            y_min, y_max = max(0, y - 3), min(h, y + 4)
            patch = self.last_frame[y_min:y_max, x_min:x_max]
            
            hsv_patch = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
            avg_h = int(np.median(hsv_patch[:, :, 0]))
            avg_s = int(np.median(hsv_patch[:, :, 1]))
            avg_v = int(np.median(hsv_patch[:, :, 2]))
            
            # Check if clicked pixel is pitch black or unlit
            if avg_v < 25 or avg_s < 15:
                self.status_msg = "Clicked area is too dark/black! Click a well-lit colored cloth."
                self.status_timer = time.time() + 4.0
                return

            h_tol, s_tol, v_tol = 14, 65, 75
            lower_h = max(0, avg_h - h_tol)
            upper_h = min(180, avg_h + h_tol)
            lower_s = max(40, avg_s - s_tol)
            upper_s = min(255, avg_s + s_tol + 40)
            lower_v = max(35, avg_v - v_tol)
            upper_v = min(255, avg_v + v_tol + 50)
            
            self.config["presets"]["custom"] = {
                "name": f"Eyedropper (H:{avg_h} S:{avg_s} V:{avg_v})",
                "lower1": [lower_h, lower_s, lower_v],
                "upper1": [upper_h, upper_s, upper_v],
                "lower2": None,
                "upper2": None
            }
            self.set_preset("custom")
            save_config(self.config)
            self.status_msg = f"Cloth sampled! HSV: ({avg_h}, {avg_s}, {avg_v}) -> Custom Preset active"
            self.status_timer = time.time() + 4.0

    def set_preset(self, key):
        if key in self.config["presets"]:
            self.active_preset_key = key
            self.active_preset = self.config["presets"][key]
            self.config["active_preset"] = key
            save_config(self.config)
            self.status_msg = f"Preset switched to: {self.active_preset['name']}"
            self.status_timer = time.time() + 3.0
            if self.show_calibrator:
                self.update_trackbar_positions()

    def get_cloak_mask(self, hsv):
        lower1 = np.array(self.active_preset["lower1"], dtype=np.uint8)
        upper1 = np.array(self.active_preset["upper1"], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower1, upper1)
        
        if self.active_preset.get("lower2") is not None and self.active_preset.get("upper2") is not None:
            lower2 = np.array(self.active_preset["lower2"], dtype=np.uint8)
            upper2 = np.array(self.active_preset["upper2"], dtype=np.uint8)
            mask2 = cv2.inRange(hsv, lower2, upper2)
            mask = mask | mask2
            
        k_size = self.config.get("morph_kernel_size", 3)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
        open_iter = self.config.get("open_iterations", 2)
        dilate_iter = self.config.get("dilate_iterations", 2)
        
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=open_iter)
        mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations=dilate_iter)
        return mask

    def apply_cloak_effect(self, current_frame, mask):
        blur_size = self.config.get("feather_blur_size", 7)
        if blur_size % 2 == 0:
            blur_size += 1
            
        feathered_mask = cv2.GaussianBlur(mask, (blur_size, blur_size), 0)
        alpha = (feathered_mask.astype(np.float32) / 255.0)[:, :, np.newaxis]
        
        blended = (self.background * alpha + current_frame * (1.0 - alpha)).astype(np.uint8)
        return blended

    def draw_hud(self, img, fps, mask, mean_brightness):
        h, w = img.shape[:2]
        
        # Top banner
        header = img.copy()
        cv2.rectangle(header, (0, 0), (w, 54), (15, 15, 25), -1)
        cv2.addWeighted(header, 0.75, img, 0.25, 0, img)
        
        # Title
        cv2.putText(img, "HARRY POTTER INVISIBILITY CLOAK", (20, 34),
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 215, 255), 2, cv2.LINE_AA)
        
        # Source tag (Live Cam vs Demo)
        src_tag = "DEMO VIDEO" if self.is_demo_mode else f"CAM {self.current_camera_index}"
        cv2.putText(img, f"[{src_tag}]", (w - 480, 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 50), 2, cv2.LINE_AA)
                    
        # Active preset tag
        tag = f"Mode: {self.active_preset['name']}"
        cv2.putText(img, tag, (w - 340, 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 150), 2, cv2.LINE_AA)
        
        # FPS
        cv2.putText(img, f"{int(fps)} FPS", (w - 75, 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1, cv2.LINE_AA)
        
        # Black Screen Alert Dialog
        if mean_brightness < 2.5 and not self.is_demo_mode:
            self.dark_frame_counter += 1
        else:
            self.dark_frame_counter = 0

        if self.dark_frame_counter > 15: # Dark for >0.5s
            card_w, card_h = 760, 220
            cx, cy = (w - card_w) // 2, (h - card_h) // 2
            card = img.copy()
            cv2.rectangle(card, (cx, cy), (cx + card_w, cy + card_h), (10, 15, 35), -1)
            cv2.rectangle(card, (cx, cy), (cx + card_w, cy + card_h), (0, 100, 255), 3)
            cv2.addWeighted(card, 0.88, img, 0.12, 0, img)
            
            cv2.putText(img, "CAMERA FEED IS PITCH BLACK!", (cx + 30, cy + 42),
                        cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 120, 255), 2, cv2.LINE_AA)
            cv2.putText(img, "1. Open your laptop's camera privacy shutter (slider above lens)", (cx + 30, cy + 85),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(img, "2. Check Camera Privacy Key (F9 or Fn+F9 on HP keyboards)", (cx + 30, cy + 118),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(img, "3. Press [TAB] to switch camera (Cam 0 <-> Cam 1)", (cx + 30, cy + 151),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.62, (100, 255, 150), 2, cv2.LINE_AA)
            cv2.putText(img, "4. Press [D] to switch to Hogwarts Demo Video immediately!", (cx + 30, cy + 184),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 230, 255), 2, cv2.LINE_AA)

        # Status Toast Bar
        if time.time() < self.status_timer:
            toast = img.copy()
            cv2.rectangle(toast, (0, h - 85), (w, h - 45), (10, 10, 20), -1)
            cv2.addWeighted(toast, 0.8, img, 0.2, 0, img)
            cv2.putText(img, self.status_msg, (25, h - 58),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 240, 255), 2, cv2.LINE_AA)
        
        # Controls Bar at Bottom
        ctrl_bar = img.copy()
        cv2.rectangle(ctrl_bar, (0, h - 42), (w, h), (10, 10, 15), -1)
        cv2.addWeighted(ctrl_bar, 0.85, img, 0.15, 0, img)
        controls = "[1] Red [2] Blue [3] Green [4] Custom | [TAB] Switch Cam | [D] Demo | [B] New BG | [C] Tune | [S] Save | [Q] Quit"
        cv2.putText(img, controls, (15, h - 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (215, 215, 215), 1, cv2.LINE_AA)

        # Picture-in-Picture Mask monitor
        if self.pip_mode:
            pip_w = 210
            pip_h = int(pip_w * (h / w))
            pip_x = w - pip_w - 20
            pip_y = 65
            
            mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            mask_color[:, :, 0] = 0
            mask_color[:, :, 2] = 0 # Tint green
            
            pip_small = cv2.resize(mask_color, (pip_w, pip_h))
            cv2.rectangle(img, (pip_x - 3, pip_y - 3), (pip_x + pip_w + 3, pip_y + pip_h + 3), (0, 215, 255), 2)
            img[pip_y:pip_y + pip_h, pip_x:pip_x + pip_w] = pip_small
            cv2.putText(img, "CLOAK MONITOR", (pip_x + 5, pip_y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 215, 255), 1, cv2.LINE_AA)

    # ----------------- Interactive Trackbar Calibrator -----------------
    def empty_callback(self, val):
        pass

    def setup_calibrator_window(self):
        cv2.namedWindow(self.calib_window, cv2.WINDOW_AUTOSIZE)
        cv2.createTrackbar("Hue Min", self.calib_window, 0, 180, self.empty_callback)
        cv2.createTrackbar("Hue Max", self.calib_window, 180, 180, self.empty_callback)
        cv2.createTrackbar("Sat Min", self.calib_window, 0, 255, self.empty_callback)
        cv2.createTrackbar("Sat Max", self.calib_window, 255, 255, self.empty_callback)
        cv2.createTrackbar("Val Min", self.calib_window, 0, 255, self.empty_callback)
        cv2.createTrackbar("Val Max", self.calib_window, 255, 255, self.empty_callback)
        cv2.createTrackbar("Feather Blur", self.calib_window, self.config.get("feather_blur_size", 7), 25, self.empty_callback)
        self.update_trackbar_positions()

    def update_trackbar_positions(self):
        if not self.show_calibrator:
            return
        l = self.active_preset["lower1"]
        u = self.active_preset["upper1"]
        cv2.setTrackbarPos("Hue Min", self.calib_window, int(l[0]))
        cv2.setTrackbarPos("Hue Max", self.calib_window, int(u[0]))
        cv2.setTrackbarPos("Sat Min", self.calib_window, int(l[1]))
        cv2.setTrackbarPos("Sat Max", self.calib_window, int(u[1]))
        cv2.setTrackbarPos("Val Min", self.calib_window, int(l[2]))
        cv2.setTrackbarPos("Val Max", self.calib_window, int(u[2]))

    def read_calibrator_trackbars(self):
        if not self.show_calibrator:
            return
        h_min = cv2.getTrackbarPos("Hue Min", self.calib_window)
        h_max = cv2.getTrackbarPos("Hue Max", self.calib_window)
        s_min = cv2.getTrackbarPos("Sat Min", self.calib_window)
        s_max = cv2.getTrackbarPos("Sat Max", self.calib_window)
        v_min = cv2.getTrackbarPos("Val Min", self.calib_window)
        v_max = cv2.getTrackbarPos("Val Max", self.calib_window)
        blur = cv2.getTrackbarPos("Feather Blur", self.calib_window)
        
        self.active_preset["lower1"] = [h_min, s_min, v_min]
        self.active_preset["upper1"] = [h_max, s_max, v_max]
        if blur % 2 == 1 and blur >= 1:
            self.config["feather_blur_size"] = blur

    # ----------------------------- Main Loop -----------------------------
    def run(self):
        if not self.open_video_source():
            print("[!] Could not open video source.")
            return

        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.on_mouse_click)

        # 1. Capture initial background plate
        success = self.capture_background_countdown(countdown_sec=2, num_frames=20)
        if not success:
            print("[!] Background capture cancelled or window closed.")
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()
            return

        prev_time = time.time()
        fps = 30.0

        print("\n=======================================================")
        print("  HARRY POTTER INVISIBILITY CLOAK IS RUNNING!")
        print("=======================================================")
        print("  Controls:")
        print("   - [1] Switch to RED cloak preset")
        print("   - [2] Switch to BLUE cloak preset")
        print("   - [3] Switch to GREEN cloak preset")
        print("   - [4] Switch to CUSTOM tuned preset")
        print("   - [TAB] Switch between Camera 0 and Camera 1")
        print("   - [D] Toggle Hogwarts Demo Video Mode")
        print("   - [Click] Left-click cloth on screen to auto-tune!")
        print("   - [B] Recapture background plate")
        print("   - [C] Open/Close live HSV Trackbar calibration window")
        print("   - [M] Toggle Picture-in-Picture mask monitor")
        print("   - [S] Save photo / screenshot")
        print("   - [H] Hide/Show on-screen HUD")
        print("   - [Q] or [ESC] to Quit")
        print("=======================================================\n")

        while True:
            curr_time = time.time()
            fps = 1.0 / max(curr_time - prev_time, 0.001)
            prev_time = curr_time

            if not self.freeze_frame:
                ret, frame = self.cap.read()
                if not ret:
                    if self.is_demo_mode:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = self.cap.read()
                    if not ret:
                        print("[!] Failed to read video frame.")
                        break
                        
                if not self.is_demo_mode:
                    frame = cv2.flip(frame, 1)
                self.last_frame = frame.copy()
            else:
                frame = self.last_frame.copy()

            if self.show_calibrator:
                self.read_calibrator_trackbars()

            if self.background is None or self.background.shape != frame.shape:
                if self.background is None and os.path.exists(DEMO_BG):
                    self.background = cv2.imread(DEMO_BG)
                if self.background is not None:
                    self.background = cv2.resize(self.background, (frame.shape[1], frame.shape[0]))
                else:
                    self.background = frame.copy()

            mean_brightness = float(frame.mean())

            # Convert to HSV & produce mask
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = self.get_cloak_mask(hsv)

            # Apply smooth invisibility effect
            output = self.apply_cloak_effect(frame, mask)

            # Overlay HUD & Diagnostics
            if self.show_hud:
                self.draw_hud(output, fps, mask, mean_brightness)

            cv2.imshow(self.window_name, output)

            # Key handling
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 27:
                break
            elif key == ord('\t'):  # TAB key to switch camera
                self.switch_camera()
            elif key == ord('d') or key == ord('D'):  # Demo video toggle
                self.toggle_demo_mode()
            elif key == ord('1'):
                self.set_preset("red")
            elif key == ord('2'):
                self.set_preset("blue")
            elif key == ord('3'):
                self.set_preset("green")
            elif key == ord('4'):
                self.set_preset("custom")
            elif key == ord('b') or key == ord('B'):
                self.capture_background_countdown(countdown_sec=2, num_frames=20)
            elif key == ord('c') or key == ord('C'):
                self.show_calibrator = not self.show_calibrator
                if self.show_calibrator:
                    self.setup_calibrator_window()
                else:
                    cv2.destroyWindow(self.calib_window)
            elif key == ord('m') or key == ord('M'):
                self.pip_mode = not self.pip_mode
            elif key == ord('h') or key == ord('H'):
                self.show_hud = not self.show_hud
            elif key == ord('s') or key == ord('S'):
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                save_dir = os.path.join(BASE_DIR, "snapshots")
                os.makedirs(save_dir, exist_ok=True)
                filename = os.path.join(save_dir, f"invisibility_{timestamp}.jpg")
                cv2.imwrite(filename, output)
                self.status_msg = f"Saved snapshot to snapshots/invisibility_{timestamp}.jpg"
                self.status_timer = time.time() + 4.0
                print(f"[+] Snapshot saved: {filename}")
            elif key == ord('p') or key == ord('P'):
                self.freeze_frame = not self.freeze_frame

        save_config(self.config)
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("[*] Application exited cleanly.")

def main():
    parser = argparse.ArgumentParser(description="Harry Potter Invisibility Cloak with OpenCV")
    parser.add_argument("--camera", type=int, default=None, help="Camera index (default: auto)")
    parser.add_argument("--video", type=str, default=None, help="Path to video file instead of webcam")
    parser.add_argument("--demo", action="store_true", help="Launch directly in Hogwarts demo mode")
    args = parser.parse_args()

    app = InvisibilityCloak(camera_index=args.camera, video_path=args.video, start_demo=args.demo)
    app.run()

if __name__ == "__main__":
    main()
