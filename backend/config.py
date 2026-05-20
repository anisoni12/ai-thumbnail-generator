from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    IMAGEKIT_PUBLIC_KEY: str
    IMAGEKIT_PRIVATE_KEY: str
    IMAGEKIT_URL_ENDPOINT: str
    GEMINI_API_KEY: str
    UNSPLASH_ACCESS_KEY: str = ""
    HF_TOKEN: str = ""

    class Config:
        env_file = ".env"

settings = Settings()