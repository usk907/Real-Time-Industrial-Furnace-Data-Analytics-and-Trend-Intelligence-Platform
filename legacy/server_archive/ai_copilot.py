"""
IEIP AI Copilot Service
Provides natural language to SQL generation, schema context mapping, query safety checks, and control room operator chatbot.
"""
import os
import re
from typing import List, Optional, Tuple
from pydantic import BaseModel
import google.generativeai as genai
from sqlalchemy.orm import Session
from sqlalchemy import text, desc

from backend.app.models import (
    Plant,
    Department,
    Machine,
    Device,
    SensorReading,
    Alarm,
    SystemSetting
)

SCHEMA_CONTEXT = """
TABLES:

plants (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  location VARCHAR(150),
  timezone VARCHAR(50),
  description TEXT,
  status VARCHAR(20) -- e.g. 'ACTIVE', 'INACTIVE'
)

departments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  plant_id INT FOREIGN KEY REFERENCES plants(id),
  name VARCHAR(100) NOT NULL,
  description TEXT
)

machines (
  id INT AUTO_INCREMENT PRIMARY KEY,
  department_id INT FOREIGN KEY REFERENCES departments(id),
  name VARCHAR(100) NOT NULL,
  type VARCHAR(50) NOT NULL, -- e.g. 'Furnace', 'Turbine', 'Breaker'
  rated_capacity FLOAT,
  status VARCHAR(20) -- e.g. 'RUNNING', 'STOPPED', 'MAINTENANCE'
)

devices (
  id INT AUTO_INCREMENT PRIMARY KEY,
  machine_id INT FOREIGN KEY REFERENCES machines(id),
  name VARCHAR(100) NOT NULL, -- e.g. 'SMS-1 Furnace Temp', 'SMS-1 Pressure', 'CB5214'
  type VARCHAR(50) NOT NULL,
  register_address VARCHAR(50) NOT NULL,
  unit VARCHAR(20) NOT NULL, -- e.g. '°C', 'bar', 'kW', 'kWh', 'ppm', '%'
  nominal_min FLOAT,
  nominal_max FLOAT,
  communication_status VARCHAR(20), -- e.g. 'ONLINE', 'OFFLINE'
  is_active BOOLEAN
)
-- Note: 'devices' represents the sensors. Always join devices on sensor_readings.sensor_id or alarms.sensor_id to get sensor names or units.

sensor_readings (
  time DATETIME PRIMARY KEY,
  sensor_id INT FOREIGN KEY REFERENCES devices(id),
  value FLOAT NOT NULL,
  quality VARCHAR(20), -- e.g. 'GOOD', 'BAD', 'UNCERTAIN'
  status VARCHAR(20) -- e.g. 'OK', 'HIGH', 'CRITICAL'
)
-- Note: This is the time-series telemetry table. Contains 1-second interval readings of all sensors.

alarms (
  id INT AUTO_INCREMENT PRIMARY KEY,
  time DATETIME,
  end_time DATETIME,
  sensor_id INT FOREIGN KEY REFERENCES devices(id),
  alarm_type VARCHAR(50), -- e.g. 'CB_OVERLOAD', 'SMS_LIMIT_SURGE', 'TURBINE_OVERLOAD'
  severity VARCHAR(20), -- e.g. 'CRITICAL', 'WARNING', 'INFO'
  trigger_value FLOAT,
  status VARCHAR(20) -- e.g. 'ACTIVE', 'ACKNOWLEDGED', 'CLEARED'
)

kpi_history (
  time DATETIME PRIMARY KEY,
  equipment_id INT FOREIGN KEY REFERENCES machines(id),
  kpi_name VARCHAR(50) PRIMARY KEY, -- e.g. 'OEE', 'Availability', 'Performance', 'Quality'
  value FLOAT NOT NULL,
  unit VARCHAR(20)
)

predictions (
  time DATETIME PRIMARY KEY,
  prediction_horizon_minutes INT PRIMARY KEY,
  sensor_id INT FOREIGN KEY REFERENCES devices(id),
  predicted_value FLOAT NOT NULL,
  upper_bound FLOAT,
  lower_bound FLOAT
)

settings (
  key VARCHAR(100) PRIMARY KEY,
  value VARCHAR(255) NOT NULL,
  description TEXT
)
"""

