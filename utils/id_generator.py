# utils/id_generator.py
# ============================================================
# Generator untuk kode vouch yang aman secara kriptografis.
# Menggunakan secrets module (bukan random) untuk keamanan.
# ============================================================

import secrets
import string


class IDGenerator:
    """
    Menghasilkan kode unik berformat: PREFIX-XXXX-XXXX-XXXX
    
    Contoh output: V-A3KD-92XZ-BT7P
    
    - Menggunakan secrets.choice() → aman secara kriptografis
    - Huruf kapital + angka → mudah dibaca, tidak ambigu
    - Dikelompokkan per 4 karakter → mudah diketik manual
    """

    ALPHABET = string.ascii_uppercase + string.digits

    @staticmethod
    def generate(prefix: str = "V", length: int = 12, group_size: int = 4) -> str:
        """
        Args:
            prefix     : Huruf awalan kode (default: "V" untuk Vouch)
            length     : Total panjang karakter acak (default: 12)
            group_size : Ukuran tiap kelompok karakter (default: 4)
        
        Returns:
            String kode berformat "PREFIX-XXXX-XXXX-XXXX"
        """
        raw_token = "".join(
            secrets.choice(IDGenerator.ALPHABET) for _ in range(length)
        )

        groups = [
            raw_token[i : i + group_size]
            for i in range(0, length, group_size)
        ]

        return f"{prefix}-" + "-".join(groups)
