"""
bg_generator.py
---------------
Fetches AI-generated background images for thumbnails.

Priority order:
  1. Pollinations.ai  (free, no key)
  2. Hugging Face Inference API  (free tier, needs HF_TOKEN env var)
  3. Graceful fallback → returns None (composer uses its own gradient bg)

Usage:
    from bg_generator import fetch_background

    bg_bytes = fetch_background(
        style="dark cinematic",
        topic="Python",
        accent_color="#7c3aed"
    )
    # bg_bytes is JPEG bytes or None
"""

import os
import re
import time
import random
import requests
from urllib.parse import quote

# ── Prompt builder ──────────────────────────────────────────────────────────

STYLE_PROMPTS = {
    "dark cinematic": (
        "cinematic dark background, dramatic volumetric lighting, "
        "deep shadows, atmospheric fog, 8k wallpaper, no text, no people"
    ),
    "neon cyberpunk": (
        "cyberpunk neon city background, glowing neon lights, "
        "rain reflections, dark night, ultra-detailed, no text, no people"
    ),
    "bold gradient": (
        "abstract bold gradient background, geometric shapes, "
        "vibrant colors, modern design, clean, no text, no people"
    ),
    "tech abstract": (
        "abstract technology background, glowing circuits, "
        "digital particles, dark theme, futuristic, no text, no people"
    ),
    "editorial clean": (
        "clean minimal editorial background, soft gradient, "
        "subtle texture, professional, no text, no people"
    ),
    "bright pop": (
        "bright bold pop-art background, high contrast colors, "
        "dynamic energy, graphic design, no text, no people"
    ),
}

TOPIC_MODIFIERS = {
    "python": "with snake scales texture overlay, green tones",
    "javascript": "with floating JS code particles, yellow accents",
    "react": "with floating atom logo shapes, blue tones",
    "node": "with green circuit traces, dark forest tones",
    "docker": "with container/cube geometric shapes, teal tones",
    "aws": "with cloud formations, orange AWS tones",
    "ai": "with neural network visualization, purple glowing nodes",
    "ml": "with data flow visualization, blue gradient",
    "devops": "with pipeline flow visualization, orange tones",
    "sql": "with database rows grid pattern, blue steel tones",
    "rust": "with metallic texture, orange rust tones",
    "java": "with coffee cup steam silhouette, red tones",
}


def _build_prompt(style: str, topic: str, accent_color: str) -> str:
    base = STYLE_PROMPTS.get(style, STYLE_PROMPTS["dark cinematic"])

    # Topic-specific modifier
    topic_lower = (topic or "").lower()
    modifier = ""
    for key, mod in TOPIC_MODIFIERS.items():
        if key in topic_lower:
            modifier = f", {mod}"
            break

    # Derive a color hint from accent
    color_hint = _color_name(accent_color)

    prompt = f"{base}{modifier}, accent color {color_hint}, ultra high quality, 16:9"
    return prompt


def _color_name(hex_color: str) -> str:
    """Very rough hex → color name for prompting."""
    try:
        h = hex_color.strip().lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        if r > 200 and g < 100 and b < 100:
            return "vivid red"
        if r > 200 and g > 150 and b < 80:
            return "golden yellow"
        if r < 80 and g > 180 and b < 80:
            return "bright green"
        if r < 80 and g < 80 and b > 200:
            return "deep blue"
        if r > 150 and g < 80 and b > 180:
            return "purple violet"
        if r < 80 and g > 180 and b > 180:
            return "cyan teal"
        if r > 200 and g > 80 and b < 80:
            return "vivid orange"
        return "neutral"
    except Exception:
        return "neutral"


# ── Provider 1: Pollinations.ai ─────────────────────────────────────────────

