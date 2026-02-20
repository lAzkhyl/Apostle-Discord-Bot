# config.py
# ============================================================
# Konfigurasi terpusat untuk seluruh bot.
# Semua variabel environment dibaca DI SINI SAJA.
# Modul lain tidak boleh membaca os.getenv() secara langsung.
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()


def _parse_ids(env_key: str) -> list[int]:
    """
    Membaca variabel environment berisi daftar ID (comma-separated)
    dan mengkonversinya menjadi list of int.
    
    Contoh .env:
        ROLE_OWNER_IDS=123456789,987654321
    """
    raw = os.getenv(env_key, "")
    if not raw:
        return []
    return [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]


def _parse_int(env_key: str, default: int = 0) -> int:
    raw = os.getenv(env_key, str(default))
    return int(raw) if raw.isdigit() else default


class Config:
    # ── Token & Guild ────────────────────────────────────────
    TOKEN = os.getenv("DISCORD_TOKEN")

    raw_guild = os.getenv("GUILD_ID", "")
    TEST_GUILD_ID = int(raw_guild) if raw_guild.isdigit() else None

    # ── Staff Roles ──────────────────────────────────────────
    # FIX: Key sebelumnya tidak konsisten antara config.py dan .env
    # Standardisasi menggunakan format ROLE_X_IDS (plural)
    OWNER_ROLES    = _parse_ids("ROLE_OWNER_IDS")
    MOD_ROLES      = _parse_ids("ROLE_MOD_IDS")
    ALLSTARS_ROLES = _parse_ids("ROLE_ALLSTARS_IDS")
    KAISER_ROLES   = _parse_ids("ROLE_KAISER_IDS")
    WARLORD_ROLES  = _parse_ids("ROLE_WARLORD_IDS")

    # ── Member Roles ──────────────────────────────────────────
    MEMBER_ROLES   = _parse_ids("ROLE_MEMBER_IDS")
    FRIENDS_ROLES  = _parse_ids("ROLE_FRIENDS_IDS")
    VISITORS_ROLES = _parse_ids("ROLE_VISITORS_IDS")

    # ── Utility Roles ─────────────────────────────────────────
    IGNORED_ROLES  = _parse_ids("ROLE_IGNORED_IDS")

    # ── Channels ──────────────────────────────────────────────
    VOUCH_LOG_CHANNEL_ID = _parse_int("VOUCH_LOG_CHANNEL_ID", 0)


config = Config()
