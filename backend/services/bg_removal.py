"""AI background removal using rembg (U2Net). Runs locally, no API key needed.

First call downloads the ~170MB U2Net model into ~/.u2net/. Subsequent calls are cached.
"""
import io
from PIL import Image

_session = None
_rembg_available = None


def _ensure_session():
    """Lazy-load rembg session. Returns None if rembg isn't installed."""
    global _session, _rembg_available
    if _rembg_available is False:
        return None
    if _session is not None:
        return _session
    try:
        from rembg import new_session  # type: ignore
        _session = new_session("u2net")
        _rembg_available = True
        return _session
    except Exception as e:
        print(f"[bg_removal] rembg unavailable, skipping background removal: {e}")
        _rembg_available = False
        return None


def remove_background(image_bytes: bytes) -> bytes | None:
    """Return PNG bytes (with alpha) of the input image with background removed.
    Returns None if removal fails or rembg isn't installed.
    """
    session = _ensure_session()
    if session is None:
        return None
    try:
        from rembg import remove  # type: ignore
        # rembg returns PNG bytes when input is bytes
        result = remove(image_bytes, session=session)
        # Validate it's a real RGBA PNG
        img = Image.open(io.BytesIO(result))
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        out = io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()
    except Exception as e:
        print(f"[bg_removal] removal failed: {e}")
        return None
