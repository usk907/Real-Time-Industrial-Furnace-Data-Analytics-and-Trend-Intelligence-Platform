# IEIP — Telemetry Generator (`branch/generator`)

Generates **60 industrial SCADA tags at 1 Hz** and writes them directly to MySQL.  
This is the **only writer** to the database — `furnace_readings` and `furnace_latest`.

```
branch/generator
├── generator/
│   ├── generator.py        ← Main loop (60 tags × 1 Hz)
│   ├── tags.py             ← Tag dictionary
│   ├── requirements.txt
│   ├── .env.example        ← Copy → .env, fill in DB credentials
│   └── tests/
├── db/
│   ├── schema.sql          ← Creates all 4 tables
│   └── create_users.sql    ← Creates generator_user + server_user
└── scripts/
    ├── init_database.bat   ← Run ONCE first to set up DB + users
    ├── start_generator.bat
    └── stop_all.bat
```

---

## Prerequisites

- Python 3.10+
- MySQL 8.x accessible from this machine

---

## Step 1 — Initialize Database *(first time only)*

```cmd
scripts\init_database.bat
```

Prompts for your MySQL root password, then:
- Creates the `furnace_db` database
- Creates `furnace_readings`, `furnace_latest`, `users`, `alarms` tables
- Creates `generator_user` (write) and `server_user` (read) accounts

---

## Step 2 — Configure

```cmd
copy generator\.env.example generator\.env
notepad generator\.env
```

| Variable | Description | Example |
|---|---|---|
| `DB_HOST` | MySQL host | `127.0.0.1` |
| `DB_PORT` | MySQL port | `3307` |
| `DB_USER` | Write user | `generator_user` |
| `DB_PASSWORD` | Password | `yourpassword` |
| `DB_NAME` | Database name | `furnace_db` |
| `GEN_INTERVAL_SECONDS` | Tick rate | `1.0` |
| `LOG_INTERVAL_TICKS` | Log every N ticks | `10` |

---

## Step 3 — Install Python Dependencies

```cmd
cd generator
pip install -r requirements.txt
```

---

## Step 4 — Run

```cmd
scripts\start_generator.bat
```

The generator prints a status line every 10 seconds showing all 60 tag values.  
Press **Ctrl+C** or run `scripts\stop_all.bat` to stop.
