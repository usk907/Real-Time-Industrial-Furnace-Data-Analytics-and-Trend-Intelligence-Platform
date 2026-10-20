import os
import re
import google.generativeai as genai
from sqlalchemy.orm import Session
from sqlalchemy import text

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

def is_safe_select(sql: str) -> tuple[bool, str]:
    """Returns (is_safe, reason_if_not)."""
    cleaned = sql.strip().rstrip(";").strip()

    if not re.match(r"^\s*SELECT\b", cleaned, re.IGNORECASE):
        return False, "Query must start with SELECT"

    if ";" in cleaned:
        return False, "Multiple statements are not allowed"

    if FORBIDDEN_PATTERN.search(cleaned):
        return False, "Query contains a disallowed keyword"

    return True, ""

def enforce_limit(sql: str, max_rows: int = 100) -> str:
    if re.search(r"\bLIMIT\s+\d+\s*$", sql, re.IGNORECASE):
        return sql
    return f"{sql.rstrip().rstrip(';')} LIMIT {max_rows}"

def get_gemini_client(api_key: str):
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    genai.configure(api_key=api_key)
    return genai

def generate_sql(question: str, api_key: str) -> str:
    genai_client = get_gemini_client(api_key)
    prompt = SQL_SYSTEM_PROMPT.format(schema=SCHEMA_CONTEXT)
    
    model = genai_client.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(f"{prompt}\n\nQUESTION: {question}\n\nSQL:")
    
    sql = response.text.strip()
    sql = re.sub(r"^```(?:sql)?\s*|\s*```$", "", sql, flags=re.IGNORECASE | re.MULTILINE).strip()
    return sql

def summarize_results(question: str, sql: str, rows: list, api_key: str) -> str:
    genai_client = get_gemini_client(api_key)
    prompt = (
        f"{SUMMARY_SYSTEM_PROMPT}\n\n"
        f"QUESTION: {question}\n\nSQL RUN: {sql}\n\nRESULTS ({len(rows)} rows): {rows[:50]}\n\nANSWER:"
    )
    model = genai_client.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

def execute_ai_query(question: str, db: Session, api_key: str) -> dict:
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
        # convert row result objects into list of dicts for JSON serialization
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
