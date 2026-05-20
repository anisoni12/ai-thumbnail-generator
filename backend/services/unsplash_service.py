import requests
from config import settings
import random

FALLBACK_COLORS = [
    "#1a1a2e", "#0f3460", "#16213e",
    "#1b1b2f", "#2c003e", "#162447",
]

def get_background_image(query: str, width: int = 1280, height: int = 720) -> bytes | None:
    """
    Fetches a background image from Unsplash for the given query.
    Returns image bytes or None if the request fails.
    """
    try:
        headers = {"Authorization": f"Client-ID {settings.UNSPLASH_ACCESS_KEY}"}

        response = requests.get(
            "https://api.unsplash.com/photos/random",
            headers=headers,
            params={
                "query": query,
                "orientation": "landscape",
                "content_filter": "high",
            },
            timeout=10
        )

        if response.status_code != 200:
            print(f"Unsplash API error: {response.status_code} — {response.text}")
            return None

        photo_data = response.json()
        image_url = photo_data["urls"]["regular"]

        image_response = requests.get(image_url, timeout=15)
        if image_response.status_code == 200:
            return image_response.content

        return None

    except Exception as e:
        print(f"Unsplash fetch failed: {e}")
        return None