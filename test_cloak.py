"""
Unit test for Invisibility Cloak image processing algorithms
"""
import numpy as np
import cv2
import json
import os
from invisibility_cloak import InvisibilityCloak

def test_pipeline():
    print("[*] Testing Invisibility Cloak image processing pipeline...")
    app = InvisibilityCloak()
    
    # Create synthetic 720p background (e.g. brick wall pattern / room)
    bg = np.zeros((720, 1280, 3), dtype=np.uint8)
    bg[:] = (180, 120, 70) # warm room wall color
    # Add some pattern
    cv2.rectangle(bg, (200, 200), (500, 500), (100, 50, 20), -1)
    app.background = bg
    
    # Create synthetic live frame: person standing with a bright red cloak
    frame = bg.copy()
    # Person body (gray clothes)
    cv2.rectangle(frame, (400, 150), (880, 680), (120, 120, 120), -1)
    # Red cloak draped over body (BGR: [0, 0, 230])
    cv2.circle(frame, (640, 400), 160, (20, 20, 230), -1)
    
    # 1. Test Red Mask
    app.set_preset("red")
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = app.get_cloak_mask(hsv)
    
    assert mask is not None, "Mask should not be None"
    assert mask.shape == (720, 1280), "Mask shape mismatch"
    red_pixels = np.sum(mask > 0)
    print(f"[+] Detected {red_pixels} cloak pixels in red test circle.")
    assert red_pixels > 10000, "Should detect the red cloak circle"
    
    # 2. Test Feathered Alpha Blending
    blended = app.apply_cloak_effect(frame, mask)
    assert blended is not None, "Blended result should not be None"
    assert blended.shape == (720, 1280, 3), "Blended shape mismatch"
    
    # Check that in center of cloak circle, pixel matches background, not red!
    center_color = blended[400, 640]
    expected_bg = bg[400, 640]
    diff = np.abs(center_color.astype(int) - expected_bg.astype(int))
    print(f"[+] Center difference between blended cloak and background: {np.max(diff)}")
    assert np.max(diff) < 5, f"Cloak center should match background plate, diff: {diff}"
    
    # 3. Test Blue Mask
    app.set_preset("blue")
    frame_blue = bg.copy()
    cv2.circle(frame_blue, (640, 400), 160, (230, 80, 20), -1) # Blue in BGR
    hsv_blue = cv2.cvtColor(frame_blue, cv2.COLOR_BGR2HSV)
    mask_blue = app.get_cloak_mask(hsv_blue)
    blue_pixels = np.sum(mask_blue > 0)
    print(f"[+] Detected {blue_pixels} cloak pixels in blue test circle.")
    assert blue_pixels > 10000, "Should detect the blue cloak circle"

    print("\n[SUCCESS] All Invisibility Cloak image processing tests passed with flying colors!")

if __name__ == "__main__":
    test_pipeline()
