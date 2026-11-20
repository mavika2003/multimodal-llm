from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    airlock_local_token: str = "dev-local-token"
    airlock_db_path: str = "./data/airlock.db"
    airlock_allowed_origins: str = (
        "http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175,http://127.0.0.1:5176,chrome-extension://"
    )
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_vlm_model: str = "qwen3.5:9b"
    ollama_text_model: str = "qwen3.5:9b"
    ollama_coder_model: str = "qwen2.5-coder:3b"
    ollama_max_concurrent_requests: int = 1
    whisper_model_size: str = "base"
    whisper_download_root: str = "./data/models/whisper"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    pdf_max_pages: int = 30
    pdf_vlm_max_pages: int = 3
    video_max_duration_sec: int = 120
    video_max_vlm_frames: int = 6
    video_frame_interval_sec: float = 2.0
    video_scan_wall_deadline_sec: float = 420.0
    video_firewall_max_duration_sec: int = 90
    video_firewall_max_vlm_frames: int = 2
    video_firewall_max_ocr_frames: int = 15
    video_firewall_max_audio_sec: int = 45
    video_firewall_vlm_timeout_sec: float = 90.0
    max_text_bytes: int = 512_000
    max_media_bytes: int = 25_000_000
    scan_timeout_seconds: float = 180.0

    @property
    def db_path(self) -> Path:
        p = Path(self.airlock_db_path)
        if not p.is_absolute():
            root = Path(__file__).resolve().parents[3]
            p = root / p
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def whisper_cache_dir(self) -> Path:
        p = Path(self.whisper_download_root)
        if not p.is_absolute():
            p = self.repo_root / p
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def policy_path(self) -> Path:
        return self.repo_root / "config" / "confidentiality_policy.yaml"

    def allowed_origin_prefixes(self) -> list[str]:
        return [o.strip() for o in self.airlock_allowed_origins.split(",") if o.strip()]


settings = Settings()