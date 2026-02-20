import os
import aiosqlite


class DatabaseCore:
    def __init__(self, db_path: str = "database/bot_data.sqlite"):
        self.db_path = db_path
        self._ensure_folder_exists()

    def _ensure_folder_exists(self):
        folder = os.path.dirname(self.db_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)

    def get_connection(self):
        return aiosqlite.connect(self.db_path)

    async def setup_core(self):
        async with self.get_connection() as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute("PRAGMA journal_mode = WAL;")
            await db.commit()


db_core = DatabaseCore()
