# Guardian Angel — What Was Built

[2026-03-15 05:59:15] TEACH: Created devlog CLI tool.
[2026-03-15 06:01:05] TEACH: Created backend entry point stub.
[2026-03-15 06:01:06] TEACH: Created empty config stub.
[2026-03-15 06:01:06] TEACH: Created detection module init.
[2026-03-15 06:01:06] TEACH: Created audio module init.
[2026-03-15 06:01:06] TEACH: Created overlay module init.
[2026-03-15 06:01:06] TEACH: Created watchdog module init.
[2026-03-15 06:01:06] TEACH: Created stats module init.
[2026-03-15 06:01:06] TEACH: Created telemetry module init.
[2026-03-15 06:01:19] TEACH: Created frontend placeholder.
[2026-03-15 06:01:19] TEACH: Created tests placeholder.
[2026-03-15 06:01:19] TEACH: Created stats data placeholder.
[2026-03-15 06:01:19] TEACH: Created telemetry data placeholder.
[2026-03-15 06:01:19] TEACH: Created dev log with header.
[2026-03-15 06:01:20] TEACH: Created teach log with header.
[2026-03-15 06:01:20] TEACH: Created production config with all default settings.
[2026-03-15 06:01:20] TEACH: Created developer config overrides with debug tools.
[2026-03-15 06:01:36] TEACH: Created Quran ayah quote pool with 5 entries.
[2026-03-15 06:01:36] TEACH: Created motivational quote pool with 6 entries.
[2026-03-15 06:01:36] TEACH: Created Python dependency list for all phases.
[2026-03-15 06:01:36] TEACH: Created full system architecture specification.
[2026-03-15 06:01:36] TEACH: Created build phases roadmap from Phase 0 through Phase 10.
[2026-03-15 06:01:36] TEACH: Created project README with overview and specs.
[2026-03-15 06:01:36] TEACH: Created gitignore covering caches builds and dev config.
[2026-03-15 06:15:51] TEACH: Created ScreenCapture class with multi-monitor support.
[2026-03-15 06:15:51] TEACH: Created MotionDetector class with SSIM motion skip and numpy fallback.
[2026-03-15 06:15:51] TEACH: Created NSFWDetector class with lazy NudeNet loading and tier classification.
[2026-03-15 06:15:51] TEACH: Created FPSManager class with rolling FPS measurement and auto-drop.
[2026-03-15 06:15:51] TEACH: Created DetectionPipeline orchestration class with full capture-detect loop.
[2026-03-15 06:15:51] TEACH: Created test script for pipeline smoke testing.
[2026-03-15 06:15:51] TEACH: Updated module init with clean exports for all detection classes.
[2026-03-15 06:15:51] TEACH: Added scikit-image for SSIM motion detection.
[2026-03-15 16:44:06] TEACH: Created OverlayRenderer class with Win32 transparent overlay, all censor styles, DPI scaling, multi-box rendering.
[2026-03-15 16:44:06] TEACH: Created overlay test script with 3 fake bounding boxes and 5-second hold.
[2026-03-15 16:44:06] TEACH: Updated overlay module init with clean OverlayRenderer export.
[2026-03-15 16:49:38] TEACH: Fixed SetTimer bug - replaced win32gui.SetTimer with ctypes.windll.user32.SetTimer.
[2026-03-15 16:49:38] TEACH: Added Optional Detection Modules section with face_blur and object_blur specs.
[2026-03-15 16:49:38] TEACH: Added commented-out ultralytics and mediapipe optional dependencies.
[2026-03-15 16:51:43] TEACH: Fixed invisible overlay - removed SetLayeredWindowAttributes that conflicted with UpdateLayeredWindow, replaced timer with direct paint loop using PumpWaitingMessages.
[2026-03-15 17:03:48] TEACH: Integrated SVG angel art rendering with cairosvg - loads 4-tier design sheet, caches per-tier images, composites onto gold background with silent fallback.
[2026-03-15 17:03:48] TEACH: Added cairosvg dependency for SVG-to-PNG rendering.
[2026-03-15 17:03:48] TEACH: Confirmed existing SVG design sheet with 4 tier variants at known crop regions.
[2026-03-15 18:01:57] TEACH: Replaced SVG rasterisation (cairosvg/svglib) with pre-rendered PNG assets. Extracted 4 tier PNGs from SVG via Selenium headless Chrome. _GuardianAngelSVG now loads PNGs directly via Pillow - zero external deps.
[2026-03-15 18:03:20] TEACH: Generated 4 pre-rendered tier PNG assets (full/medium/small/micro) from SVG design sheet using Selenium headless Chrome with per-tier viewBox cropping at 4x resolution.
[2026-03-15 18:03:24] TEACH: Created Selenium-based script to extract per-tier PNG assets from SVG. Runs headless Chrome with modified viewBox per tier, exports canvas to base64 PNG.
[2026-03-15 18:55:56] TEACH: Deleted browser preview files (render_svg_tiers.html, extract_tiers.html, generate_tier_pngs.py). Deleted temp SVGs and test PNGs from assets/.
[2026-03-15 18:55:59] TEACH: Rewrote to use 4 per-tier SVGs (full/medium/small/micro) as source. Selenium headless Chrome renders at 2x native res (520x600, 800x200, 140x140, 120x120). Build-time only.
[2026-03-15 18:56:05] TEACH: Updated _GuardianAngelSVG class - lowercase tier keys, assets/ prefix paths, warning on load failure, .lower() tier lookup. Removed all cairosvg/svglib references.
[2026-03-15 18:56:08] TEACH: Ran overlay test - 3 boxes (FULL/MEDIUM/SMALL) rendered with angel art for 5s, closed cleanly, zero errors.
[2026-03-15 19:20:15] TEACH: Created AudioCapture class - WASAPI loopback via pyaudiowpatch, auto device discovery, callback stream, thread-safe deque buffer.
[2026-03-15 19:20:15] TEACH: Created RingBuffer class - 1s pre-buffer, retroactive mute via zeroing, deque maxlen from sample_rate/chunk_size.
[2026-03-15 19:20:15] TEACH: Created VADFilter class - Silero VAD via torch.hub, lazy load, int16-to-float32, fail-open on error.
[2026-03-15 19:21:37] TEACH: Created AudioClassifier class - YAMNet via tensorflow_hub, lazy load, 10 explicit audio classes, graceful fallback.
[2026-03-15 19:21:37] TEACH: Created AudioTranscriber class - Whisper tiny.en, multilingual keywords (EN/AR/UR), auto language detect.
[2026-03-15 19:21:37] TEACH: Created AudioOutput class - pyaudiowpatch playback, silence injection, 1kHz bleep tone generator.
[2026-03-15 19:22:13] TEACH: Created AudioPipeline orchestrator - capture>ringbuf>VAD>classifier>transcriber>output, retroactive mute, threaded loop, dev_mode logging.
[2026-03-15 19:22:14] TEACH: Created audio capture test script - loopback device discovery, 3s capture, chunk counting.
[2026-03-15 19:22:14] TEACH: Updated with clean exports for all 7 audio classes.
[2026-03-15 19:23:01] TEACH: Removed cairosvg, svglib. Added tensorflow-hub commented. Confirmed pyaudiowpatch, openai-whisper, silero-vad present.
[2026-03-15 19:35:09] TEACH: Fixed 0-chunks bug - added explicit start_stream() call for callback mode. WASAPI loopback only generates data when system audio is playing (0 on silent desktop is expected).
[2026-03-15 19:35:09] TEACH: Updated test to play 440Hz tone during capture so loopback has data. Verified 154 chunks captured in 3s.
[2026-03-15 19:38:23] TEACH: Created SharedState class - Manager-backed boxes list, audio_trigger/is_running/fps_actual/detection_count Values, atomic box updates.
[2026-03-15 19:38:24] TEACH: Created run_detection_process entry point - DetectionPipeline loop, writes boxes/fps/count to SharedState, crash-resilient.
[2026-03-15 19:38:24] TEACH: Created run_overlay_process entry point - reads boxes from SharedState, updates OverlayRenderer at 60Hz, crash-resilient.
[2026-03-15 19:41:43] TEACH: Created run_audio_process entry point - AudioPipeline with callback to set SharedState audio_trigger.
[2026-03-15 19:41:43] TEACH: Created ProcessSupervisor - spawns 3 subprocesses, health monitor thread restarts crashed processes every 5s, graceful stop with force-terminate fallback.
[2026-03-15 19:43:46] TEACH: Created IPC integration test - starts supervisor, runs 8s printing status, stops. Requires if __name__ guard for Windows multiprocessing.
[2026-03-15 19:43:46] TEACH: Created with clean exports for SharedState, ProcessSupervisor.
[2026-03-15 19:44:53] TEACH: Auto-dropped FPS from 60 to 55.
[2026-03-15 19:49:18] TEACH: Full rewrite - overview, mission, architecture diagram, phase status table, requirements, install, Islamic note, license, contributing.
[2026-03-15 19:49:18] TEACH: Created bug_report.md, feature_request.md issue templates and repo_meta.txt with description/topics.
[2026-03-15 20:00:04] TEACH: Added trust_repo=True to torch.hub.load to suppress UserWarning on first run.
[2026-03-15 20:07:06] TEACH: Created Pydantic models - StatusResponse, ConfigResponse, ConfigUpdateRequest, OverlayStatusResponse, AudioStatusResponse, StatsResponse, TelemetryPayload, TriggerRequest.
[2026-03-15 20:07:06] TEACH: Created ConfigManager - thread-safe config read/write, deep merge, dot-key access, dev config overlay, atomic write via temp+rename.
[2026-03-15 20:07:06] TEACH: Created StatsManager - session+cumulative JSON files, trigger recording, streak tracking, combined view for API.
[2026-03-15 20:07:53] TEACH: Created all API route handlers - GET /status, GET/PATCH /config, GET /overlay, GET /audio, GET /stats, POST /stats/trigger, GET /telemetry, POST /quit. Error wrapping on all endpoints.
[2026-03-15 20:07:53] TEACH: Created FastAPI app factory - CORS for localhost:8422, app.state dependency wiring, startup/shutdown lifecycle hooks.
[2026-03-15 20:08:15] TEACH: Updated backend entry point - instantiates ConfigManager, StatsManager, ProcessSupervisor, creates FastAPI app, runs uvicorn on localhost:8421.
[2026-03-15 20:08:16] TEACH: Created API integration test - starts supervisor+FastAPI in background thread, hits 5 GET endpoints, prints results.
[2026-03-15 20:08:16] TEACH: Created with clean exports for create_app, ConfigManager, StatsManager.
[2026-03-15 20:13:04] TEACH: Updated phase table - Phase 5 done, Phase 6 in progress.
[2026-03-15 20:39:01] TEACH: Scaffolded Vite v8 + React, installed Tailwind v4 via @tailwindcss/vite, configured port 8422 + API proxy to 8421.
[2026-03-15 20:39:01] TEACH: Created API client with 7 async functions - getStatus, getConfig, updateConfig, getStats, getOverlay, getAudio, postQuit.
[2026-03-15 20:39:01] TEACH: Created top status bar - 3 glowing pills (Detection/Overlay/Audio) with live/dead states, FPS counter.
[2026-03-15 20:39:01] TEACH: Created stats card - hero days_protected number, streak with flame, total/session blocked, uptime HH:MM:SS.
[2026-03-15 20:39:01] TEACH: Created settings panel - censor style dropdown, sensitivity slider, FPS input, audio action, auto FPS/dev mode toggles.
[2026-03-15 20:39:19] TEACH: Created decorative header - angel art from /assets/, Arabic calligraphy, Quranic reference, gold glow.
[2026-03-15 20:39:19] TEACH: Created main dashboard - AngelBadge header, StatusBar (2s poll), two-column StatsPanel + ConfigPanel grid, themed footer.
[2026-03-15 20:39:19] TEACH: Updated title to Guardian Angel, shield emoji favicon.
[2026-03-15 20:39:19] TEACH: Added StaticFiles mount for assets/ directory at /assets path for angel art PNGs.
[2026-03-15 20:39:19] TEACH: Verified npm run dev starts on port 8422 successfully - VITE v8.0.0 ready in 596ms.
[2026-03-15 20:40:05] TEACH: Auto-dropped FPS from 60 to 55.
[2026-03-15 20:40:08] TEACH: Auto-dropped FPS from 55 to 50.
[2026-03-15 20:40:11] TEACH: Auto-dropped FPS from 50 to 45.
[2026-03-15 20:40:14] TEACH: Auto-dropped FPS from 45 to 40.
[2026-03-15 20:40:18] TEACH: Auto-dropped FPS from 40 to 35.
[2026-03-15 20:40:21] TEACH: Auto-dropped FPS from 35 to 30.
[2026-03-15 20:40:24] TEACH: Auto-dropped FPS from 30 to 25.
[2026-03-15 20:40:28] TEACH: Auto-dropped FPS from 25 to 20.
[2026-03-15 20:40:31] TEACH: Auto-dropped FPS from 20 to 15.
[2026-03-15 20:40:34] TEACH: Auto-dropped FPS from 15 to 10.
[2026-03-15 20:40:43] TEACH: Auto-dropped FPS from 10 to 5.
[2026-03-15 20:46:37] TEACH: Removed Manager Lock - was crashing on Windows spawn. Manager list del+extend is already process-safe without separate lock.
[2026-03-15 20:46:38] TEACH: Detection loop already had try/except with 1s retry - confirmed error handling is in place.
[2026-03-15 21:27:48] TEACH: Auto-dropped FPS from 60 to 55.
[2026-03-15 21:27:51] TEACH: Auto-dropped FPS from 55 to 50.
[2026-03-15 21:27:54] TEACH: Auto-dropped FPS from 50 to 45.
[2026-03-15 21:27:58] TEACH: Auto-dropped FPS from 45 to 40.
[2026-03-15 21:28:01] TEACH: Auto-dropped FPS from 40 to 35.
[2026-03-15 21:28:05] TEACH: Auto-dropped FPS from 35 to 30.
[2026-03-15 21:28:08] TEACH: Auto-dropped FPS from 30 to 25.
[2026-03-15 21:28:11] TEACH: Auto-dropped FPS from 25 to 20.
[2026-03-15 21:28:15] TEACH: Auto-dropped FPS from 20 to 15.
[2026-03-15 21:28:18] TEACH: Auto-dropped FPS from 15 to 10.
[2026-03-15 21:33:16] TEACH: Replaced FPS auto-drop devlog call with print() - runtime events should not spam DEVLOG.md.
[2026-03-15 21:33:16] TEACH: Created start script - launches backend+frontend in separate cmd windows with 4s delay.
[2026-03-15 21:33:16] TEACH: Created stop script - kills backend+frontend windows by title.
[2026-03-15 21:33:16] TEACH: Updated phase table - Phase 6 done, Phase 7 in progress.
[2026-03-15 22:12:56] TEACH: Added advanced detection config.
[2026-03-15 22:12:59] TEACH: Added detection config fields to Config models.
[2026-03-15 22:13:11] TEACH: Created watchdog persistence logic.
[2026-03-15 22:13:20] TEACH: Added /persistence and /watchdog endpoints.
[2026-03-15 22:13:24] TEACH: Created lock and disable UI.
[2026-03-15 22:13:28] TEACH: Integrated PersistencePanel.
[2026-03-15 22:35:20] TEACH: Fixed frontend build error and backend NameError.