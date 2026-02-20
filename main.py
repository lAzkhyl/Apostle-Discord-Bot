# main.py
# ============================================================
# Entry point utama ApostleBot.
# Bertanggung jawab untuk:
#   1. Inisialisasi bot dan intents
#   2. Load semua modul dari folder /modules
#   3. Sync slash commands ke guild atau global
# ============================================================

import os
import asyncio
import platform
import discord
from discord.ext import commands

from config import config
from utils.logger import logger
from database.core import db_core


class ApostleBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(
            command_prefix="ap!",
            intents=intents,
            help_command=None,
            case_insensitive=True,
        )

    async def setup_hook(self):
        """
        Dipanggil oleh discord.py sebelum bot login.
        Urutan eksekusi:
            1. Setup database core
            2. Load semua extension (cog) dari /modules
            3. Sync slash commands
        """
        # ── 1. Setup Database ─────────────────────────────────
        await db_core.setup_core()
        logger.info("Database core initialized.")

        # ── 2. Load Modules ───────────────────────────────────
        modules_folder = "modules"
        if not os.path.exists(modules_folder):
            os.makedirs(modules_folder)
            logger.warning(f"Folder '{modules_folder}' tidak ditemukan, dibuat baru.")

        for folder_name in os.listdir(modules_folder):
            folder_path = os.path.join(modules_folder, folder_name)
            cog_path    = os.path.join(folder_path, "cog.py")

            # Hanya load folder yang memiliki file cog.py di dalamnya
            if not os.path.isdir(folder_path) or folder_name.startswith("_"):
                continue
            if not os.path.exists(cog_path):
                continue

            extension_name = f"{modules_folder}.{folder_name}.cog"
            try:
                await self.load_extension(extension_name)
                logger.info(f"✅ Module loaded: {extension_name}")
            except Exception as error:
                logger.error(f"❌ Failed to load {extension_name}: {error}")

        # ── 3. Sync Slash Commands ────────────────────────────
        if config.TEST_GUILD_ID:
            guild_object = discord.Object(id=config.TEST_GUILD_ID)
            self.tree.copy_global_to(guild=guild_object)
            await self.tree.sync(guild=guild_object)
            logger.info(f"Slash commands synced to Test Guild ID: {config.TEST_GUILD_ID}")
        else:
            await self.tree.sync()
            logger.info("Slash commands synced Globally (may take up to 1 hour).")

    async def on_ready(self):
        logger.info("=" * 50)
        logger.info(f"Bot Online  : {self.user} (ID: {self.user.id})")
        logger.info(f"Python      : {platform.python_version()}")
        logger.info(f"discord.py  : {discord.__version__}")
        logger.info(f"Guild Count : {len(self.guilds)}")
        logger.info("=" * 50)

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Two Moon Server",
            )
        )

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Global error handler untuk prefix commands (ap!)."""
        if isinstance(error, commands.CommandNotFound):
            return
        logger.error(f"Command error: {error}")


async def main():
    if not config.TOKEN:
        logger.critical("DISCORD_TOKEN tidak ditemukan di .env! Bot tidak bisa dijalankan.")
        return

    bot = ApostleBot()

    try:
        async with bot:
            await bot.start(config.TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot shutdown oleh user (KeyboardInterrupt).")
    except discord.LoginFailure:
        logger.critical("Token Discord tidak valid! Periksa kembali DISCORD_TOKEN di .env.")
    except Exception as error:
        logger.critical(f"Runtime error tidak terduga: {error}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