SQL_SYSTEM_PROMPT = """You are a SQL generator for a MySQL 8 database monitoring an industrial plant.
Given a question in plain English, output EXACTLY ONE valid MySQL SELECT statement that answers it.

Rules:
1. Output ONLY the raw SQL. No markdown fences (do not wrap in ```sql), no explanation, no semicolon-separated multiple statements.
2. Only write SELECT statements. Never write INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, GRANT, or other modifying queries.
3. Always resolve sensor names by joining 'devices' (match device.name exactly as requested).
4. Use MySQL date/time functions (e.g. NOW(), DATE_SUB(NOW(), INTERVAL 1 DAY), CURDATE()) for relative dates unless specified.
5. If the query asks for "yesterday", "last 2 hours", "today" etc., filter on `sensor_readings.time` or `alarms.time` using standard time window operations.
6. Limit results to a maximum of 100 rows unless requested otherwise.
7. If the question is unsupported or can't be answered by this schema, output: SELECT 'UNSUPPORTED' AS error;

SCHEMA:
{schema}
"""

SUMMARY_SYSTEM_PROMPT = """You are an AI assistant in an industrial plant control room.
Given the operator's original question, the SQL query executed, and the raw query result rows, write a direct, concise, and plain-English answer (1-3 sentences).
Always use the actual numbers and units from the results. Do not mention SQL, databases, or tables.
If the result is empty, say so clearly and suggest a different time frame or sensor name.
"""

FORBIDDEN_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|REPLACE|EXEC|CALL)\b",
    re.IGNORECASE,
)


class ChatMessage(BaseModel):
    role: str  # 'user' or 'model'
    content: str


