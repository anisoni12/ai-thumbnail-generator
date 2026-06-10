import os
import requests

def remove_background(image_bytes: bytes) -> bytes | None:
    api_key = os.getenv("REMOVE_BG_API_KEY")
    if not api_key:
        print("[bg_removal] REMOVE_BG_API_KEY not set, skipping")
        return None
    try:
        print("[bg_removal] calling remove.bg API...")
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": ("image.png", image_bytes)},
            data={"size": "auto"},
            headers={"X-Api-Key": api_key},
        )
        if response.status_code == 200:
            print(f"[bg_removal] success, output size: {len(response.content)} bytes")
            return response.content
        else:
            print(f"[bg_removal] API error: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"[bg_removal] failed: {e}")
        return None