def _fetch_pollinations(prompt: str, seed: int | None = None) -> bytes | None:
    """
    Free, no key needed.
    Returns image bytes or None on failure.
    """
    try:
        encoded = quote(prompt)
        seed_param = f"&seed={seed}" if seed is not None else f"&seed={random.randint(1, 99999)}"
        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width=1280&height=720&model=flux&nologo=true&enhance=true{seed_param}"
        )
        r = requests.get(url, timeout=25, headers={"User-Agent": "ThumbnailPro/1.0"})
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
            print(f"[bg_generator] Pollinations OK ({len(r.content)} bytes)")
            return r.content
        print(f"[bg_generator] Pollinations failed: {r.status_code}")
    except Exception as e:
        print(f"[bg_generator] Pollinations error: {e}")
    return None


# ── Provider 2: Hugging Face Inference API ──────────────────────────────────

HF_MODELS = [
    "stabilityai/stable-diffusion-xl-base-1.0",
    "runwayml/stable-diffusion-v1-5",
    "CompVis/stable-diffusion-v1-4",
]


def _fetch_huggingface(prompt: str) -> bytes | None:
    """
    Free tier available. Needs HF_TOKEN environment variable.
    Falls back gracefully if token missing.
    """
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if not token:
        print("[bg_generator] HF_TOKEN not set, skipping Hugging Face")
        return None

    for model in HF_MODELS:
        try:
            url = f"https://api-inference.huggingface.co/models/{model}"
            headers = {"Authorization": f"Bearer {token}"}
            payload = {
                "inputs": prompt,
                "parameters": {
                    "width": 1280,
                    "height": 720,
                    "num_inference_steps": 25,
                    "guidance_scale": 7.5,
                },
            }
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                print(f"[bg_generator] HuggingFace OK via {model} ({len(r.content)} bytes)")
                return r.content
            if r.status_code == 503:
                # Model loading, wait and retry once
                print(f"[bg_generator] {model} loading, waiting 10s...")
                time.sleep(10)
                r2 = requests.post(url, headers=headers, json=payload, timeout=60)
                if r2.status_code == 200:
                    return r2.content
            print(f"[bg_generator] HF {model}: {r.status_code}")
        except Exception as e:
            print(f"[bg_generator] HF {model} error: {e}")
            continue
    return None


# ── Public API ───────────────────────────────────────────────────────────────

STYLES = list(STYLE_PROMPTS.keys())


def fetch_background(
    style: str | None = None,
    topic: str = "",
    accent_color: str = "#7c3aed",
    seed: int | None = None,
    provider: str = "auto",  # "auto" | "pollinations" | "huggingface"
) -> bytes | None:
    """
    Fetch an AI-generated background image.

    Args:
        style:        One of STYLES, or None for random pick.
        topic:        e.g. "Python", "React", "Docker" — adds style modifier.
        accent_color: Hex color hint for the prompt.
        seed:         Optional seed for reproducibility (Pollinations).
        provider:     "auto" tries Pollinations first, then HuggingFace.

    Returns:
        JPEG/PNG bytes, or None if all providers failed.
    """
    if style is None or style not in STYLE_PROMPTS:
        style = random.choice(STYLES)

    prompt = _build_prompt(style, topic, accent_color)
    print(f"[bg_generator] Prompt: {prompt[:80]}...")

    if provider in ("auto", "pollinations"):
        result = _fetch_pollinations(prompt, seed=seed)
        if result:
            return result

    if provider in ("auto", "huggingface"):
        result = _fetch_huggingface(prompt)
        if result:
            return result

    print("[bg_generator] All providers failed, returning None (will use gradient bg)")
    return None


def style_for_template(template_index: int) -> str:
    """Map template index → a fitting background style."""
    mapping = {
        0: "bold gradient",       # Split diagonal
        1: "dark cinematic",      # Dark cinematic
        2: "bright pop",          # Bright bold
        3: "editorial clean",     # Editorial magazine
        4: "neon cyberpunk",      # Neon grid
        5: "tech abstract",       # Stacked layers
    }
    return mapping.get(template_index, random.choice(STYLES))