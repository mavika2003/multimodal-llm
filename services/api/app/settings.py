from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    airlock_local_token: str = "dev-local-token"
    airlock_db_path: str = "./data/airlock.db"
    airlock_allowed_origins: str = (
        "http://127.0.0.1:5173,http://127.0.0.1:5174,chrome-extension://"
    )
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_vlm_model: str = ""
    ollama_coder_model: str = "qwen2.5-coder:3b"
    max_text_bytes: int = 512_000
    max_media_bytes: int = 25_000_000
    scan_timeout_seconds: float = 120.0

    @property
    def db_path(self) -> Path:
        p = Path(self.airlock_db_path)
        if not p.is_absolute():
            root = Path(__file__).resolve().parents[3]
            p = root / p
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def allowed_origin_prefixes(self) -> list[str]:
        return [o.strip() for o in self.airlock_allowed_origins.split(",") if o.strip()]


settings = Settings()