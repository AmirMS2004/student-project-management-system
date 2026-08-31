import base64
import io
import random
import threading
import time
import uuid

from PIL import Image, ImageDraw, ImageFont

CAPTCHA_TTL_SECONDS = 5 * 60
CAPTCHA_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # avoid ambiguous chars

_store: dict[str, tuple[str, float]] = {}
_lock = threading.Lock()


def _cleanup_expired():
    now = time.time()
    expired = [key for key, (_, expires_at) in _store.items() if expires_at < now]
    for key in expired:
        _store.pop(key, None)


def _render_image(code: str) -> bytes:
    width, height = 160, 60
    image = Image.new("RGB", (width, height), color=(245, 246, 250))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 34)
    except OSError:
        font = ImageFont.load_default()

    # noisy background lines
    for _ in range(6):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line((x1, y1, x2, y2), fill=(200, 205, 215), width=2)

    for i, char in enumerate(code):
        x = 15 + i * 28 + random.randint(-4, 4)
        y = random.randint(5, 15)
        angle = random.randint(-25, 25)
        char_img = Image.new("RGBA", (40, 40), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_img)
        char_draw.text((5, 0), char, font=font, fill=(40, 50, 70, 255))
        char_img = char_img.rotate(angle, expand=1)
        image.paste(char_img, (x, y), char_img)

    # noisy dots
    for _ in range(80):
        x, y = random.randint(0, width - 1), random.randint(0, height - 1)
        draw.point((x, y), fill=(180, 185, 195))

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_captcha() -> tuple[str, str]:
    """Returns (captcha_id, base64_png). The plaintext code is stored server-side only."""
    with _lock:
        _cleanup_expired()
        code = "".join(random.choices(CAPTCHA_CHARS, k=5))
        captcha_id = uuid.uuid4().hex
        _store[captcha_id] = (code, time.time() + CAPTCHA_TTL_SECONDS)

    image_bytes = _render_image(code)
    return captcha_id, base64.b64encode(image_bytes).decode("ascii")


def verify_captcha(captcha_id: str, answer: str) -> bool:
    with _lock:
        _cleanup_expired()
        entry = _store.pop(captcha_id, None)

    if not entry:
        return False
    code, expires_at = entry
    if time.time() > expires_at:
        return False
    return code.strip().upper() == (answer or "").strip().upper()
