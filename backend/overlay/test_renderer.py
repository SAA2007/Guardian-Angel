"""Guardian Angel -- Overlay Renderer Test Script

Opens the overlay, fires 3 fake bounding boxes at hardcoded
coordinates, holds for 5 seconds, then closes cleanly.

Usage:
    python backend/overlay/test_renderer.py
"""

import os
import sys
import time

# Ensure project root is on the Python path
_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, _project_root)


def main():
    from backend.overlay.renderer import OverlayRenderer

    print("=" * 60)
    print("Guardian Angel -- Overlay Renderer Test")
    print("=" * 60)

    renderer = OverlayRenderer()
    print("Starting overlay window...")
    renderer.start()
    time.sleep(0.5)  # give window time to initialise

    # 3 fake bounding boxes at hardcoded screen coordinates
    fake_boxes = [
        {
            "x": 200,
            "y": 200,
            "width": 250,
            "height": 250,
            "tier": "FULL",
            "confidence": 0.92,
            "label": "TEST_FULL",
            "monitor_id": 1,
        },
        {
            "x": 500,
            "y": 150,
            "width": 120,
            "height": 100,
            "tier": "MEDIUM",
            "confidence": 0.78,
            "label": "TEST_MEDIUM",
            "monitor_id": 1,
        },
        {
            "x": 700,
            "y": 400,
            "width": 50,
            "height": 50,
            "tier": "SMALL",
            "confidence": 0.65,
            "label": "TEST_SMALL",
            "monitor_id": 1,
        },
    ]

    print("Rendering 3 fake bounding boxes:")
    for b in fake_boxes:
        print(
            "  {} box at ({}, {}) -- {}x{}".format(
                b["tier"], b["x"], b["y"], b["width"], b["height"]
            )
        )

    renderer.update_boxes(fake_boxes)
    print("Holding for 5 seconds...")
    time.sleep(5)

    print("Closing overlay...")
    renderer.stop()
    print("Overlay renderer test complete.")


if __name__ == "__main__":
    main()
