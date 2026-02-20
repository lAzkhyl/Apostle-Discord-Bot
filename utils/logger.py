# utils/logger.py
# ============================================================
# Logger terpusat untuk seluruh bot.
# Output ke console DAN file apostle.log secara bersamaan.
# ============================================================

import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logger(name: str = "ApostleBot") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Hindari duplikasi handler jika setup dipanggil lebih dari sekali
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── File Handler (dengan rotasi otomatis) ────────────────
    # Max 5MB per file, simpan 3 file backup
    file_handler = RotatingFileHandler(
        filename="apostle.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # ── Console Handler ───────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()
