# Guardian Angel 🛡️

> AI-powered Islamic NSFW content filter for addiction recovery — real-time screen censor and audio mute with guardian angel overlay.

## What It Is

Guardian Angel is a Windows desktop application that detects explicit visual and audio content in real time and replaces it with an Islamic guardian angel censor overlay. It's built for people on the journey of addiction recovery — a tool that feels like protection, not punishment. Inspired by the concept of *Kiraman Katibin* (كِرَامًا كَاتِبِين), the noble recording angels, it's designed to be a caring, always-present companion for anyone who needs it.

## Why It Exists

Existing NSFW filters are either browser-only (useless against desktop apps), rely on URL blocklists (easily bypassed), or feel clinical and punishing. Tools like Porda-AI started the right idea but remain incomplete. Guardian Angel fills this gap — an OS-level filter with an Islamic spiritual frame, built as a personal mission for anyone struggling, Muslim or not.

## How It Works

```
Screen Capture (mss) → NudeNet ONNX Detection → Win32 Transparent Overlay
                                                    ↓
                                            Guardian Angel Art
                                         (4 tiers by box size)

Audio Loopback (WASAPI) → Silero VAD → Whisper Transcription → Mute / Bleep
                            ↓
                     YAMNet Classifier
                  (non-verbal detection)
```

- **Video**: Captures all monitors via `mss`, runs NudeNet ONNX inference, renders a transparent always-on-top Win32 overlay with angel art scaled to each detection box
- **Audio**: Captures system audio via WASAPI loopback (no VB-Cable needed), filters through Silero VAD, classifies with YAMNet, transcribes with Whisper, applies retroactive mute or bleep

## Current Status

| Phase | Name | Status |
|-------|------|--------|
| 0 | Project Scaffold | ✅ Done |
| 1 | Screen Capture + Detection | ✅ Done |
| 2 | Overlay Renderer | ✅ Done |
| 3 | Audio Pipeline | ✅ Done |
| 4 | Multiprocessing IPC | ✅ Done |
| 5 | FastAPI Backend | ✅ Done |
| 6 | React Frontend | ✅ Done |
| 7 | Performance Overlay + Persistence | ✅ Done |
| 8 | Testing & Packaging | 📝 Pending |
| 9 | Packaging + Installer | ⏳ Pending |

## Requirements

- **OS**: Windows 10 or 11 (64-bit)
- **Python**: 3.11
- **RAM**: 8 GB minimum
- **CPU**: Intel Core i5 8th gen or equivalent
- **GPU**: NVIDIA recommended for better FPS (any GTX 1060+), but not required
- **Disk**: ~500 MB free

## Installation

```bash
# Clone the repository
git clone https://github.com/SAA2007/Guardian-Angel.git
cd Guardian-Angel

# Install dependencies (use Python 3.11 explicitly)
C:\Users\DELL\AppData\Local\Programs\Python\Python311\python.exe -m pip install -r requirements.txt

# Run the IPC integration test
C:\Users\DELL\AppData\Local\Programs\Python\Python311\python.exe backend/ipc/test_ipc.py
```

## Islamic Note

> *"Indeed, over you are guardians, noble and recording; they know whatever you do."*
> — Quran 82:10-12

The name Guardian Angel draws from the concept of *Kiraman Katibin* — the noble angels appointed to every person, ever-present and ever-watchful. This tool is built in that spirit: not as a judgement, but as a practical aid for those who are struggling. Addiction recovery is a journey, and sometimes the hardest step is having the right support around you. Guardian Angel is meant to be part of that support — quiet, caring, and always there.

Built with love, for anyone who needs it. Muslim or not.

## License

MIT — free to use, modify, and distribute.
Built to help people. Keep it that way.

## Contributing

Open to pull requests. Issues welcome. If you're building tools for addiction recovery or Islamic tech, let's connect.
