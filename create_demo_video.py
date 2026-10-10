"""
Generates an interactive demonstration video for the Invisibility Cloak project.
Creates a room background plate and an animated person moving with a red cloak.
"""
import cv2
import numpy as np
import os

def generate_demo_video(filename="demo_cloak.mp4", width=1280, height=720, fps=30, duration_sec=8):
    output_path = os.path.join(os.path.dirname(__file__), filename)
    print(f"[*] Generating demo video: {output_path}...")
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # 1. Generate room background
    bg = np.zeros((height, width, 3), dtype=np.uint8)
    # Wall gradient
    for y in range(height):
        factor = y / height
        bg[y, :] = [int(180 - 40 * factor), int(140 - 30 * factor), int(100 - 20 * factor)]
    
    # Add room elements: Bookshelf, window, picture frame, floor
    # Floor
    floor_y = int(height * 0.72)
    bg[floor_y:, :] = [60, 80, 110]
    cv2.line(bg, (0, floor_y), (width, floor_y), (40, 50, 70), 3)
    
    # Window with outdoor sky & sun
    cv2.rectangle(bg, (100, 80), (380, 420), (240, 220, 160), -1)
    cv2.rectangle(bg, (115, 95), (365, 405), (255, 240, 180), -1)
    cv2.circle(bg, (300, 180), 45, (120, 240, 255), -1) # Sun
    cv2.line(bg, (240, 95), (240, 405), (100, 90, 80), 4)
    cv2.line(bg, (115, 250), (365, 250), (100, 90, 80), 4)
    
    # Bookshelf
    cv2.rectangle(bg, (920, 120), (1200, 680), (40, 60, 90), -1)
    for shelf_y in [250, 390, 530]:
        cv2.line(bg, (920, shelf_y), (1200, shelf_y), (30, 45, 70), 8)
        # Books
        for bx in range(940, 1180, 28):
            color = [int(np.random.randint(50, 220)), int(np.random.randint(50, 200)), int(np.random.randint(50, 220))]
            bh = np.random.randint(70, 115)
            cv2.rectangle(bg, (bx, shelf_y - bh), (bx + 22, shelf_y - 4), color, -1)

    # Picture frame on wall
    cv2.rectangle(bg, (520, 100), (760, 260), (30, 40, 60), 8)
    cv2.rectangle(bg, (528, 108), (752, 252), (180, 200, 220), -1)
    cv2.putText(bg, "HOGWARTS", (560, 190), cv2.FONT_HERSHEY_DUPLEX, 0.9, (80, 50, 40), 2)

    total_frames = int(fps * duration_sec)
    
    # Save reference background as an image too
    bg_img_path = os.path.join(os.path.dirname(__file__), "demo_background.jpg")
    cv2.imwrite(bg_img_path, bg)

    # First 30 frames: Empty room background plate (so countdown captures it cleanly)
    for _ in range(35):
        out.write(bg.copy())

    # Remaining frames: Person walks in holding a bright red cloak
    walk_frames = total_frames - 35
    for i in range(walk_frames):
        frame = bg.copy()
        t = i / walk_frames
        
        # Person walking from left (x=450) to right (x=800) and back
        center_x = int(450 + 350 * np.sin(t * np.pi))
        center_y = int(height * 0.52)
        
        # Draw Person
        # Head (skin color BGR: [150, 190, 235])
        head_y = center_y - 170
        cv2.circle(frame, (center_x, head_y), 45, (150, 190, 235), -1)
        # Hair
        cv2.ellipse(frame, (center_x, head_y - 20), (45, 30), 0, 180, 360, (30, 40, 50), -1)
        # Glasses (Harry Potter style round glasses!)
        cv2.circle(frame, (center_x - 16, head_y + 5), 12, (20, 20, 20), 2)
        cv2.circle(frame, (center_x + 16, head_y + 5), 12, (20, 20, 20), 2)
        cv2.line(frame, (center_x - 4, head_y + 5), (center_x + 4, head_y + 5), (20, 20, 20), 2)
        
        # Body / Legs (dark pants)
        cv2.rectangle(frame, (center_x - 35, center_y + 60), (center_x - 5, center_y + 220), (50, 50, 50), -1)
        cv2.rectangle(frame, (center_x + 5, center_y + 60), (center_x + 35, center_y + 220), (50, 50, 50), -1)
        # Shoes
        cv2.rectangle(frame, (center_x - 42, center_y + 215), (center_x - 5, center_y + 230), (20, 20, 20), -1)
        cv2.rectangle(frame, (center_x + 5, center_y + 215), (center_x + 42, center_y + 230), (20, 20, 20), -1)
        
        # Cloak waving / draped over torso
        # Bright Red fabric (BGR: ~ [20, 20, 220])
        cloak_pts = np.array([
            [center_x - 85, center_y - 110],
            [center_x + 85, center_y - 110],
            [center_x + 115 + int(15 * np.sin(i * 0.2)), center_y + 110],
            [center_x - 115 - int(15 * np.cos(i * 0.2)), center_y + 110]
        ], np.int32)
        cv2.fillPoly(frame, [cloak_pts], (25, 25, 225))
        
        # Cloak folds/shading for realism
        cv2.line(frame, (center_x - 20, center_y - 100), (center_x - 30, center_y + 100), (15, 15, 180), 4)
        cv2.line(frame, (center_x + 20, center_y - 100), (center_x + 30, center_y + 100), (15, 15, 180), 4)

        # Hands holding the cloak (visible at corners)
        cv2.circle(frame, (center_x - 90, center_y - 95), 14, (150, 190, 235), -1)
        cv2.circle(frame, (center_x + 90, center_y - 95), 14, (150, 190, 235), -1)
        
        out.write(frame)
        
    out.release()
    print(f"[+] Successfully generated demo video at: {output_path}")

if __name__ == "__main__":
    generate_demo_video()
