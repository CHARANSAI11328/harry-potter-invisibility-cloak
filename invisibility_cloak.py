"""
=============================================================================
Harry Potter Invisibility Cloak - Advanced OpenCV Implementation
=============================================================================
Features:
- Dynamic Color Presets (Red [double hue wrap], Blue, Green, Custom)
- Interactive Eyedropper: Click directly on your cloth to sample the color!
- Live HSV Calibration Sliders (press 'c' to open calibration panel)
- Median Frame Background Capture: 30-frame noise-free background plate
- Feathered Alpha Blending: Seamless Gaussian edge blending (no harsh pixels)
- Picture-in-Picture (PiP) Mask Monitor: See what is being detected in real time
- Snapshot Capture ('s' key) & On-Screen Display HUD ('h' key)
=============================================================================
"""

import cv2
import numpy as np
import json
import os
import sys
import time
import argparse

# Suppress stderr noise if any
os.environ["PYTHONWARNINGS"] = "ignore"

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

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
                "lower1": [95, 80, 60],
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
                "upper1": [20, 255, 255],
                "lower2": None,
                "upper2": None
            }
        },
        "camera_index": 0,
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
    def __init__(self, camera_index=0, video_path=None):
        self.config = load_config()
        self.active_preset_key = self.config.get("active_preset", "red")
        self.active_preset = self.config["presets"].get(self.active_preset_key, self.config["presets"]["red"])
        
        self.camera_index = camera_index if video_path is None else video_path
        self.cap = None
        self.background = None
        self.show_hud = True
        self.pip_mode = True       # Picture-in-picture mask view
        self.show_calibrator = False
        self.freeze_frame = False
        self.status_msg = "Press 'b' to recapture background | Click on cloth to sample color"
        self.status_timer = time.time() + 5.0
        
        self.window_name = "Harry Potter Invisibility Cloak"
        self.calib_window = "Color Tuning (HSV)"
        
        # Click sample state
        self.click_sampled_hsv = None

    def open_camera(self):
        print(f"[*] Opening video capture device: {self.camera_index}")
        if isinstance(self.camera_index, int):
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_index)
        else:
            self.cap = cv2.VideoCapture(self.camera_index)
            
        if not self.cap.isOpened():
            print(f"[!] Error: Could not open camera {self.camera_index}.")
            return False
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        return True

    def capture_background_countdown(self, countdown_sec=3, num_frames=30):
        """
        Gives the user a visual countdown on the live feed to step out of view,
        then averages multiple frames to get a pristine, noise-free background plate.
        """
        print("[*] Starting background capture countdown...")
        start_time = time.time()
        
        while time.time() - start_time < countdown_sec:
            ret, frame = self.cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            time_left = countdown_sec - int(time.time() - start_time)
            
            # Draw prominent countdown overlay
            overlay = frame.copy()
            h, w = frame.shape[:2]
            cv2.rectangle(overlay, (0, 0), (w, 140), (20, 20, 20), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            
            cv2.putText(frame, "STEP OUT OF THE CAMERA VIEW!", (int(w * 0.15), 50),
                        cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 215, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, f"Capturing reference background in: {time_left}s", (int(w * 0.22), 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
            
            cv2.imshow(self.window_name, frame)
            if cv2.waitKey(30) & 0xFF == ord('q'):
                return False

        # Now collect frames for median filtering
        frames = []
        for i in range(num_frames):
            ret, frame = self.cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            frames.append(frame)
            
            # Progress bar
            progress = int((i + 1) / num_frames * (w - 200))
            prog_frame = frame.copy()
            cv2.rectangle(prog_frame, (100, h // 2 - 30), (w - 100, h // 2 + 30), (40, 40, 40), -1)
            cv2.rectangle(prog_frame, (100, h // 2 - 20), (100 + progress, h // 2 + 20), (0, 215, 255), -1)
            cv2.putText(prog_frame, "Analyzing background plate...", (120, h // 2 + 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.imshow(self.window_name, prog_frame)
            cv2.waitKey(20)

        if len(frames) > 0:
            # Median along temporal axis cleans all shadows/flicker
            self.background = np.median(frames, axis=0).astype(np.uint8)
            self.status_msg = "Background captured successfully! Put on your cloak."
            self.status_timer = time.time() + 4.0
            print("[+] Background successfully captured and locked!")
            return True
        return False

    def on_mouse_click(self, event, x, y, flags, param):
        """
        Eyedropper tool: Click anywhere on the cloak to automatically calculate
        and tune HSV bounds around that exact shade!
        """
        if event == cv2.EVENT_LBUTTONDOWN and self.last_frame is not None:
            # Get 7x7 patch around click to avoid single-pixel noise
            h, w = self.last_frame.shape[:2]
            x_min, x_max = max(0, x - 3), min(w, x + 4)
            y_min, y_max = max(0, y - 3), min(h, y + 4)
            patch = self.last_frame[y_min:y_max, x_min:x_max]
            
            hsv_patch = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
            avg_h = int(np.median(hsv_patch[:, :, 0]))
            avg_s = int(np.median(hsv_patch[:, :, 1]))
            avg_v = int(np.median(hsv_patch[:, :, 2]))
            
            h_tol = 14
            s_tol = 65
            v_tol = 75
            
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
            self.status_timer = time.time() + 5.0
            
            # Update trackbars if calibrator window is active
            if self.show_calibrator:
                self.update_trackbar_positions()

    def set_preset(self, key):
        if key in self.config["presets"]:
            self.active_preset_key = key
            self.active_preset = self.config["presets"][key]
            self.config["active_preset"] = key
            self.status_msg = f"Preset switched to: {self.active_preset['name']}"
            self.status_timer = time.time() + 3.0
            if self.show_calibrator:
                self.update_trackbar_positions()

    def get_cloak_mask(self, hsv):
        """
        Creates a clean, filtered mask for the cloak.
        Handles dual-range (e.g. red wrap-around) and single-range colors.
        """
        lower1 = np.array(self.active_preset["lower1"], dtype=np.uint8)
        upper1 = np.array(self.active_preset["upper1"], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower1, upper1)
        
        if self.active_preset.get("lower2") is not None and self.active_preset.get("upper2") is not None:
            lower2 = np.array(self.active_preset["lower2"], dtype=np.uint8)
            upper2 = np.array(self.active_preset["upper2"], dtype=np.uint8)
            mask2 = cv2.inRange(hsv, lower2, upper2)
            mask = mask | mask2
            
        # Morphological operations to clean small noise & expand edges slightly
        k_size = self.config.get("morph_kernel_size", 3)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
        
        open_iter = self.config.get("open_iterations", 2)
        dilate_iter = self.config.get("dilate_iterations", 2)
        
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=open_iter)
        mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations=dilate_iter)
        return mask

    def apply_cloak_effect(self, current_frame, mask):
        """
        Feathered Alpha Blending:
        Instead of harsh pixel cuts, we apply a subtle Gaussian blur to the mask edges
        and blend the background into the live frame smoothly.
        """
        blur_size = self.config.get("feather_blur_size", 7)
        if blur_size % 2 == 0:
            blur_size += 1
            
        feathered_mask = cv2.GaussianBlur(mask, (blur_size, blur_size), 0)
        
        # Convert to 0.0 - 1.0 float alpha channel
        alpha = (feathered_mask.astype(np.float32) / 255.0)[:, :, np.newaxis]
        
        # Blend: Cloak area receives background, non-cloak area receives current frame
        blended = (self.background * alpha + current_frame * (1.0 - alpha)).astype(np.uint8)
        return blended

    def draw_hud(self, img, fps, mask):
        """Draws the magical Harry Potter themed Heads-Up Display."""
        h, w = img.shape[:2]
        
        # Top banner
        header = img.copy()
        cv2.rectangle(header, (0, 0), (w, 54), (15, 15, 25), -1)
        cv2.addWeighted(header, 0.75, img, 0.25, 0, img)
        
        # Title
        cv2.putText(img, "HARRY POTTER INVISIBILITY CLOAK", (20, 34),
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 215, 255), 2, cv2.LINE_AA)
        
        # Active preset tag
        tag = f"Mode: {self.active_preset['name']}"
        cv2.putText(img, tag, (w - 380, 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (100, 255, 150), 2, cv2.LINE_AA)
        
        # FPS
        cv2.putText(img, f"{int(fps)} FPS", (w - 80, 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1, cv2.LINE_AA)
        
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
        controls = "[1] Red  [2] Blue  [3] Green  [4] Custom  |  [B] New BG  |  [C] Calibrator  |  [M] Mask PiP  |  [S] Save  |  [Q] Exit"
        cv2.putText(img, controls, (20, h - 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (210, 210, 210), 1, cv2.LINE_AA)

        # Picture-in-Picture Mask thumbnail
        if self.pip_mode:
            pip_w = 220
            pip_h = int(pip_w * (h / w))
            pip_x = w - pip_w - 20
            pip_y = 65
            
            mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            # Tint detected cloak green in the monitor
            mask_color[:, :, 0] = 0
            mask_color[:, :, 2] = 0
            
            pip_small = cv2.resize(mask_color, (pip_w, pip_h))
            cv2.rectangle(img, (pip_x - 3, pip_y - 3), (pip_x + pip_w + 3, pip_y + pip_h + 3), (0, 215, 255), 2)
            img[pip_y:pip_y + pip_h, pip_x:pip_x + pip_w] = pip_small
            cv2.putText(img, "CLOAK MASK MONITOR", (pip_x + 5, pip_y - 8),
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
        if not self.open_camera():
            return

        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.on_mouse_click)

        # 1. Capture initial background plate
        success = self.capture_background_countdown(countdown_sec=3, num_frames=30)
        if not success:
            print("[!] Background capture cancelled or failed.")
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
        print("   - [Click] Click directly on your cloth with mouse to auto-tune!")
        print("   - [B] Recapture background plate (step out when countdown starts)")
        print("   - [C] Open/Close live HSV Trackbar calibration window")
        print("   - [M] Toggle Picture-in-Picture mask monitor")
        print("   - [S] Save photo / screenshot")
        print("   - [H] Hide/Show on-screen HUD")
        print("   - [Q] or [ESC] to Quit")
        print("=======================================================\n")

        self.last_frame = None

        while True:
            curr_time = time.time()
            fps = 1.0 / max(curr_time - prev_time, 0.001)
            prev_time = curr_time

            if not self.freeze_frame:
                ret, frame = self.cap.read()
                if not ret:
                    print("[!] End of video or failed to read frame.")
                    break
                frame = cv2.flip(frame, 1)
                self.last_frame = frame.copy()
            else:
                frame = self.last_frame.copy()

            if self.show_calibrator:
                self.read_calibrator_trackbars()

            # Ensure background matches current frame size
            if self.background.shape != frame.shape:
                self.background = cv2.resize(self.background, (frame.shape[1], frame.shape[0]))

            # Convert to HSV & produce mask
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = self.get_cloak_mask(hsv)

            # Apply smooth invisibility effect
            output = self.apply_cloak_effect(frame, mask)

            # Overlay HUD
            if self.show_hud:
                self.draw_hud(output, fps, mask)

            cv2.imshow(self.window_name, output)

            # Key handling
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 27:   # Quit
                break
            elif key == ord('1'):
                self.set_preset("red")
            elif key == ord('2'):
                self.set_preset("blue")
            elif key == ord('3'):
                self.set_preset("green")
            elif key == ord('4'):
                self.set_preset("custom")
            elif key == ord('b') or key == ord('B'):
                self.capture_background_countdown(countdown_sec=3, num_frames=25)
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
                save_dir = os.path.join(os.path.dirname(__file__), "snapshots")
                os.makedirs(save_dir, exist_ok=True)
                filename = os.path.join(save_dir, f"invisibility_{timestamp}.jpg")
                cv2.imwrite(filename, output)
                self.status_msg = f"Saved snapshot to snapshots/invisibility_{timestamp}.jpg"
                self.status_timer = time.time() + 4.0
                print(f"[+] Snapshot saved: {filename}")
            elif key == ord('p') or key == ord('P'):
                self.freeze_frame = not self.freeze_frame

        save_config(self.config)
        self.cap.release()
        cv2.destroyAllWindows()
        print("[*] Application exited cleanly.")

def main():
    parser = argparse.ArgumentParser(description="Harry Potter Invisibility Cloak with OpenCV")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    parser.add_argument("--video", type=str, default=None, help="Path to video file instead of webcam")
    args = parser.parse_args()

    app = InvisibilityCloak(camera_index=args.camera, video_path=args.video)
    app.run()

if __name__ == "__main__":
    main()
