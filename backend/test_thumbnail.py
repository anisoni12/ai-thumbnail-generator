"""Quick local render test for compositor without hitting Gemini/ImageKit.
Pass a real photo path as the first arg to test with a real headshot + bg removal.
"""
import io
import sys
from PIL import Image, ImageDraw
from services.compositor import compose_thumbnail
from services.bg_removal import remove_background
from services.topic_illustration_service import fetch_illustration


def make_dummy_headshot() -> bytes:
    img = Image.new("RGB", (600, 800), (60, 60, 80))
    d = ImageDraw.Draw(img)
    d.ellipse([180, 180, 420, 420], fill=(220, 180, 150))
    d.rectangle([120, 480, 480, 800], fill=(40, 40, 90))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


_real_path = sys.argv[1] if len(sys.argv) > 1 else None
if _real_path:
    with open(_real_path, "rb") as f:
        ORIGINAL = f.read()
else:
    ORIGINAL = make_dummy_headshot()

print("Running AI background removal (first run may download model)...")
CUTOUT = remove_background(ORIGINAL)
USE_BYTES = CUTOUT if CUTOUT else ORIGINAL
IS_CUTOUT = CUTOUT is not None
print(f"Background removal {'succeeded' if IS_CUTOUT else 'failed - using original'}.")


def render(name: str, design: dict, prompt: str, topic: str = ""):
    illus = fetch_illustration(topic or prompt) if (topic or prompt) else None
    if illus:
        print(f"  illustration fetched ({len(illus)} bytes) for '{topic or prompt}'")
    else:
        print(f"  no illustration for '{topic or prompt}'")
    out = compose_thumbnail(USE_BYTES, None, design, prompt_text=prompt,
                            headshot_is_cutout=IS_CUTOUT,
                            illustration_bytes=illus)
    with open(f"test_output_{name}.jpg", "wb") as f:
        f.write(out)
    print(f"  wrote test_output_{name}.jpg")


if __name__ == "__main__":
    render("react_right", {
        "title": "REACT JS",
        "subtitle": "ZERO TO HERO",
        "bg_color": "#0f172a",
        "accent_color": "#00f2ff",
        "text_color": "#ffffff",
        "layout": "headshot_right",
        "style_name": "Dark Tech",
    }, prompt="React JS full course in 5 hours, beginner to advanced", topic="react")

    render("python_left", {
        "title": "PYTHON MASTER",
        "subtitle": "FULL ROADMAP",
        "bg_color": "#1e0a3c",
        "accent_color": "#ffd60a",
        "text_color": "#ffffff",
        "layout": "headshot_left",
        "style_name": "Neon Pop",
    }, prompt="Python for beginners in 3 hours", topic="python")

    render("docker_right", {
        "title": "DOCKER GUIDE",
        "subtitle": "PRODUCTION READY",
        "bg_color": "#0b1d2a",
        "accent_color": "#ff3366",
        "text_color": "#ffffff",
        "layout": "headshot_right",
        "style_name": "Sunset Code",
    }, prompt="Docker and Kubernetes one shot 4 hours", topic="docker")
