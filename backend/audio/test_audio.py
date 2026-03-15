"""Guardian Angel -- Audio Capture Test Script

Simple test that verifies WASAPI loopback audio capture works.
Plays a short test tone through the system speakers while
capturing from the loopback — WASAPI loopback only generates
data when the system is outputting audio.

Usage:
    python backend/audio/test_audio.py
"""

import math
import os
import struct
import sys
import time

# Ensure project root is on the Python path
_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, _project_root)


def main():
    from backend.audio.capture import AudioCapture
    import pyaudiowpatch as pyaudio

    print("=" * 60)
    print("Guardian Angel -- Audio Capture Test")
    print("=" * 60)

    capture = AudioCapture()

    # Step 1: Find loopback device
    print("\nSearching for WASAPI loopback device...")
    try:
        device = capture.get_loopback_device()
        print("  Found: {}".format(device.get("name", "Unknown")))
        print("  Sample rate: {}".format(
            int(device.get("defaultSampleRate", 0))
        ))
        print("  Channels: {}".format(
            device.get("maxInputChannels", 0)
        ))
    except RuntimeError as e:
        print("  ERROR: {}".format(e))
        sys.exit(1)

    # Step 2: Start capture
    print("\nStarting capture...")
    capture.start()

    rate = capture.sample_rate
    channels = capture.channels

    # Step 3: Play a test tone so the loopback has data to capture
    # WASAPI loopback only generates audio when the system is
    # actually outputting sound — silence = 0 chunks.
    print("Playing 440Hz test tone (3 seconds)...")
    pa = pyaudio.PyAudio()
    out_stream = pa.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=rate,
        output=True,
        frames_per_buffer=1024,
    )

    # Generate 3 seconds of 440Hz sine at ~25% volume
    total_frames = rate * 3
    chunk_frames = 1024
    chunk_count = 0

    for offset in range(0, total_frames, chunk_frames):
        n = min(chunk_frames, total_frames - offset)
        samples = []
        for i in range(n):
            t = float(offset + i) / rate
            val = int(math.sin(2.0 * math.pi * 440.0 * t) * 4000)
            for _ in range(channels):
                samples.append(val)
        tone_bytes = struct.pack("<{}h".format(len(samples)),
                                *samples)
        out_stream.write(tone_bytes)

        # Read any captured chunks
        chunk = capture.read_chunk()
        while chunk is not None:
            chunk_count += 1
            chunk = capture.read_chunk()

    # Drain remaining buffered chunks
    time.sleep(0.2)
    chunk = capture.read_chunk()
    while chunk is not None:
        chunk_count += 1
        chunk = capture.read_chunk()

    # Step 4: Stop
    out_stream.stop_stream()
    out_stream.close()
    pa.terminate()
    capture.stop()

    print("\nAudio capture test complete.")
    print("Chunks received: {}".format(chunk_count))
    print("Sample rate: {}".format(rate))
    print("Channels: {}".format(channels))

    if chunk_count > 0:
        print("PASS: loopback capture is working.")
    else:
        print("FAIL: 0 chunks received. Check audio device.")


if __name__ == "__main__":
    main()
