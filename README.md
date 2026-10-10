# 🧙‍♂️ Harry Potter Invisibility Cloak (OpenCV)

An advanced, real-time Computer Vision implementation of Harry Potter's Invisibility Cloak using **OpenCV** and **Python**.

This project isolates a specific color of fabric (cloak/sheet/towel) using the **HSV (Hue, Saturation, Value)** color space and replaces it seamlessly with a pre-recorded reference background plate.

---

## ⚡ What Makes This Implementation "Effective"?

Standard tutorials often flicker, exhibit jagged pixelated borders, or fail completely when your cloth isn't an exact shade of red. This implementation solves all of those issues:

1. **30-Frame Median Background Plate**: Eliminates camera sensor grain, auto-exposure flicker, and transient shadows by calculating the temporal median across 30 frames with an on-screen visual countdown.
2. **Feathered Alpha Blending**: Instead of harsh binary pixel cuts (`bitwise_and`), it applies a Gaussian blur to the mask edges and performs float alpha blending. This yields smooth, cinematic Hollywood-style transitions.
3. **Interactive Eyedropper Sampling**: Don't know the exact HSV numbers? Simply **left-click on your cloth directly on the webcam screen** to auto-sample the hue and compute optimized bounds!
4. **Live HSV Calibration Sliders**: Press `c` at any time to open real-time trackbars and fine-tune detection without restarting the code.
5. **Color Presets**: Instant switching between **Red** (with dual 0-10 & 170-180 hue wrap), **Blue**, **Green**, and **Custom**.
6. **Picture-in-Picture (PiP) Mask Monitor**: A real-time thumbnail monitor in the corner shows you exactly what pixels are being masked out.

---

## 📁 Project Structure

```
d:\ml-workshop\games_dev\harry_potter_cloak\
├── invisibility_cloak.py   # Main application with full HUD & cloak magic
├── calibrate_color.py      # Standalone color calibrator utility
├── config.json             # Saved color presets and morphology settings
├── requirements.txt        # Python package dependencies
├── run.bat                 # 1-click launcher for the main app
├── calibrate.bat           # 1-click launcher for the calibration tool
└── snapshots/              # Directory where captured photos are saved
```

---

## 🚀 How to Run

### Method 1: Using 1-Click Launchers (Windows)
Double-click:
- **`run.bat`**: Runs the live webcam Invisibility Cloak.
- **`demo.bat`**: Runs the Hogwarts Demo Video Mode (instant verification without webcam).
- **`calibrate.bat`**: Runs the standalone color calibration tool.

### Method 2: From PowerShell / Command Prompt
```powershell
cd d:\ml-workshop\games_dev\harry_potter_cloak

# Live Webcam mode:
.\.venv\Scripts\python.exe invisibility_cloak.py

# Demo Video mode (offline Hogwarts test):
.\.venv\Scripts\python.exe invisibility_cloak.py --demo
```

Optional CLI flags:
```powershell
# Use an external webcam (e.g. index 1)
.\.venv\Scripts\python.exe invisibility_cloak.py --camera 1

# Process a pre-recorded video file
.\.venv\Scripts\python.exe invisibility_cloak.py --video my_video.mp4
```

---

## 🎮 Keyboard Controls & Cheatsheet

| Key | Action | Description |
| :---: | :--- | :--- |
| **`TAB`** | **Switch Camera** | Toggles between Camera 0 and Camera 1 on the fly |
| **`D`** | **Demo Mode** | Toggles between your live webcam and Hogwarts demo video |
| **`Left Click`** | **Eyedropper Tool** | Click anywhere on your cloth to automatically sample its HSV color! |
| **`1`** | **Red Preset** | Switches to Red cloak preset (handles wrapped hue ranges 0-10 & 170-180) |
| **`2`** | **Blue Preset** | Switches to Blue cloak preset (HSV 90-130) |
| **`3`** | **Green Preset** | Switches to Green cloak preset (HSV 35-85) |
| **`4`** | **Custom Preset** | Switches to your custom saved/eyedropper preset |
| **`B`** | **Recapture BG** | Starts a countdown to recapture a new background plate |
| **`C`** | **HSV Calibrator** | Opens/closes live trackbars for fine-tuning |
| **`M`** | **Toggle Mask PiP**| Shows/hides the top-right mask thumbnail monitor |
| **`S`** | **Save Photo** | Saves a high-res snapshot into `snapshots/` folder |
| **`H`** | **Toggle HUD** | Hides/shows the overlay text for clean recording |
| **`P`** | **Pause/Freeze** | Freezes current frame to inspect mask quality |
| **`Q` / `Esc`** | **Quit** | Exits cleanly and saves settings |

---

## 💡 Pro Tips for Best Results

1. **Keep the Camera Fixed**: Mount your camera or laptop stably on a desk. Do not move or tilt the camera after the background is captured.
2. **Stable Lighting**: Avoid fluctuating light (e.g. flickering monitors or waving shadows).
3. **High Contrast Cloth**: Use a single solid color cloth (red, blue, or green blanket/sheet). Avoid wearing clothing of the same color as the cloak, or that part of your body will disappear too!
4. **Step Away during Countdown**: When pressing `B`, make sure the entire camera view is clear of people so it captures the pure background scene.
