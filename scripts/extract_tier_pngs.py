"""Extract Guardian Angel tier PNGs from per-tier SVG files.

Uses Selenium + headless Chrome to rasterise each SVG at 2x native
resolution and saves RGBA PNG files with transparency preserved.

Source SVGs (in assets/):
    guardian_angel_full.svg    (260x300)  -> guardian_angel_full.png    (520x600)
    guardian_angel_medium.svg  (400x100)  -> guardian_angel_medium.png  (800x200)
    guardian_angel_small.svg   (70x70)    -> guardian_angel_small.png   (140x140)
    guardian_angel_micro.svg   (60x60)    -> guardian_angel_micro.png   (120x120)

Usage:
    python scripts/extract_tier_pngs.py

Requirements:
    - selenium (pip install selenium)
    - Chrome or Chromium installed
    - Pillow (pip install Pillow)
"""

import base64
import json
import os
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")

# Source SVGs and their 2x output sizes
TIERS = {
    "full":   {"svg": "guardian_angel_full.svg",   "w": 520, "h": 600},
    "medium": {"svg": "guardian_angel_medium.svg", "w": 800, "h": 200},
    "small":  {"svg": "guardian_angel_small.svg",  "w": 140, "h": 140},
    "micro":  {"svg": "guardian_angel_micro.svg",  "w": 120, "h": 120},
}


def _build_extract_html():
    """Build an HTML page that renders each SVG on a canvas and
    outputs base64 PNG data as JSON in a <pre id='output'> tag."""
    canvas_blocks = []
    for tier, info in TIERS.items():
        canvas_blocks.append("""
        {{
            const resp = await fetch('/assets/{svg}');
            const svgText = await resp.text();
            const blob = new Blob([svgText], {{ type: 'image/svg+xml' }});
            const url = URL.createObjectURL(blob);
            const img = new Image();
            await new Promise(function(res, rej) {{
                img.onload = res;
                img.onerror = rej;
                img.src = url;
            }});
            const c = document.createElement('canvas');
            c.width = {w};
            c.height = {h};
            const ctx = c.getContext('2d');
            ctx.drawImage(img, 0, 0, {w}, {h});
            URL.revokeObjectURL(url);
            results['{tier}'] = c.toDataURL('image/png');
        }}""".format(tier=tier, svg=info["svg"], w=info["w"], h=info["h"]))

    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body>
<pre id="output"></pre>
<script>
(async function() {{
    var results = {{}};
    {blocks}
    document.getElementById('output').textContent = JSON.stringify(results);
}})();
</script>
</body></html>""".format(blocks="\n".join(canvas_blocks))


def _start_server(port=8766):
    """Start a simple HTTP server in a daemon thread."""
    os.chdir(PROJECT_ROOT)
    handler = SimpleHTTPRequestHandler
    handler.log_message = lambda *a, **k: None  # suppress logging
    httpd = HTTPServer(("127.0.0.1", port), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def main():
    # ── Pre-flight checks ──────────────────────────────────────
    missing = []
    for tier, info in TIERS.items():
        svg_path = os.path.join(ASSETS_DIR, info["svg"])
        if not os.path.isfile(svg_path):
            missing.append(info["svg"])
    if missing:
        print("ERROR: Missing source SVGs:")
        for m in missing:
            print("  assets/{}".format(m))
        sys.exit(1)

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
    except ImportError:
        print("ERROR: selenium not installed.")
        print("  pip install selenium")
        sys.exit(1)

    # ── Start HTTP server ──────────────────────────────────────
    print("Starting HTTP server on port 8766...")
    httpd = _start_server(8766)

    # ── Write temp HTML ────────────────────────────────────────
    html_path = os.path.join(PROJECT_ROOT, "scripts", "_extract_temp.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(_build_extract_html())

    # ── Launch headless Chrome ─────────────────────────────────
    print("Starting headless Chrome...")
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=2000,2000")

    driver = webdriver.Chrome(options=opts)
    try:
        driver.get("http://127.0.0.1:8766/scripts/_extract_temp.html")
        time.sleep(3)  # wait for JS to finish rendering

        output_el = driver.find_element(By.ID, "output")
        raw = output_el.text
        if not raw:
            print("ERROR: No output from JS. Check SVG files.")
            sys.exit(1)

        data = json.loads(raw)
        os.makedirs(ASSETS_DIR, exist_ok=True)

        for tier, b64 in data.items():
            header, payload = b64.split(",", 1)
            png_bytes = base64.b64decode(payload)
            out_path = os.path.join(
                ASSETS_DIR, "guardian_angel_{}.png".format(tier)
            )
            with open(out_path, "wb") as f:
                f.write(png_bytes)
            expected = TIERS[tier]
            print("  {}: {} bytes -> {} ({}x{})".format(
                tier, len(png_bytes), os.path.basename(out_path),
                expected["w"], expected["h"]
            ))

        print("\nAll 4 tier PNGs saved to assets/.")

    finally:
        driver.quit()
        httpd.shutdown()
        # Clean up temp file
        try:
            os.remove(html_path)
        except OSError:
            pass


if __name__ == "__main__":
    main()
