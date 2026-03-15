# Guardian Angel — Build Phases

## Phase 0 — Project scaffold ✅ COMPLETE
Folder structure, devlog, config schema, quote data,
requirements, spec, README, gitignore.

## Phase 1 — Screen capture + detection ✅ COMPLETE
mss multi-monitor capture, NudeNet ONNX inference,
bounding box output, SSIM motion skip, FPS measurement.

### Fixes & improvements applied
- Resolution scaling: detection runs at configurable
  fraction of screen resolution (default 50%) and
  coordinates are scaled back up to full resolution
- Frame skip: NudeNet runs every N frames (default 2),
  last result held between skipped frames
- SSIM downsampled to 320px wide before comparison
  for 10x speed improvement
- NudeNet v3 box format fixed: [x,y,w,h] not [x1,y1,x2,y2]
- BGR to RGB conversion added before NudeNet inference
- Bounding box padding: boxes expanded by configurable
  factor (default 40%) to cover surrounding context
- Class filter: BELLY_EXPOSED, FACE_FEMALE, FACE_MALE,
  ARMPITS_EXPOSED excluded from censoring
- ONNX thread count configurable to limit CPU usage
- FPS auto-drop no longer spams DEVLOG.md

## Phase 2 — Overlay renderer ✅ COMPLETE
pywin32 transparent always-on-top click-through window,
multi-box rendering, guardian angel SVG scaling tiers,
all censor style modes, FPS overlay (dev mode).

### Fixes & improvements applied
- SetTimer bug fixed: replaced win32gui.SetTimer with
  ctypes.windll.user32.SetTimer
- DPI scaling: per-monitor DPI via GetDpiForMonitor
  for correct coordinates on mixed-DPI setups
- Angel art: 4 pre-rendered PNG tiers (full/medium/
  small/micro) loaded via Pillow, extracted from SVG
  via Selenium headless Chrome at 2x resolution
- Tier-based rendering: MICRO gets solid gold fill,
  SMALL gets nur orb with gold glow, MEDIUM/FULL get
  full angel art with aspect-ratio letterboxing
- 800ms box hold: overlay keeps last non-empty boxes
  for 800ms before clearing, prevents flicker

## Phase 3 — Audio pipeline ✅ COMPLETE
pyaudiowpatch WASAPI loopback, Silero VAD, YAMNet classifier,
Whisper tiny.en transcription, ring buffer, retroactive mute.

### Fixes & improvements applied
- WASAPI loopback requires explicit start_stream() call
- 0-chunk bug fixed: stream now captures correctly
- Silero VAD trust_repo=True suppresses UserWarning
- Audio capture verified: 151 chunks in 3 seconds

## Phase 4 — Multiprocessing IPC ✅ COMPLETE
Python multiprocessing, shared memory for bounding boxes,
process A spawning detection/audio/overlay subprocesses,
graceful shutdown, crash recovery.

### Fixes & improvements applied
- Manager Lock removed: was crashing on Windows spawn,
  del+extend on Manager list is already process-safe
- KeyboardInterrupt handling: all 3 subprocesses now
  catch Ctrl+C cleanly without ugly tracebacks
- PID file: backend writes data/guardian_angel.pid on
  startup for reliable process termination

## Phase 5 — FastAPI backend ✅ COMPLETE
All endpoints: /status /config /overlay /audio /stats
/telemetry /quit, config read/write, stats read/write,
dev_mode tools endpoint.

### Fixes & improvements applied
- Missing fastapi import in routes.py fixed
- Stats manager records session start/end on lifecycle

## Phase 6 — React frontend ✅ COMPLETE
Vite setup, settings UI, stats dashboard, censor style picker,
quote pool editor, persistence controls, dev tools panel.

### Fixes & improvements applied
- Stale venv scaffold directory removed from git
- start.bat: dev mode runs backend in same terminal
  for visible logs (run with "dev" argument)
