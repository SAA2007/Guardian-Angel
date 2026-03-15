"""Guardian Angel — Detection Pipeline Test Script

Runnable smoke test that exercises the detection pipeline
five times on your normal desktop. Does NOT require any
NSFW content — it verifies the capture → motion → detect
flow works and reports zero detections on clean screens.

Usage:
    python backend/detection/test_pipeline.py
"""

import json
import os
import sys
import time

# Ensure the project root is on the Python path so imports work
_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, _project_root)


def main():
    # Temporarily force dev_mode for verbose output
    config_path = os.path.join(_project_root, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    original_dev_mode = config.get("dev_mode", False)

    # Set dev_mode true for the test run
    config["dev_mode"] = True
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    try:
        from backend.detection.pipeline import DetectionPipeline

        pipeline = DetectionPipeline()
        monitors = pipeline.capture.get_monitors()

        print("=" * 60)
        print("Guardian Angel — Detection Pipeline Test")
        print("=" * 60)
        print(f"Monitors detected: {len(monitors)}")
        for mon in monitors:
            print(
                f"  Monitor {mon['id']}: "
                f"{mon['width']}x{mon['height']} "
                f"at ({mon['x']}, {mon['y']})"
            )
        print("-" * 60)

        for i in range(1, 6):
            results = pipeline.run_once()
            actual_fps = pipeline.fps_manager.get_actual_fps()
            target_fps = pipeline.fps_manager.get_target_fps()
            print(
                f"Run {i}/5 | "
                f"Detections: {len(results)} | "
                f"FPS actual: {actual_fps:.1f} | "
                f"FPS target: {target_fps}"
            )
            if i < 5:
                time.sleep(0.5)

        print("-" * 60)
        print("Detection pipeline test complete.")

    finally:
        # Restore original dev_mode
        config["dev_mode"] = original_dev_mode
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)


if __name__ == "__main__":
    main()
