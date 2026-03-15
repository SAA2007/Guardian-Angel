# Guardian Angel — System Architecture Specification
Version: 0.1.0 | Status: Phase 0

## Overview
Guardian Angel is a Windows-first Islamic-themed NSFW content
filter built for addiction recovery. It operates at the OS level,
intercepting screen content and audio output before they reach
the user, and replacing flagged content with an Islamic guardian
angel censor overlay.

## Process Architecture

### Process A — Main Application
- FastAPI server on localhost:8421
- Endpoints: /status /config /overlay /audio /stats /telemetry /quit
- Spawns and manages detection, audio, overlay as subprocesses
- Writes stats to data/stats/ on each trigger event
- Reads config.json on startup; config.dev.json overrides if dev_mode

### Process B — Guardian Watchdog (persistence mode only)
- Installed as Windows service with randomised service name
- Stored in randomised subfolder under AppData
- Checks Process A is RUNNING (not just installed) every 30 seconds
- Restarts Process A immediately if not running
- Checks own service files intact every 60 seconds
- Restores from encrypted backup if files missing or tampered
- Checks lock timer — blocks uninstall until timer expires
- Encrypted backup stored in second randomised AppData location
- Randomised scheduled task ensures watchdog survives reboot
- Clean disable sequence (indefinite mode only):
    Screen 1: 60-second mandatory wait, angel displayed, cannot skip
    Screen 2: user types reason in own words (free text, no dropdown)
    Screen 3: personal stats shown — days protected, trigger count
    Screen 4: notification sent to accountability contact if configured
    Only after all 4 screens does disable proceed

## Censor Overlay Rendering

### Bounding Box Handling
- NudeNet returns boxes of any aspect ratio
- Each box renders independently
- Multiple simultaneous boxes fully supported
- Angel scales responsively to fill its box

### Angel Size Tiers
- FULL    (>= 200x200px): nur orb + 3-layer wings + body + arabic text + quote
- MEDIUM  (>= 80x80px):   nur orb + wings + arabic text only
- SMALL   (>= 40x40px):   nur orb + wings only
- MICRO   (< 40px either): nur orb only

### Censor Styles
- guardian_angel (default): Islamic angel, Nur face, multi-layer wings,
  caring downward-curved posture, rotating quotes
- solid_black / solid_white / solid_custom: flat colour fill
- blur_light / blur_medium / blur_heavy: gaussian blur levels
- pixelate: pixelation effect

## Audio Pipeline
- WASAPI loopback capture via pyaudiowpatch (no VB-Cable required)
- Silero VAD filters non-speech chunks before transcription
- YAMNet classifies sound type — catches non-verbal explicit audio
- Whisper tiny.en transcribes speech chunks only
- 1-second pre-buffer ring before audio reaches output
- Retroactive mute/bleep on trigger detection
- Audio/video sync maintained — both delayed by same buffer

## FPS Adaptation
- Starts at monitor max FPS (read from system at launch)
- Auto-drops by 5 FPS increments when stable rate not maintained
- Minimum floor: fps_min in config (default: 2 FPS)
- User override available to disable auto-drop
- SSIM motion detection skips frames with no significant change

## Stats Tracking
- Per-session and cumulative stats stored in data/stats/
- Tracks: days protected, streak, triggers by hour/day, audio/video split
- Stats displayed on Screen 3 of persistence disable sequence
- Stats endpoint: GET /stats returns full JSON

## Telemetry
- Disabled by default for all users
- Enabled automatically in dev_mode
- Anonymous UUID generated on first run
- Sends: trigger counts, FPS metrics, error logs (no personal data)
- Endpoint: configurable in config.json

## Dev/Admin Tools (dev_mode only)
- FastAPI auto-docs at localhost:8421/docs
- Bounding box visualisation overlay
- FPS counter overlay
- Confidence score display
- Mock detection mode (fires fake triggers on interval)
- Benchmark mode (measures detection speed)
- Frame saving for flagged detections
- Audio chunk logging

## Optional Detection Modules

### face_blur
- OpenCV Haar cascade or MediaPipe face detection
- Blurs all detected faces in the captured frame
- Toggle in config: face_blur_enabled (default: false)
- Censor style inherits the global censor.style setting
- Runs alongside the primary NudeNet detection pipeline

### object_blur
- YOLOv8 (ultralytics) object detection
- Filters detected objects by a user-defined class list
  in config: object_blur_classes (array of COCO class names,
  e.g. ["wine glass", "bottle"])
- Toggle in config: object_blur_enabled (default: false)
- Planned for post-v1 release

## Frontend
- React + Vite served on localhost:8422
- Opens in system default browser
- Same codebase deployable as hosted website
- Settings, stats dashboard, censor style picker, persistence controls

## Packaging
- PyInstaller bundles Python backend to single exe
- NSIS installer creates Start Menu entry, Add/Remove Programs entry,
  optional desktop shortcut, system tray autostart
- Appears as normal Windows application to end user
