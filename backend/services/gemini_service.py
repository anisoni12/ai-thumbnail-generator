from google import genai
from google.genai import types
from config import settings
import json
import time
import re

client = genai.Client(api_key=settings.GEMINI_API_KEY)

MODELS_TO_TRY = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

def _clean_json(text: str) -> str:
    """Strip markdown fences and extract the JSON array."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return match.group(0)
    return text

def get_thumbnail_designs(prompt: str, style_count: int) -> list:
    sys_prompt = f"""You are an expert YouTube thumbnail designer for educational tech content.
Generate {style_count} DIFFERENT thumbnail designs for the user's video idea.
The final image will be composed locally from the user's real headshot + a styled gradient background + text overlays. You are NOT generating an image, only design metadata.

Return ONLY a valid JSON array (no markdown, no backticks, no explanation).
Each object MUST contain ALL of these fields:

- "title": Punchy main text overlay, max 3 words, ALL CAPS, NO emojis. Should NAME the topic clearly (e.g. "REACT JS", "PYTHON MASTER", "DOCKER GUIDE", "SYSTEM DESIGN").
- "subtitle": Supporting tagline, max 4 words, ALL CAPS, NO emojis (e.g. "ZERO TO HERO", "BEGINNER TO PRO", "FULL ROADMAP", "IN ONE VIDEO").
- "prompt_used": One short sentence describing the overall vibe (for display only).
- "fal_prompt": Short description of background mood/style (used only as metadata, not for image generation).
- "bg_color": A DARK hex base color suitable for a YouTube thumbnail background (e.g. "#0f172a", "#1a1a2e", "#1e0a3c", "#0b1d2a", "#1a0f2e"). Avoid pure black and avoid bright colors here.
- "accent_color": A VIVID hex highlight color that contrasts well with bg_color (e.g. "#00f2ff", "#ff3366", "#ffd60a", "#7c3aed", "#22c55e", "#f97316").
- "text_color": Either "#ffffff" or "#ffeb3b". Use "#ffffff" by default.
- "layout": One of "headshot_right" or "headshot_left". Vary across the {style_count} designs.
- "style_name": A short distinctive label (e.g. "Dark Tech", "Neon Pop", "Cyber Glow", "Sunset Code").
- "topic_slug": The single most relevant brand/tech logo slug for the video idea, lowercase, no spaces. Use Simple Icons slugs when possible (e.g. "react", "python", "docker", "kubernetes", "javascript", "typescript", "nodedotjs", "nextdotjs", "vuedotjs", "angular", "tensorflow", "pytorch", "openai", "googlegemini", "amazonwebservices", "github", "linux", "kalilinux", "mongodb", "postgresql"). If no obvious brand applies, give a single concept word (e.g. "ai", "hacking", "devops"). Same value across all designs.
- "unsplash_query": Always set to empty string "".

Make each of the {style_count} designs visually DISTINCT (different color palette, different layout direction, different style_name).

User's video idea: {prompt}"""    

    last_error = None
    for model in MODELS_TO_TRY:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=sys_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    )
                )

                raw = response.text
                print(f"[Gemini] Raw response ({model}):\n{raw}\n")

                cleaned = _clean_json(raw)
                return json.loads(cleaned)

            except json.JSONDecodeError as e:
                print(f"[Gemini] JSON parse failed: {e}")
                print(f"[Gemini] Raw text was:\n{response.text}\n")
                break  # move to next model

            except Exception as e:
                last_error = e
                error_str = str(e)
                is_retryable = "429" in error_str or "503" in error_str or "UNAVAILABLE" in error_str

                if is_retryable:
                    if attempt < 2:
                        wait = 2 ** attempt * 5
                        print(f"[Gemini] {model} retryable error (attempt {attempt+1}), waiting {wait}s: {error_str[:80]}")
                        time.sleep(wait)
                        continue
                    else:
                        print(f"[Gemini] {model} failed after 3 attempts, trying next model.")
                        break

                raise

    print(f"[Gemini] All models exhausted. Last error: {last_error}")
    palettes = [
        {"bg": "#0f172a", "accent": "#00f2ff", "name": "Dark Tech",  "layout": "headshot_right"},
        {"bg": "#1e0a3c", "accent": "#ff3366", "name": "Neon Pop",   "layout": "headshot_left"},
        {"bg": "#0b1d2a", "accent": "#ffd60a", "name": "Sunset Code", "layout": "headshot_right"},
    ]
    title_fallback = (prompt or "TUTORIAL").upper().split()[:3]
    title_text = " ".join(title_fallback) or "TUTORIAL"
    subtitle_fallback = "BEGINNER TO ADVANCED"
    # cheap topic_slug guess from the prompt
    topic_guess = (prompt or "").strip().lower().split()[0] if prompt else ""
    designs = []
    for i in range(style_count):
        p = palettes[i % len(palettes)]
        designs.append({
            "title": title_text,
            "subtitle": subtitle_fallback,
            "prompt_used": f"{p['name']} variant",
            "fal_prompt": f"Cinematic YouTube thumbnail background for {prompt}",
            "unsplash_query": "",
            "topic_slug": topic_guess,
            "bg_color": p["bg"],
            "accent_color": p["accent"],
            "text_color": "#ffffff",
            "layout": p["layout"],
            "style_name": p["name"],
        })
    return designs