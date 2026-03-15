"""Guardian Angel -- Overlay Renderer

Transparent, always-on-top, click-through Win32 overlay window
that spans all monitors.  Renders censor boxes over NSFW detections
using the active censor style from config.json.

Requirements:  pywin32, Pillow, mss  (all in requirements.txt)
Python target: 3.11 -- no walrus, no match/case.
"""

import ctypes
import ctypes.wintypes
import json
import os
import threading
import time
import traceback
from io import BytesIO

import mss
import win32api
import win32con
import win32gui
import win32ui
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Guardian Angel art is loaded from pre-rendered PNG assets
# in assets/guardian_angel_{tier}.png.  No SVG library at runtime.

# ── ctypes helpers for per-monitor DPI ──────────────────────────

_shcore = None
try:
    _shcore = ctypes.windll.shcore
except OSError:
    pass  # older Windows without shcore

_MDT_EFFECTIVE_DPI = 0


def _get_dpi_for_monitor(hmonitor):
    """Return the effective DPI for *hmonitor* via GetDpiForMonitor.

    Falls back to 96 (100 %) if the call is unavailable.
    """
    if _shcore is None:
        return 96
    dpi_x = ctypes.c_uint()
    dpi_y = ctypes.c_uint()
    try:
        _shcore.GetDpiForMonitor(
            hmonitor,
            _MDT_EFFECTIVE_DPI,
            ctypes.byref(dpi_x),
            ctypes.byref(dpi_y),
        )
        return dpi_x.value
    except Exception:
        return 96


def _enum_display_monitors():
    """Return a list of dicts with monitor rects and DPI values."""
    monitors = []

    def _callback(hmon, hdc, lprect, lparam):
        rect = lprect.contents
        dpi = _get_dpi_for_monitor(hmon)
        monitors.append({
            "hmonitor": hmon,
            "left": rect.left,
            "top": rect.top,
            "right": rect.right,
            "bottom": rect.bottom,
            "width": rect.right - rect.left,
            "height": rect.bottom - rect.top,
            "dpi": dpi,
            "scale": dpi / 96.0,
        })
        return True

    MONITORENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.POINTER(ctypes.wintypes.RECT),
        ctypes.c_double,
    )
    ctypes.windll.user32.EnumDisplayMonitors(
        None, None, MONITORENUMPROC(_callback), 0
    )
    return monitors


# ── config loader ───────────────────────────────────────────────

