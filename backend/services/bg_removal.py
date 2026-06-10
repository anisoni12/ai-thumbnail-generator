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
        _session = new_session("u2netp")
        _rembg_available = True
        return _session
    except Exception as e:
        print(f"[bg_removal] rembg unavailable, skipping background removal: {e}")
        _rembg_available = False
        return None

def remove_background(image_bytes: bytes) -> bytes | None:
    session = _ensure_session()
    if session is None:
        return None
    try:
        from rembg import remove
        print(f"[bg_removal] starting removal, input size: {len(image_bytes)} bytes")
        result = remove(image_bytes, session=session)
        print(f"[bg_removal] removal complete, output size: {len(result)} bytes")
        img = Image.open(io.BytesIO(result))
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        out = io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()
    except Exception as e:
        print(f"[bg_removal] removal failed: {e}")
        return None