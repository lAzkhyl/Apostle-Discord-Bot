import aiosqlite
import asyncio
from datetime import datetime, timedelta, timezone
from database.core import db_core

_generate_locks: dict[int, asyncio.Lock] = {}

def _get_user_lock(user_id: int) -> asyncio.Lock:
    if user_id not in _generate_locks:
        _generate_locks[user_id] = asyncio.Lock()
    return _generate_locks[user_id]


def _parse_timestamp(raw: str) -> datetime:
    if not raw:
        return datetime.now(tz=timezone.utc)
    try:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        pass

    try:
        clean = raw.split(".")[0].replace("T", " ")
        parsed = datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
        return parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        pass

    return datetime.now(tz=timezone.utc)


class VouchDatabase:

    async def setup(self):
        async with db_core.get_connection() as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS vouch_codes (
                    code        TEXT PRIMARY KEY,
                    guild_id    INTEGER NOT NULL,
                    role_id     INTEGER NOT NULL,
                    creator_id  INTEGER NOT NULL,
                    created_at  TIMESTAMP NOT NULL,
                    used_by     INTEGER,
                    status      TEXT NOT NULL DEFAULT 'ACTIVE',
                    rep_value   INTEGER NOT NULL DEFAULT 0
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS redeemed_users (
                    user_id         INTEGER PRIMARY KEY,
                    first_redeem_at TIMESTAMP NOT NULL
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id    INTEGER PRIMARY KEY,
                    reputation INTEGER NOT NULL DEFAULT 0,
                    voucher_id INTEGER
                )
            """)

            try:
                await db.execute(
                    "ALTER TABLE vouch_codes ADD COLUMN rep_value INTEGER NOT NULL DEFAULT 0"
                )
            except aiosqlite.OperationalError:
                pass

            await db.commit()

    async def create_vouch(
        self,
        code: str,
        guild_id: int,
        role_id: int,
        creator_id: int,
        rep_value: int = 0,
    ) -> None:
        async with db_core.get_connection() as db:
            await db.execute(
                """
                INSERT INTO vouch_codes
                    (code, guild_id, role_id, creator_id, created_at, status, rep_value)
                VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?)
                """,
                (code, guild_id, role_id, creator_id, datetime.now(tz=timezone.utc), rep_value),
            )
            await db.commit()

    async def can_generate(self, creator_id: int, cooldown_minutes: int) -> bool:
        if cooldown_minutes <= 0:
            return True

        async with _get_user_lock(creator_id):
            limit_time = datetime.now(tz=timezone.utc) - timedelta(minutes=cooldown_minutes)
            async with db_core.get_connection() as db:
                async with db.execute(
                    "SELECT COUNT(*) FROM vouch_codes WHERE creator_id = ? AND created_at >= ?",
                    (creator_id, limit_time),
                ) as cursor:
                    count = (await cursor.fetchone())[0]
                    return count == 0

    async def get_creator_vouches(self, creator_id: int) -> list:
        async with db_core.get_connection() as db:
            async with db.execute(
                """
                SELECT code, status, created_at, used_by, role_id
                FROM vouch_codes
                WHERE creator_id = ?
                ORDER BY created_at DESC
                LIMIT 25
                """,
                (creator_id,),
            ) as cursor:
                return await cursor.fetchall()

    async def execute_revoke(self, code: str) -> None:
        async with db_core.get_connection() as db:
            await db.execute(
                "UPDATE vouch_codes SET status = 'REVOKED' WHERE code = ?",
                (code,),
            )
            await db.commit()

    async def redeem_vouch(
        self, code: str, user_id: int
    ) -> tuple[bool, int | None, bool, str]:
        """
        Memproses redemption kode vouch.
        
        Returns:
            (success, role_id, is_first_time, message)
        """
        async with db_core.get_connection() as db:
            async with db.execute(
                "SELECT role_id, status, created_at, creator_id, rep_value FROM vouch_codes WHERE code = ?",
                (code,),
            ) as cursor:
                row = await cursor.fetchone()

            if not row:
                return False, None, False, "Kode tidak ditemukan."

            role_id, status, created_at_raw, creator_id, rep_value = row
            created_at = _parse_timestamp(created_at_raw)
            now_utc    = datetime.now(tz=timezone.utc)

            # Auto-expire jika sudah lewat 3 hari
            if status == "ACTIVE" and (now_utc - created_at) > timedelta(days=3):
                await db.execute(
                    "UPDATE vouch_codes SET status = 'EXPIRED' WHERE code = ?",
                    (code,),
                )
                await db.commit()
                return False, None, False, "Kode sudah kedaluwarsa (lebih dari 3 hari)."

            if status != "ACTIVE":
                return False, None, False, f"Kode sudah berstatus **{status.lower()}**."

            # Tandai kode sebagai USED
            await db.execute(
                "UPDATE vouch_codes SET status = 'USED', used_by = ? WHERE code = ?",
                (user_id, code),
            )

            # Cek apakah first-time redeem
            async with db.execute(
                "SELECT user_id FROM redeemed_users WHERE user_id = ?",
                (user_id,),
            ) as cursor:
                first_time_row = await cursor.fetchone()

            is_first_time = first_time_row is None
            if is_first_time:
                await db.execute(
                    "INSERT INTO redeemed_users (user_id, first_redeem_at) VALUES (?, ?)",
                    (user_id, now_utc),
                )

            # Update atau insert profil user
            async with db.execute(
                "SELECT reputation FROM user_profiles WHERE user_id = ?",
                (user_id,),
            ) as cursor:
                profile_row = await cursor.fetchone()

            if profile_row:
                await db.execute(
                    "UPDATE user_profiles SET reputation = reputation + ?, voucher_id = ? WHERE user_id = ?",
                    (rep_value, creator_id, user_id),
                )
            else:
                await db.execute(
                    "INSERT INTO user_profiles (user_id, reputation, voucher_id) VALUES (?, ?, ?)",
                    (user_id, rep_value, creator_id),
                )

            await db.commit()
            return True, role_id, is_first_time, "Berhasil."

    async def update_voucher_manual(self, target_user_id: int, new_voucher_id: int) -> None:
        async with db_core.get_connection() as db:
            async with db.execute(
                "SELECT user_id FROM user_profiles WHERE user_id = ?",
                (target_user_id,),
            ) as cursor:
                exists = await cursor.fetchone()

            if exists:
                await db.execute(
                    "UPDATE user_profiles SET voucher_id = ? WHERE user_id = ?",
                    (new_voucher_id, target_user_id),
                )
            else:
                await db.execute(
                    "INSERT INTO user_profiles (user_id, voucher_id) VALUES (?, ?)",
                    (target_user_id, new_voucher_id),
                )
            await db.commit()

    async def get_user_profile(self, user_id: int) -> tuple | None:
        async with db_core.get_connection() as db:
            async with db.execute(
                "SELECT reputation, voucher_id FROM user_profiles WHERE user_id = ?",
                (user_id,),
            ) as cursor:
                return await cursor.fetchone()


vouch_db = VouchDatabase()
