"""
System tray integration for Sobriety Counter.
Uses pystray for cross-platform tray icon support.
"""
import threading

try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False


def create_tray_icon_image(text="SC", bg_color="#5B86E5", fg_color="#ffffff"):
    """Create a simple tray icon with text."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw circle background
    r, g, b = _hex_to_rgb(bg_color)
    draw.ellipse([2, 2, size - 2, size - 2], fill=(r, g, b, 255))

    # Draw text
    fr, fg_, fb = _hex_to_rgb(fg_color)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("Arial Bold", 22)
        except (OSError, IOError):
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) // 2
    y = (size - th) // 2 - 2
    draw.text((x, y), text, fill=(fr, fg_, fb, 255), font=font)
    return img


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class TrayManager:
    """Manages the system tray icon and menu."""

    def __init__(self, show_callback, quit_callback, get_stats_fn):
        """
        show_callback: called when user clicks "Show" in tray menu
        quit_callback: called when user clicks "Quit" in tray menu
        get_stats_fn: callable returning list of (tracker_name, days_sober) tuples
        """
        self._show = show_callback
        self._quit = quit_callback
        self._get_stats = get_stats_fn
        self._icon = None
        self._thread = None

    def start(self):
        if not HAS_TRAY:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass

    def update_tooltip(self, text):
        if self._icon:
            try:
                self._icon.title = text
            except Exception:
                pass

    def _build_menu(self):
        items = []
        try:
            stats = self._get_stats()
            for name, days in stats:
                items.append(pystray.MenuItem(f"{name}: {days} days", None, enabled=False))
            if items:
                items.append(pystray.Menu.SEPARATOR)
        except Exception:
            pass

        items.extend([
            pystray.MenuItem("Show", lambda: self._show()),
            pystray.MenuItem("Quit", lambda: self._quit()),
        ])
        return pystray.Menu(*items)

    def _run(self):
        image = create_tray_icon_image()
        self._icon = pystray.Icon(
            "sobriety_counter",
            image,
            "Sobriety Counter",
            menu=self._build_menu(),
        )
        self._icon.run()