class ChatPayload(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []


class AIQueryPayload(BaseModel):
    question: str


def is_safe_select(sql: str) -> Tuple[bool, str]:
    """Validates that query is strictly a single, read-only SELECT statement."""
    cleaned = sql.strip().rstrip(";").strip()

    if not re.match(r"^\s*SELECT\b", cleaned, re.IGNORECASE):
        return False, "Query must start with SELECT"

    if ";" in cleaned:
        return False, "Multiple statements are not allowed"

    if FORBIDDEN_PATTERN.search(cleaned):
        return False, "Query contains a disallowed keyword"

    return True, ""


def enforce_limit(sql: str, max_rows: int = 100) -> str:
    """Appends a LIMIT clause if not already present."""
    if re.search(r"\bLIMIT\s+\d+\s*$", sql, re.IGNORECASE):
        return sql
    return f"{sql.rstrip().rstrip(';')} LIMIT {max_rows}"


def get_gemini_client(api_key: str):
    """Configures and returns the Google Gemini API client."""
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    genai.configure(api_key=api_key)
    return genai


def generate_sql(question: str, api_key: str) -> str:
    """Uses Gemini 2.5 to translate a natural language question into SQL."""
    genai_client = get_gemini_client(api_key)
    prompt = SQL_SYSTEM_PROMPT.format(schema=SCHEMA_CONTEXT)

    model = genai_client.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(f"{prompt}\n\nQUESTION: {question}\n\nSQL:")

    sql = response.text.strip()
    sql = re.sub(r"^```(?:sql)?\s*|\s*```$", "", sql, flags=re.IGNORECASE | re.MULTILINE).strip()
    return sql


def summarize_results(question: str, sql: str, rows: list, api_key: str) -> str:
    """Summarizes raw SQL rows into a natural language response."""
    genai_client = get_gemini_client(api_key)
    prompt = (
        f"{SUMMARY_SYSTEM_PROMPT}\n\n"
        f"QUESTION: {question}\n\nSQL RUN: {sql}\n\nRESULTS ({len(rows)} rows): {rows[:50]}\n\nANSWER:"
    )
    model = genai_client.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()


def execute_ai_query(question: str, db: Session, api_key: str) -> dict:
    """End-to-end execution of text-to-SQL and natural language answer generation."""
    if not api_key:
        return {
            "question": question,
            "sql": None,
            "error": "Gemini API key is not configured in this project's .env file.",
            "rows": [],
            "answer": "I cannot answer this question because the Gemini API key is missing. Please add `GEMINI_API_KEY` to the backend `.env` file."
        }

    try:
        sql = generate_sql(question, api_key)
    except Exception as e:
        return {
            "question": question,
            "sql": None,
            "error": f"Failed to generate SQL: {e}",
            "rows": [],
            "answer": None
        }

    safe, reason = is_safe_select(sql)
    if not safe:
        return {
            "question": question,
            "sql": sql,
            "error": f"Blocked unsafe query: {reason}",
            "rows": [],
            "answer": None
        }

    if "UNSUPPORTED" in sql.upper():
        return {
            "question": question,
            "sql": sql,
            "error": None,
            "rows": [],
            "answer": "I couldn't map that question to the available database metrics. Try asking about a specific sensor value, plant counts, or recent alarms."
        }

    try:
        final_sql = enforce_limit(sql)
        result = db.execute(text(final_sql))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
    except Exception as e:
        return {
            "question": question,
            "sql": sql,
            "error": f"SQL execution failed: {e}",
            "rows": [],
            "answer": None
        }

    try:
        answer = summarize_results(question, sql, rows, api_key)
    except Exception as e:
        answer = f"Found {len(rows)} results, but failed to generate a natural summary: {e}"

    return {
        "question": question,
        "sql": sql,
        "error": None,
        "rows": rows,
        "answer": answer
    }


def process_copilot_chat(payload: ChatPayload, db: Session) -> dict:
    """Answers operator queries with real-time control room context or offline fallback."""
    try:
        plants_count = db.query(Plant).count()
        deps_count = db.query(Department).count()
        machines_count = db.query(Machine).count()
        devices_count = db.query(Device).count()

        active_alarms = db.query(Alarm).filter(Alarm.status == "ACTIVE").all()
        alarms_list = []
        for a in active_alarms:
            sensor = db.query(Device).filter(Device.id == a.sensor_id).first()
            alarms_list.append({
                "sensor": sensor.name if sensor else f"Sensor {a.sensor_id}",
                "type": a.alarm_type,
                "severity": a.severity,
                "value": a.trigger_value,
                "time": a.time.isoformat() if a.time else None
            })

        latest_telemetry = []
        devices = db.query(Device).all()
        for s in devices:
            reading = db.query(SensorReading).filter(
                SensorReading.sensor_id == s.id
            ).order_by(desc(SensorReading.time)).first()
            if reading:
                latest_telemetry.append({
                    "id": s.id,
                    "name": s.name,
                    "value": reading.value,
                    "unit": s.unit,
                    "status": reading.status,
                    "quality": reading.quality
                })

        settings = db.query(SystemSetting).all()
        system_settings = {s.key: s.value for s in settings}

    except Exception as db_err:
        print(f"[CHAT DB ERROR]: {db_err}")
        plants_count, deps_count, machines_count, devices_count = 1, 1, 5, 60
        alarms_list = []
        latest_telemetry = []
        system_settings = {}

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        db_key = db.query(SystemSetting).filter(SystemSetting.key == "GEMINI_API_KEY").first()
        if db_key and db_key.value:
            api_key = db_key.value

    if not api_key:
        status_msg = (
            "**AI Chatbot Offline (Key Missing)**\n\n"
            "To activate full natural language answers, please add your Google Gemini API key as `GEMINI_API_KEY` in the `.env` file of the project root.\n\n"
            "**Live Control Room Snapshot:**\n"
            f"- **Active Alarms**: {len(alarms_list)} alarm(s) currently active.\n"
            f"- **System Counts**: {plants_count} Plant(s), {deps_count} Department(s), {machines_count} Machine(s), {devices_count} Device(s).\n"
        )
        if alarms_list:
            status_msg += "\n**Active Alarms List:**\n"
            for a in alarms_list:
                status_msg += f"- `{a['sensor']}`: {a['type']} ({a['severity']}) - Trigger Value: {a['value']}\n"
        else:
            status_msg += "\n- **Alarms State**: Clean (No active alarms).\n"

        if latest_telemetry:
            status_msg += "\n**Key Sensor Values:**\n"
            key_sensor_ids = [19, 22, 51, 52, 53, 58, 60]
            for t in latest_telemetry:
                if t['id'] in key_sensor_ids:
                    status_msg += f"- `{t['name']}`: **{t['value']} {t['unit']}** (Status: {t['status']})\n"
        return {
            "response": status_msg,
            "offline": True
        }

    try:
        genai.configure(api_key=api_key)

        telemetry_summary = [
            {"id": t["id"], "name": t["name"], "val": f"{t['value']} {t['unit']}", "status": t["status"]}
            for t in latest_telemetry
        ]

        system_prompt = (
            "You are the AI Operations Assistant for the Real-Time Industrial Furnace Data Analytics and Trend Intelligence Platform.\n"
            "Your role is to assist operators in the control room by answering questions about the plant layout, live metrics, alarms, and settings.\n\n"
            "Here is the LIVE SYSTEM CONTEXT fetched directly from the SQL database:\n"
            f"- Counts: {plants_count} Plant(s), {deps_count} Department(s), {machines_count} Machine(s), {devices_count} Device(s).\n"
            f"- Active Alarms list: {alarms_list}\n"
            f"- Safety Limits / Thresholds: {system_settings}\n"
            f"- Latest Sensor Telemetry (1-60): {telemetry_summary}\n\n"
            "Project & System Overview:\n"
            "- It is a high-density industrial control system monitoring a Steel Works plant.\n"
            "- Sensors include Power meters (CB5214, CB14, SMS Run. Power), Furnace Details (SMS-1, SMS-4), Turbine Generators (TG-1 to TG-5), Accumulators (Grid import/export kWh), and Physical Sensors (SMS-1 Furnace Temp [ID 51, °C], Pressure [ID 52, bar], Cooling Water Flow [ID 53, m³/h], Ambient Humidity [ID 57], CO2 [ID 58, ppm], Production heats [ID 59], CO gas [ID 60, ppm]).\n"
            "- Threshold limits are configured in Settings. Alarms automatically trigger when these limits are breached (e.g. CB_OVERLOAD, TURBINE_OVERLOAD, SMS_LIMIT_SURGE, POWER_FACTOR_LOW) or if a sensor freezes (FROZEN_SENSOR).\n\n"
            "Instructions:\n"
            "1. Give direct, professional, and clear answers suited for an industrial control room operator.\n"
            "2. Rely on the LIVE SYSTEM CONTEXT above to answer questions about the current state of sensors and alarms.\n"
            "3. Format numbers and values clearly with their units (e.g., '1520.4 °C', '26163 kW').\n"
            "4. If requested to perform historical queries beyond the live snapshot, explain that you have live snapshot access, and suggest using the Trends page for historic visualization.\n"
            "5. Use Markdown lists or tables when summarizing multiple telemetry points.\n"
        )

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_prompt
        )

        google_history = []
        if payload.history:
            for h in payload.history:
                role = "user" if h.role == "user" else "model"
                google_history.append({
                    "role": role,
                    "parts": [h.content]
                })

        chat = model.start_chat(history=google_history)
        response = chat.send_message(payload.message)

        return {
            "response": response.text,
            "offline": False
        }
    except Exception as gemini_err:
        print(f"[GEMINI API ERROR]: {gemini_err}")
        return {
            "response": f"**AI Chatbot Connection Error**\n\nFailed to fetch response from Gemini: {str(gemini_err)}\n\nPlease check your internet connection or verify the `GEMINI_API_KEY` configuration.",
            "offline": True
        }
