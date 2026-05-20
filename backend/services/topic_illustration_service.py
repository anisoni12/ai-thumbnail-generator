"""Topic illustration service.

Fetches a brand / topic logo as a PNG (with alpha) from the Simple Icons CDN
and rasterizes it via svglib + reportlab (pure Python, no native deps).

Used to add a tasteful watermark of the topic logo behind the title text.
"""
from __future__ import annotations

import io
import re
import threading
import httpx
from PIL import Image

# ----- curated alias map -----
# Maps natural-language topic guesses to canonical Simple Icons slugs.
# Simple Icons covers most major brand/tech logos.
ALIASES: dict[str, str] = {
    "react": "react",
    "reactjs": "react",
    "react js": "react",
    "react.js": "react",
    "next": "nextdotjs",
    "nextjs": "nextdotjs",
    "next.js": "nextdotjs",
    "node": "nodedotjs",
    "nodejs": "nodedotjs",
    "node.js": "nodedotjs",
    "javascript": "javascript",
    "js": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "python": "python",
    "py": "python",
    "django": "django",
    "flask": "flask",
    "fastapi": "fastapi",
    "java": "openjdk",
    "spring": "spring",
    "kotlin": "kotlin",
    "swift": "swift",
    "go": "go",
    "golang": "go",
    "rust": "rust",
    "c++": "cplusplus",
    "cpp": "cplusplus",
    "c#": "csharp",
    "csharp": "csharp",
    "ruby": "ruby",
    "rails": "rubyonrails",
    "php": "php",
    "laravel": "laravel",
    "html": "html5",
    "css": "css3",
    "tailwind": "tailwindcss",
    "tailwindcss": "tailwindcss",
    "bootstrap": "bootstrap",
    "vue": "vuedotjs",
    "vuejs": "vuedotjs",
    "angular": "angular",
    "svelte": "svelte",
    "docker": "docker",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "aws": "amazonwebservices",
    "amazon web services": "amazonwebservices",
    "azure": "microsoftazure",
    "gcp": "googlecloud",
    "google cloud": "googlecloud",
    "linux": "linux",
    "ubuntu": "ubuntu",
    "git": "git",
    "github": "github",
    "gitlab": "gitlab",
    "vscode": "visualstudiocode",
    "vs code": "visualstudiocode",
    "mongodb": "mongodb",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "mysql": "mysql",
    "redis": "redis",
    "graphql": "graphql",
    "firebase": "firebase",
    "supabase": "supabase",
    "openai": "openai",
    "chatgpt": "openai",
    "gpt": "openai",
    "gemini": "googlegemini",
    "claude": "anthropic",
    "huggingface": "huggingface",
    "tensorflow": "tensorflow",
    "pytorch": "pytorch",
    "pandas": "pandas",
    "numpy": "numpy",
    "jupyter": "jupyter",
    "android": "android",
    "ios": "apple",
    "flutter": "flutter",
    "react native": "react",
    "unity": "unity",
    "unreal": "unrealengine",
    "blender": "blender",
    "figma": "figma",
    "photoshop": "adobephotoshop",
    # Concept fallbacks (Simple Icons doesn't have these; the service will skip if not found)
    "ai": "openai",
    "machine learning": "tensorflow",
    "ml": "tensorflow",
    "data science": "pandas",
    "web dev": "html5",
    "web development": "html5",
    "system design": "kubernetes",
    "devops": "docker",
    "ethical hacking": "kalilinux",
    "hacking": "kalilinux",
    "cybersecurity": "kalilinux",
    "blockchain": "ethereum",
    "crypto": "bitcoin",
    "linux command": "gnubash",
    "bash": "gnubash",
    "shell": "gnubash",
}

CDN_TEMPLATE = "https://cdn.simpleicons.org/{slug}/{color}"

_lock = threading.Lock()
_cache: dict[str, bytes] = {}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def resolve_slug(topic_query: str) -> str | None:
    """Best-effort slug resolution from a free-form topic query."""
    if not topic_query:
        return None
    q = _normalize(topic_query)
    if q in ALIASES:
        return ALIASES[q]
    # Try first word
    head = q.split()[0]
    if head in ALIASES:
        return ALIASES[head]
    # Fuzzy: any alias key contained in the query
    for key, slug in ALIASES.items():
        if key in q:
            return slug
    # Last resort: pass the cleaned query through as a slug guess
    candidate = re.sub(r"[^a-z0-9]", "", q)
    return candidate or None


def _svg_to_png(svg_bytes: bytes, target_px: int = 512) -> bytes | None:
    """Convert SVG bytes to RGBA PNG with transparent background.

    reportlab always renders on a white background, so we fetch a dark-colored
    icon and threshold out the near-white background pixels, recoloring the
    icon to white so it works as a watermark on any dark template.
    """
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
    except Exception as e:
        print(f"[illustration] svglib unavailable: {e}")
        return None
    try:
        drawing = svg2rlg(io.BytesIO(svg_bytes))
        if drawing is None:
            return None
        # Scale uniformly to target_px on the longer side
        w, h = drawing.width or 1, drawing.height or 1
        scale = target_px / max(w, h)
        drawing.width = w * scale
        drawing.height = h * scale
        drawing.transform = (scale, 0, 0, scale, 0, 0)
        out = io.BytesIO()
        renderPM.drawToFile(drawing, out, fmt="PNG")  # white background
        raw = out.getvalue()

        # Convert white background → transparent, dark icon pixels → white
        img = Image.open(io.BytesIO(raw)).convert("RGBA")
        pixels = list(img.getdata())
        new_pixels = []
        for r, g, b, a in pixels:
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if lum > 240:              # near-white = background
                new_pixels.append((255, 255, 255, 0))
            else:                      # icon pixel → white, alpha from darkness
                icon_alpha = int(255 * (1.0 - lum / 255.0))
                new_pixels.append((255, 255, 255, icon_alpha))
        img.putdata(new_pixels)

        out2 = io.BytesIO()
        img.save(out2, format="PNG")
        return out2.getvalue()
    except Exception as e:
        print(f"[illustration] SVG->PNG render failed: {e}")
        return None


def fetch_illustration(topic_query: str, color_hex: str = "000000",
                       size_px: int = 512, timeout: float = 6.0) -> bytes | None:
    """Return PNG bytes (with alpha) of the topic illustration, or None on failure.
    Cached in-process by (slug, color).
    """
    slug = resolve_slug(topic_query)
    if not slug:
        return None
    color = re.sub(r"[^0-9a-fA-F]", "", color_hex) or "ffffff"
    cache_key = f"{slug}:{color}:{size_px}"

    with _lock:
        if cache_key in _cache:
            return _cache[cache_key]

    url = CDN_TEMPLATE.format(slug=slug, color=color)
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url)
        if resp.status_code != 200 or len(resp.content) < 64:
            print(f"[illustration] {slug} not found at simpleicons CDN ({resp.status_code})")
            return None
        png_bytes = _svg_to_png(resp.content, target_px=size_px)
        if not png_bytes:
            return None
        # Confirm it parses as RGBA
        img = Image.open(io.BytesIO(png_bytes))
        if img.mode != "RGBA":
            img = img.convert("RGBA")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            png_bytes = buf.getvalue()

        with _lock:
            _cache[cache_key] = png_bytes
        return png_bytes
    except Exception as e:
        print(f"[illustration] fetch failed for {slug}: {e}")
        return None