- stop.bat: kills by port+PID via psutil, reliable
- FPS auto-drop DEVLOG spam fixed: now uses print()
- Encoding: em dashes replaced with hyphens in bat files

## Phase 7 — Persistence + watchdog ✅ COMPLETE
Windows service install, randomised naming, encrypted backup,
lock timer, indefinite mode 4-screen disable sequence,
accountability contact notification.

### Fixes & improvements applied
- PersistencePanel renamed to "Your Guardian"
- Disable button text: "I need a break..."
- Full 4-screen disable flow implemented and verified
- Live activity feed added to stats panel
- Shutdown button added to dashboard footer
- Detection raw debug output added for dev_mode
- Sensitivity lowered to 0.25 for NudeNet v3 score range
- Box padding slider added to ConfigPanel

## Phase 8 — Stats + telemetry ⏳ PENDING
Stats aggregation, streak calculation, hourly/daily heatmap,
telemetry batching and sending, anonymous UUID.

## Phase 9 — Packaging + installer ⏳ PENDING
PyInstaller build, NSIS installer script, Start Menu entry,
tray autostart, Add/Remove Programs, README for end users.

## Phase 10 — Testing + hardening ⏳ PENDING
Benchmark dataset testing (no live content), FPS adaptation
testing, watchdog tamper testing, multi-monitor testing,
minimum spec testing.

---

## Planned Improvements — v1.0 (before release)

### Detection — window enumeration
Use pywin32 EnumWindows to enumerate all visible
windows and their bounding rectangles. Skip scanning
windows that are known-safe by process name (IDE,
file explorer, Guardian Angel dashboard itself).
Prioritise scanning browser and video player windows.
Config key: window_scan_allowlist (array of process
names to skip).

### Detection — temporal smoothing
Average bounding box coordinates across the last 3
frames so boxes do not jump around between frames.
If a box was at (400,380) and then (410,385), render
at (405,382). Smooth movement, less jarring.

### Detection — scene-level hold
If 3 or more NSFW classes detected simultaneously
in one frame, treat as a confirmed explicit scene
and hold censoring for a minimum of 3 seconds
regardless of per-frame detection results.
Config key: scene_hold_seconds (default 3).

### Overlay — click intercept (Option B, default on)
When user clicks at screen coordinates that fall
within a current censor box, block the click via
Win32 mouse hook and briefly show "Guarded 🛡️"
on the censor box instead of passing the click
through to the content below.
Outside censor regions: clicks pass through normally.
Toggle in config: overlay_intercept_clicks (default true).
Option A (full click-through) available by setting false.

---

## Planned Improvements — v1.1 (post-release)

### Detection — grid sampling
Divide screen into 4x4 cells. Run a fast lightweight
scene classifier on each cell (~5ms each). Only run
NudeNet on cells that score above threshold.
Approximately 6x more efficient than current approach
on typical desktops where most screen area is safe.

### Detection — two-stage pipeline
Fast scene classifier (MobileNet/EfficientNet, ~5ms)
as Layer 0 before NudeNet. Only call NudeNet when
Layer 0 fires. Similar approach to HaramBlur which
uses nsfwjs for scene scoring before element blur.

### Detection — better model
Evaluate community fine-tuned ONNX models on
HuggingFace trained on video frames rather than
static images. Current NudeNet trained primarily
on static images, struggles with motion blur and
unusual angles.

### Optional modules
- face_blur: OpenCV Haar cascade or MediaPipe
  (already specced in SPEC.md)
- object_blur: YOLOv8 COCO class filtering
  (already specced in SPEC.md)

### Audio — keyword expansion
Larger multilingual keyword list covering Arabic
slang, Urdu common terms, and English euphemisms.
Community-maintained lists to be integrated.

### Audio — VPN detection
Monitor active network connections via psutil.
If a VPN process is detected while Guardian Angel
is running, automatically lower sensitivity
threshold and optionally notify user.
