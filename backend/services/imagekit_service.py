from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
from config import settings
import base64

imagekit = ImageKit(
    public_key=settings.IMAGEKIT_PUBLIC_KEY,
    private_key=settings.IMAGEKIT_PRIVATE_KEY,
    url_endpoint=settings.IMAGEKIT_URL_ENDPOINT
)

def upload_headshot(file_content: bytes, filename: str) -> str:
    encoded_file = base64.b64encode(file_content).decode('utf-8')
    
    response = imagekit.upload_file(              # ← upload_file(), not upload()
        file=encoded_file,
        file_name=filename,
        options=UploadFileRequestOptions(         # ← must be this object, not a dict
            folder="/thumbnails",
            is_private_file=False,
        )
    )

    if response.error:
        raise Exception(f"ImageKit Upload Error: {response.error.message}")

    return response.response_metadata.raw['url']


def build_thumbnail_url(headshot_url: str, prompt: str) -> str:
    """
    Returns a resized 1280x720 version of the headshot URL via ImageKit transformations.
    """
    return f"{headshot_url}?tr=w-1280,h-720,c-at_max"