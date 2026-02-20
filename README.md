# ApostleBot — Two Moon Clan Discord Bot

Bot Discord untuk sistem Vouch & Profile server Two Moon Clan.

---

## 📁 Struktur Proyek

```
apostlebot/
├── main.py                          # Entry point bot
├── config.py                        # Konfigurasi terpusat (.env reader)
├── requirements.txt
├── .env.example                     # Template environment variables
├── .gitignore
│
├── database/
│   ├── __init__.py
│   └── core.py                      # Koneksi & setup database SQLite
│
├── utils/
│   ├── __init__.py
│   ├── logger.py                    # Logger terpusat (console + file)
│   └── id_generator.py              # Generator kode vouch kriptografis
│
└── modules/
    ├── __init__.py
    │
    ├── profile/                     # Modul Profile
    │   ├── __init__.py
    │   ├── cog.py                   # Command: /profile
    │   ├── service.py               # ⭐ Single Source of Truth profile embed
    │   └── views.py                 # ProfileView, ProfileConfirmPostView
    │
    └── vouch/                       # Modul Vouch
        ├── __init__.py
        ├── cog.py                   # Commands: /vouch, /vouch_bulk, dll
        ├── db.py                    # Data Access Layer vouch
        └── views/
            ├── __init__.py          # Public API views
            ├── helpers.py           # send_log, build_error_embed
            ├── modals.py            # RedeemModal, ChangeNickModal
            ├── first_time_view.py   # FirstTimeRedeemView
            ├── manage_view.py       # ManageVouchView, ConfirmRevokeView
            └── vouch_view.py        # VouchView, SetupView
```

---

## ⚙️ Setup & Instalasi

### 1. Clone & Install Dependencies
```bash
git clone <repo-url>
cd apostlebot
pip install -r requirements.txt
```

### 2. Konfigurasi Environment
```bash
cp .env.example .env
```
Buka `.env` dan isi semua nilai yang diperlukan:

| Variable | Keterangan |
|---|---|
| `DISCORD_TOKEN` | Token bot dari Discord Developer Portal |
| `GUILD_ID` | ID server untuk dev (kosongkan untuk production) |
| `ROLE_OWNER_IDS` | ID role Owner (pisah koma jika lebih dari 1) |
| `ROLE_MOD_IDS` | ID role Moderator |
| `ROLE_ALLSTARS_IDS` | ID role All Stars |
| `ROLE_KAISER_IDS` | ID role Kaiser |
| `ROLE_WARLORD_IDS` | ID role Warlord |
| `ROLE_MEMBER_IDS` | ID role Member |
| `ROLE_FRIENDS_IDS` | ID role Friends |
| `ROLE_VISITORS_IDS` | ID role Visitors |
| `ROLE_IGNORED_IDS` | Role yang disembunyikan dari tampilan profile |
| `VOUCH_LOG_CHANNEL_ID` | ID channel untuk log vouch activity |

### 3. Jalankan Bot
```bash
python main.py
```

---

## 🎯 Slash Commands

| Command | Akses | Deskripsi |
|---|---|---|
| `/vouch` | Semua member | Buka menu sistem vouch |
| `/profile [member]` | Semua member | Lihat profile server |
| `/vouch_bulk` | Owner / Admin | Generate banyak kode sekaligus |
| `/update_vouch` | Owner / Admin | Ubah data voucher seseorang |
| `/setup` | Admin | Spawn panel verifikasi statis |

---

## 🏗️ Hierarki Tier & Vouch Config

| Tier | Cooldown Generate | Rep per Vouch |
|---|---|---|
| Owner | Tidak ada | +50 |
| Mod | Tidak ada | +20 |
| All Stars | 10 menit | +10 |
| Kaiser | 60 menit | +5 |
| Warlord | 60 menit | +5 |
| Member / Friends / Visitors | — | (tidak bisa generate) |

---

## 🔐 Arsitektur Keamanan

- **Single Source of Truth**: Semua profile embed dibangun oleh `ProfileService` — tidak ada duplikasi logika
- **Persistent Views**: `SetupView` dan `FirstTimeRedeemView` tetap aktif setelah bot restart
- **Race Condition Guard**: `asyncio.Lock` per user mencegah double-generate kode
- **Extended Info Privacy**: Data sensitif (User ID, tanggal akun) hanya terlihat oleh pemilik profil via ephemeral message
- **Robust Timestamp Parsing**: `_parse_timestamp()` menangani semua format SQLite di berbagai OS
