#!/usr/bin/env python3
"""Guardian Angel — Dev Log CLI Tool

Appends structured log entries to docs/DEVLOG.md and
plain-English explanations to docs/TEACH.md.

Usage:
    python scripts/devlog.py "PHASE:0 | FILE:example.py | ACTION:created file | STATUS:done"
"""

import sys
import os
import re
from datetime import datetime


def get_project_root():
    """Resolve the project root regardless of working directory.

    The project root is the parent of the 'scripts/' directory
    that contains this file.
    """
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ensure_file(path, header):
    """Create the file with the given header if it does not exist."""
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)
    if not os.path.isfile(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(header + "\n")


def parse_action(log_string):
    """Extract the ACTION field from the structured log string."""
    match = re.search(r"ACTION\s*:\s*(.+?)(?:\s*\||$)", log_string)
    if match:
        return match.group(1).strip()
    return None


def action_to_teach(action_text):
    """Convert an ACTION field into a beginner-friendly sentence."""
    # Capitalise first letter and ensure it ends with a full stop.
    sentence = action_text[0].upper() + action_text[1:] if action_text else action_text
    if sentence and not sentence.endswith("."):
        sentence += "."
    return sentence


def main():
    if len(sys.argv) != 2:
        print("Error: devlog.py expects exactly one argument — the log string.")
        print('Usage: python scripts/devlog.py "PHASE:0 | FILE:x | ACTION:y | STATUS:z"')
        sys.exit(1)

    log_string = sys.argv[1]
    project_root = get_project_root()
    devlog_path = os.path.join(project_root, "docs", "DEVLOG.md")
    teach_path = os.path.join(project_root, "docs", "TEACH.md")

    try:
        # Ensure target files exist with headers
        ensure_file(devlog_path, "# Guardian Angel Dev Log")
        ensure_file(teach_path, "# Guardian Angel — What Was Built")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Append to DEVLOG.md
        with open(devlog_path, "a", encoding="utf-8") as f:
            f.write(f"\n[{timestamp}] {log_string}")

        # Parse ACTION and append to TEACH.md
        action = parse_action(log_string)
        if action:
            teach_sentence = action_to_teach(action)
            with open(teach_path, "a", encoding="utf-8") as f:
                f.write(f"\n[{timestamp}] TEACH: {teach_sentence}")

        print("Logged.")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
