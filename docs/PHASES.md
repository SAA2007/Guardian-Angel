# Guardian Angel — Build Phases

## Phase 0 — Project scaffold (CURRENT)
Folder structure, devlog, config schema, quote data,
requirements, spec, README, gitignore.

## Phase 1 — Screen capture + detection
mss multi-monitor capture, NudeNet ONNX inference,
bounding box output, SSIM motion skip, FPS measurement.

## Phase 2 — Overlay renderer
pywin32 transparent always-on-top click-through window,
multi-box rendering, guardian angel SVG scaling tiers,
all censor style modes, FPS overlay (dev mode).

## Phase 3 — Audio pipeline
pyaudiowpatch WASAPI loopback, Silero VAD, YAMNet classifier,
Whisper tiny.en transcription, ring buffer, retroactive mute.

## Phase 4 — Multiprocessing IPC
Python multiprocessing, shared memory for bounding boxes,
process A spawning detection/audio/overlay subprocesses,
graceful shutdown, crash recovery.

## Phase 5 — FastAPI backend
All endpoints: /status /config /overlay /audio /stats
/telemetry /quit, config read/write, stats read/write,
dev_mode tools endpoint.

## Phase 6 — React frontend
Vite setup, settings UI, stats dashboard, censor style picker,
quote pool editor, persistence controls, dev tools panel.

## Phase 7 — Persistence + watchdog
Windows service install, randomised naming, encrypted backup,
lock timer, indefinite mode 4-screen disable sequence,
accountability contact notification.

## Phase 8 — Stats + telemetry
Stats aggregation, streak calculation, hourly/daily heatmap,
telemetry batching and sending, anonymous UUID.

## Phase 9 — Packaging + installer
PyInstaller build, NSIS installer script, Start Menu entry,
tray autostart, Add/Remove Programs, README for end users.

## Phase 10 — Testing + hardening
Benchmark dataset testing (no live content), FPS adaptation
testing, watchdog tamper testing, multi-monitor testing,
minimum spec testing.
