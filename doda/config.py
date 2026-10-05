"""DODA konfiguratsiyasi — yagona, tiplangan, production-ready (env + .env + kelajak cloud).

Manba tartibi (yuqori ustun oldin): ``init > muhit-o'zgaruvchi (DODA_...) > .env fayl > default``.
Ichma-ich bo'limlar ``__`` bilan: masalan ``DODA_LLM__PROVIDER=gemini``.

**Sirlar bu yerda EMAS** — ular ``SecretStore`` orqali (``docs/SECURITY.md``). Config faqat
sir bo'lmagan sozlamalar (provider nomi, yo'llar, bayroqlar).

Kelajakda yangi manba (masalan bulut config) ``BaseSettings`` ning ``settings_customise_sources``
orqali qo'shiladi — mavjud kod o'zgarmaydi.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_NAME = "DODA"


def default_data_dir() -> Path:
    """OS-standart ilova-ma'lumot papkasi (yagona sxema, per-OS yo'l).

    - macOS: ``~/Library/Application Support/DODA``
    - Windows: ``%APPDATA%/DODA``
    - Linux/boshqa: ``$XDG_DATA_HOME/DODA`` yoki ``~/.local/share/DODA``
    """
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        return (Path(base) if base else Path.home()) / APP_NAME
    xdg = os.environ.get("XDG_DATA_HOME")
    return (Path(xdg) if xdg else Path.home() / ".local" / "share") / APP_NAME


class LLMSettings(BaseModel):
    """AI provayder sozlamalari (sir EMAS — kalit SecretStore'da)."""

    provider: str = "claude"
    model: str = "claude-haiku-4-5"
    max_tokens: int = 1024


class VisionSettings(BaseModel):
    """Ko'rish (kamera) sozlamalari."""

    provider: str = "screen"  # screen / mac_camera (usb/rtsp/ip — v2.0)


class VoiceSettings(BaseModel):
    """Ovoz (STT/TTS/VAD/wake) sozlamalari — o'zbekcha ovoz ustuvor.

    API kalitlari BU YERDA EMAS — ``SecretStore`` da (``speech.stt.key`` / ``speech.tts.key``).
    Provayderlar config orqali almashtiriladi (registry), kod o'zgarmaydi.
    """

    language: str = "uz"
    tts_voice: str = "uz-UZ-SardorNeural"  # edge-tts uchun; elevenlabs uchun voice_id
    voice_id: str = ""  # provayderga xos ovoz identifikatori (masalan ElevenLabs)
    wake_word: str = "doda"
    record_seconds: float = 5.0
    sample_rate: int = 16000

    stt_provider: str = "whisper"  # whisper / elevenlabs / mock
    tts_provider: str = "edge_tts"  # edge_tts / elevenlabs / mock
    vad_provider: str = "energy"  # energy (dep-siz) / silero / mock
    audio_provider: str = "auto"  # auto (OS aniqlaydi) / macos / linux / windows / mock

    enable_voice: bool = True
    enable_vad: bool = True
    streaming_enabled: bool = True
    wake_word_enabled: bool = False
    mock_mode: bool = False  # True → barcha ovoz provayderlari soxta (kalitsiz test)


class PathsSettings(BaseModel):
    """Fayl yo'llari (per-OS)."""

    data_dir: Path = Field(default_factory=default_data_dir)


class Settings(BaseSettings):
    """DODA'ning yagona konfiguratsiyasi."""

    model_config = SettingsConfigDict(
        env_prefix="DODA_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "dev"
    """Ishlash muhiti: ``dev`` / ``prod``."""

    log_level: str = "info"
    """Global log darajasi: debug/info/warning/error."""

    llm: LLMSettings = Field(default_factory=LLMSettings)
    vision: VisionSettings = Field(default_factory=VisionSettings)
    voice: VoiceSettings = Field(default_factory=VoiceSettings)
    paths: PathsSettings = Field(default_factory=PathsSettings)

    features: dict[str, bool] = Field(default_factory=dict)
    """Imkoniyat bayroqlari (FeatureFlags shundan o'qiydi)."""