def _project_root():
    """Return the absolute project root path."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def _load_config():
    """Load config.json from the project root."""
    config_path = os.path.join(_project_root(), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Guardian Angel art loader ───────────────────────────────────

class _GuardianAngelSVG:
    """Loads pre-rendered per-tier PNG assets and caches as Pillow
    RGBA images.

    The PNGs are extracted from per-tier SVGs at 2x native resolution
    by scripts/extract_tier_pngs.py (Selenium headless Chrome,
    build-time only — never used at runtime).

    Asset files:
        assets/guardian_angel_full.png    520x600  (from 260x300 SVG)
        assets/guardian_angel_medium.png  800x200  (from 400x100 SVG)
        assets/guardian_angel_small.png   140x140  (from 70x70 SVG)
        assets/guardian_angel_micro.png   120x120  (from 60x60 SVG)
    """

    _TIER_FILES = {
        "full":   "assets/guardian_angel_full.png",
        "medium": "assets/guardian_angel_medium.png",
        "small":  "assets/guardian_angel_small.png",
        "micro":  "assets/guardian_angel_micro.png",
    }

    def __init__(self):
        self._images = {}   # tier -> PIL.Image.Image (RGBA)
        self._loaded = False
        self._load()

    def _load(self):
        """Load per-tier PNG assets from the assets directory."""
        root = _project_root()
        try:
            for tier, rel_path in self._TIER_FILES.items():
                png_path = os.path.join(root, rel_path)
                if not os.path.isfile(png_path):
                    print("[WARNING] Guardian Angel PNG missing: "
                          "{}".format(png_path))
                    return   # all files must be present
                self._images[tier] = Image.open(png_path).convert("RGBA")
            self._loaded = True
        except Exception:
            traceback.print_exc()
            print("[WARNING] Guardian Angel art failed to load — "
                  "falling back to gold rect.")
            self._images.clear()
            self._loaded = False

    @property
    def available(self):
        """True if PNG images were loaded successfully."""
        return self._loaded

    def get_tier_image(self, tier, width, height):
        """Return a Pillow RGBA image for *tier* scaled to fit
        *width* x *height*, or None if unavailable."""
        tier_key = tier.lower()
        img = self._images.get(tier_key)
        if img is None:
            return None
        try:
            return img.resize((width, height), Image.LANCZOS)
        except Exception:
            return None

    # Alias for internal use
    get = get_tier_image


# ── colour helpers ──────────────────────────────────────────────

def _hex_to_rgb(hexstr):
    """Convert '#RRGGBB' to an (R, G, B) tuple."""
    hexstr = hexstr.lstrip("#")
    return tuple(int(hexstr[i:i + 2], 16) for i in (0, 2, 4))


# ── overlay renderer ───────────────────────────────────────────

class OverlayRenderer:
    """Full-screen transparent overlay rendered via pywin32 + Pillow.

    Lifecycle
    ---------
    1.  ``__init__`` reads config and enumerates monitors.
    2.  ``start()`` creates the Win32 window on a background thread.
    3.  ``update_boxes(boxes)`` is called each frame by the pipeline.
    4.  ``stop()`` destroys the window and joins the thread.
    """

    # Win32 class name (arbitrary, unique enough)
    _WND_CLASS = "GuardianAngelOverlay"

    def __init__(self):
        config = _load_config()

        # Censor config
        censor_cfg = config.get("censor", {})
        self._style = censor_cfg.get("style", "guardian_angel")
        self._custom_colour = _hex_to_rgb(
            censor_cfg.get("solid_custom_color", "#000000")
        )

        # Overlay config
        overlay_cfg = config.get("overlay", {})
        self._opacity = overlay_cfg.get("opacity", 1.0)
        self._click_through = overlay_cfg.get("click_through", True)
        self._always_on_top = overlay_cfg.get("always_on_top", True)

        # Dev mode
        self._dev_mode = config.get("dev_mode", False)

        # Load SVG angel art (falls back silently if unavailable)
        self._angel_svg = _GuardianAngelSVG()

        # Monitor geometry (virtual desktop)
        self._monitors = _enum_display_monitors()
        self._virt_left = 0
        self._virt_top = 0
        self._virt_width = 1
        self._virt_height = 1
        self._compute_virtual_desktop()

        # Shared state
        self._boxes = []           # type: list[dict]
        self._lock = threading.Lock()
        self._hwnd = None          # type: int | None
        self._running = False
        self._thread = None        # type: threading.Thread | None

    # ── geometry ────────────────────────────────────────────────

    def _compute_virtual_desktop(self):
        """Calculate bounding rect of all monitors (virtual desktop)."""
        if not self._monitors:
            self._virt_left = 0
            self._virt_top = 0
            self._virt_width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            self._virt_height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
            return
        left = min(m["left"] for m in self._monitors)
        top = min(m["top"] for m in self._monitors)
        right = max(m["right"] for m in self._monitors)
        bottom = max(m["bottom"] for m in self._monitors)
        self._virt_left = left
        self._virt_top = top
        self._virt_width = right - left
        self._virt_height = bottom - top

    def _find_monitor_for_point(self, x, y):
        """Return the monitor dict whose rect contains (x, y), or None."""
        for m in self._monitors:
            if m["left"] <= x < m["right"] and m["top"] <= y < m["bottom"]:
                return m
        return None

    def _scale_box(self, box):
        """Apply per-monitor DPI scaling to a bounding box dict.

        Returns a new dict with scaled x, y, width, height.
        """
        mon = self._find_monitor_for_point(box["x"], box["y"])
        if mon is None:
            return dict(box)  # no scaling if monitor not found

        scale = mon["scale"]
        scaled = dict(box)
        # The detection pipeline works in physical pixels (mss captures
        # at native resolution).  The overlay window lives in virtual
        # (logical) coordinates because we call SetProcessDPIAware.
        # We need to convert physical coords → logical coords.
        if scale > 0:
            rel_x = box["x"] - mon["left"]
            rel_y = box["y"] - mon["top"]
            scaled["x"] = mon["left"] + int(rel_x / scale)
            scaled["y"] = mon["top"] + int(rel_y / scale)
            scaled["width"] = int(box["width"] / scale)
            scaled["height"] = int(box["height"] / scale)
        return scaled

    # ── public API ──────────────────────────────────────────────

    def update_boxes(self, boxes):
        """Replace the current bounding boxes with *boxes*.

        Each dict should contain at minimum:
            x, y, width, height, tier
        Optionally:  confidence, label, monitor_id
        """
        with self._lock:
            self._boxes = list(boxes)
        # Trigger a repaint
        if self._hwnd:
            try:
                win32gui.InvalidateRect(self._hwnd, None, True)
            except Exception:
                pass

    def start(self):
        """Create the overlay window on a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._window_thread, daemon=True, name="GA-Overlay"
        )
        self._thread.start()

    def stop(self):
        """Destroy the overlay window and join the thread."""
        self._running = False
        if self._hwnd:
            try:
                win32gui.PostMessage(self._hwnd, win32con.WM_CLOSE, 0, 0)
            except Exception:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

    # ── Win32 window management ─────────────────────────────────

    def _window_thread(self):
        """Create & run the Win32 overlay window message loop."""
        try:
            # Make this process DPI-aware so coordinates match the desktop
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self._wnd_proc
            wc.lpszClassName = self._WND_CLASS
            wc.hbrBackground = win32gui.GetStockObject(win32con.HOLLOW_BRUSH)
            wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
            wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW

            try:
                win32gui.RegisterClass(wc)
            except Exception:
                pass  # class may already be registered

            # Layered  +  transparent  +  topmost  +  tool-window (no taskbar)
            ex_style = (
                win32con.WS_EX_LAYERED
                | win32con.WS_EX_TOPMOST
                | win32con.WS_EX_TOOLWINDOW
            )
            if self._click_through:
                ex_style |= win32con.WS_EX_TRANSPARENT

            self._hwnd = win32gui.CreateWindowEx(
                ex_style,
                self._WND_CLASS,
                "Guardian Angel Overlay",
                win32con.WS_POPUP,
                self._virt_left,
                self._virt_top,
                self._virt_width,
                self._virt_height,
                0,
                0,
                0,
                None,
            )

            # NOTE: do NOT call SetLayeredWindowAttributes here.
            # It conflicts with UpdateLayeredWindow(ULW_ALPHA) which
            # we use in _blit_canvas for per-pixel alpha rendering.
            # They are mutually exclusive — LWA takes ownership of
            # the layered surface and silently ignores ULW calls.

            win32gui.ShowWindow(self._hwnd, win32con.SW_SHOW)
            win32gui.UpdateWindow(self._hwnd)

            # Direct paint loop at ~60 fps.
            # We call _paint ourselves each iteration and use
            # PumpWaitingMessages to handle WM_CLOSE / WM_DESTROY.
            while self._running:
                win32gui.PumpWaitingMessages()
                self._paint(self._hwnd)
                time.sleep(0.016)  # ~60 fps

        except Exception:
            traceback.print_exc()
        finally:
            if self._hwnd:
                try:
                    win32gui.DestroyWindow(self._hwnd)
                except Exception:
                    pass
                self._hwnd = None

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """Window procedure for the overlay."""
        if msg == win32con.WM_DESTROY:
            self._running = False
            win32gui.PostQuitMessage(0)
            return 0

        if msg == win32con.WM_TIMER or msg == win32con.WM_PAINT:
            self._paint(hwnd)
            return 0

        if msg == win32con.WM_ERASEBKGND:
            return 1  # prevent default erase (we handle it)

        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    # ── rendering ───────────────────────────────────────────────

    def _paint(self, hwnd):
        """Render all active censor boxes onto the overlay using Pillow
        and blit via UpdateLayeredWindow for per-pixel alpha."""
        with self._lock:
            boxes = list(self._boxes)

        width = self._virt_width
        height = self._virt_height

        if width <= 0 or height <= 0:
            return

        # Create a transparent RGBA canvas
        canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        for box in boxes:
            sbox = self._scale_box(box)
            # Convert absolute coords to overlay-relative coords
            bx = sbox["x"] - self._virt_left
            by = sbox["y"] - self._virt_top
            bw = sbox.get("width", 100)
            bh = sbox.get("height", 100)
            tier = sbox.get("tier", "full").upper()
            conf = sbox.get("confidence", 0.0)
            label = sbox.get("label", "")

            if bw <= 0 or bh <= 0:
                continue

            rect = (bx, by, bx + bw, by + bh)

            self._render_style(draw, canvas, rect, tier)

            # Dev mode: red border + debug text
            if self._dev_mode:
                draw.rectangle(rect, outline=(255, 0, 0, 255), width=2)
                debug_text = "{} | {:.0f}%".format(tier, conf * 100)
                try:
                    font = ImageFont.truetype("arial.ttf", 14)
                except Exception:
                    font = ImageFont.load_default()
                draw.text(
                    (bx + 4, by + 4),
                    debug_text,
                    fill=(255, 0, 0, 255),
                    font=font,
                )

        # Blit canvas to overlay via UpdateLayeredWindow
        self._blit_canvas(hwnd, canvas)

    def _render_style(self, draw, canvas, rect, tier):
        """Render the active censor style inside *rect*."""
        style = self._style
        bx, by, bx2, by2 = rect

        if style == "guardian_angel":
            self._render_guardian_angel(draw, rect, tier)
        elif style == "solid_black":
            draw.rectangle(rect, fill=(0, 0, 0, 255))
        elif style == "solid_white":
            draw.rectangle(rect, fill=(255, 255, 255, 255))
        elif style == "solid_custom":
            r, g, b = self._custom_colour
            draw.rectangle(rect, fill=(r, g, b, 255))
        elif style == "blur_light":
            self._render_blur(canvas, rect, radius=5)
        elif style == "blur_medium":
            self._render_blur(canvas, rect, radius=15)
        elif style == "blur_heavy":
            self._render_blur(canvas, rect, radius=30)
        elif style == "pixelate":
            self._render_pixelate(canvas, rect)
        else:
            # Unknown style — default to solid black
            draw.rectangle(rect, fill=(0, 0, 0, 255))

    def _render_guardian_angel(self, draw, rect, tier):
        """Render the Guardian Angel censor art.

        Attempts to use the pre-loaded PNG tier images.  If the PNGs
        are unavailable (files missing, Pillow error, etc.), falls
        back to the simple gold rect + wing-shape placeholder.
        """
        bx, by, bx2, by2 = rect
        bw = bx2 - bx
        bh = by2 - by
        gold = (201, 168, 76, 240)  # #C9A84C with high alpha
        white = (255, 255, 255, 255)

        # Gold background always drawn first (visible if SVG fails)
        draw.rectangle(rect, fill=gold)

        # Try SVG art — composited on top of the gold background
        if self._angel_svg.available and bw > 0 and bh > 0:
            svg_img = self._angel_svg.get(tier, bw, bh)
            if svg_img is not None:
                # Get the canvas Image that the draw object belongs to
                canvas = draw.im
                # Paste the SVG image; need to access the underlying
                # Pillow Image from ImageDraw — use _image attribute
                try:
                    pil_canvas = draw._image
                    pil_canvas.paste(svg_img, (bx, by), svg_img)
                    return  # SVG rendered successfully
                except Exception:
                    pass  # fall through to placeholder

        # ── Fallback: simple wing-shape placeholder ─────────────
        cx = bx + bw // 2
        cy = by + bh // 2

        if tier == "FULL" or tier == "MEDIUM":
            # Wing-like chevron
            wing_w = min(bw // 3, 60)
            wing_h = min(bh // 3, 40)
            # Left wing
            draw.polygon(
                [
                    (cx - 2, cy - wing_h),
                    (cx - wing_w, cy),
                    (cx - 2, cy + wing_h // 2),
                ],
                fill=white,
            )
            # Right wing
            draw.polygon(
                [
                    (cx + 2, cy - wing_h),
                    (cx + wing_w, cy),
                    (cx + 2, cy + wing_h // 2),
                ],
                fill=white,
            )
            # Nur orb
            orb_r = min(bw, bh) // 8
            draw.ellipse(
                (cx - orb_r, cy - orb_r - wing_h, cx + orb_r, cy + orb_r - wing_h),
                fill=white,
            )
        elif tier == "SMALL":
            # Smaller wing + orb
            wing_w = min(bw // 4, 20)
            wing_h = min(bh // 4, 15)
            draw.polygon(
                [(cx, cy - wing_h), (cx - wing_w, cy), (cx, cy + wing_h // 2)],
                fill=white,
            )
            draw.polygon(
                [(cx, cy - wing_h), (cx + wing_w, cy), (cx, cy + wing_h // 2)],
                fill=white,
            )
            orb_r = max(min(bw, bh) // 10, 3)
            draw.ellipse(
                (cx - orb_r, cy - orb_r - wing_h, cx + orb_r, cy + orb_r - wing_h),
                fill=white,
            )
        else:
            # MICRO — nur orb only
            orb_r = max(min(bw, bh) // 4, 3)
            draw.ellipse(
                (cx - orb_r, cy - orb_r, cx + orb_r, cy + orb_r),
                fill=white,
            )

    def _render_blur(self, canvas, rect, radius=15):
        """Approximate gaussian blur by filling the region with a
        semi-transparent frosted-glass look.

        Real blur of the screen beneath requires screen capture inside the
        overlay loop (Phase 4 integration).  For now we render a frosted
        white overlay to indicate blur.
        """
        bx, by, bx2, by2 = rect
        region = canvas.crop((bx, by, bx2, by2))
        # Fill with translucent white then blur
        frost = Image.new("RGBA", region.size, (255, 255, 255, 180))
        frost = frost.filter(ImageFilter.GaussianBlur(radius=radius))
        canvas.paste(frost, (bx, by))

    def _render_pixelate(self, canvas, rect):
        """Render a pixelation effect over the region.

        True pixelation of underlying screen content needs capture
        integration (Phase 4).  Placeholder: mosaic-style coloured blocks.
        """
        bx, by, bx2, by2 = rect
        bw = bx2 - bx
        bh = by2 - by
        block_size = max(bw // 8, 4)
        draw = ImageDraw.Draw(canvas)
        colours = [
            (60, 60, 60, 220),
            (90, 90, 90, 220),
            (120, 120, 120, 220),
            (80, 80, 80, 220),
        ]
        idx = 0
        y = by
        while y < by2:
            x = bx
            while x < bx2:
                x2 = min(x + block_size, bx2)
                y2 = min(y + block_size, by2)
                draw.rectangle((x, y, x2, y2), fill=colours[idx % len(colours)])
                idx += 1
                x += block_size
            y += block_size

    # ── blit helpers ────────────────────────────────────────────

    def _blit_canvas(self, hwnd, canvas):
        """Copy the Pillow RGBA canvas to the layered window via
        UpdateLayeredWindow for proper per-pixel alpha."""
        try:
            width = canvas.width
            height = canvas.height

            # Convert RGBA → BGRA for the Windows bitmap
            r, g, b, a = canvas.split()
            bgra = Image.merge("RGBA", (b, g, r, a))

            hdc_screen = win32gui.GetDC(0)
            hdc_mem = win32gui.CreateCompatibleDC(hdc_screen)

            # Create a 32-bit DIB section
            bmi = _make_bitmapinfo(width, height)
            ppv_bits = ctypes.c_void_p()
            hbmp = ctypes.windll.gdi32.CreateDIBSection(
                hdc_mem,
                ctypes.byref(bmi),
                0,  # DIB_RGB_COLORS
                ctypes.byref(ppv_bits),
                None,
                0,
            )
            if not hbmp or not ppv_bits.value:
                win32gui.DeleteDC(hdc_mem)
                win32gui.ReleaseDC(0, hdc_screen)
                return

            old_bmp = ctypes.windll.gdi32.SelectObject(hdc_mem, hbmp)

            # Copy pixel data into the DIB
            raw = bgra.tobytes()
            # DIBs are bottom-up; flip rows
            stride = width * 4
            flipped = b""
            for row in range(height - 1, -1, -1):
                flipped += raw[row * stride : (row + 1) * stride]
            ctypes.memmove(ppv_bits, flipped, len(flipped))

            # UpdateLayeredWindow
            pt_src = _make_point(0, 0)
            pt_dst = _make_point(self._virt_left, self._virt_top)
            sz = _make_size(width, height)
            blend = _make_blendfunction(alpha=255)

            ctypes.windll.user32.UpdateLayeredWindow(
                hwnd,
                hdc_screen,
                ctypes.byref(pt_dst),
                ctypes.byref(sz),
                hdc_mem,
                ctypes.byref(pt_src),
                0,
                ctypes.byref(blend),
                2,  # ULW_ALPHA
            )

            # Cleanup
            ctypes.windll.gdi32.SelectObject(hdc_mem, old_bmp)
            ctypes.windll.gdi32.DeleteObject(hbmp)
            win32gui.DeleteDC(hdc_mem)
            win32gui.ReleaseDC(0, hdc_screen)

        except Exception:
            traceback.print_exc()


# ── ctypes structures for UpdateLayeredWindow ───────────────────

class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.wintypes.DWORD),
        ("biWidth", ctypes.wintypes.LONG),
        ("biHeight", ctypes.wintypes.LONG),
        ("biPlanes", ctypes.wintypes.WORD),
        ("biBitCount", ctypes.wintypes.WORD),
        ("biCompression", ctypes.wintypes.DWORD),
        ("biSizeImage", ctypes.wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.wintypes.LONG),
        ("biYPelsPerMeter", ctypes.wintypes.LONG),
        ("biClrUsed", ctypes.wintypes.DWORD),
        ("biClrImportant", ctypes.wintypes.DWORD),
    ]


class _BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", _BITMAPINFOHEADER),
    ]


class _BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_byte),
        ("BlendFlags", ctypes.c_byte),
        ("SourceConstantAlpha", ctypes.c_byte),
        ("AlphaFormat", ctypes.c_byte),
    ]


def _make_bitmapinfo(width, height):
    bmi = _BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = width
    bmi.bmiHeader.biHeight = height  # positive = bottom-up
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0  # BI_RGB
    return bmi


def _make_point(x, y):
    pt = ctypes.wintypes.POINT()
    pt.x = x
    pt.y = y
    return pt


def _make_size(cx, cy):
    sz = ctypes.wintypes.SIZE()
    sz.cx = cx
    sz.cy = cy
    return sz


def _make_blendfunction(alpha=255):
    bf = _BLENDFUNCTION()
    bf.BlendOp = 0  # AC_SRC_OVER
    bf.BlendFlags = 0
    bf.SourceConstantAlpha = alpha
    bf.AlphaFormat = 1  # AC_SRC_ALPHA
    return bf
