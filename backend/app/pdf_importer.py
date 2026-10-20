import re
import io
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import pdfplumber
from sqlalchemy.orm import Session
from backend.app.models import Device, SensorReading

def normalize_tag(name: str) -> str:
    """Normalize header text to match device names regardless of formatting."""
    return re.sub(r"\s+", "", name or "").lower()

def extract_pdf_tables(pdf_bytes: bytes) -> List[Tuple[List[str], List[str]]]:
    """Yields (header_cells, row_cells) for every valid data row in the PDF."""
    results = []
    header = None
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or not any(row):
                        continue
                    first_cell = str(row[0]).strip() if row[0] else ""
                    if "sync date" in first_cell.lower() or "date" in first_cell.lower():
                        header = [str(c).strip() if c else "" for c in row]
                        continue
                    if header is None:
                        continue
                    if first_cell.lower().startswith("total") or "summary" in first_cell.lower():
                        continue
                    if first_cell:
                        results.append((header, [str(c).strip() if c else "" for c in row]))
    return results

def parse_row_timestamp(date_str: str, time_str: str) -> Tuple[datetime, bool]:
    """Parse date and interval timestamps (e.g., '2026-07-05', '11:15 - 11:30' or '00:00 - 00:00')."""
    clean_date = date_str.strip()
    is_daily = "00:00 - 00:00" in time_str or not time_str.strip()
    
    start_time = time_str.split('-')[0].strip() if '-' in time_str else time_str.strip()
    if not start_time:
        start_time = "00:00"
        
    try:
        dt = datetime.strptime(f"{clean_date} {start_time}", "%Y-%m-%d %H:%M")
    except Exception:
        try:
            dt = datetime.strptime(clean_date, "%Y-%m-%d")
        except Exception:
            dt = datetime.utcnow()
    return dt, is_daily

def process_pdf_import(pdf_bytes: bytes, db: Session) -> Dict[str, Any]:
    """Parse PDF file bytes and insert readings into the database."""
    devices = db.query(Device).all()
    device_lookup = {normalize_tag(d.name): d for d in devices}
    # Also index by register address or sanitized substrings
    for d in devices:
        device_lookup[d.name.lower()] = d
        if d.register_address:
            device_lookup[d.register_address.lower()] = d

    rows = extract_pdf_tables(pdf_bytes)
    if not rows:
        return {"success": False, "message": "No valid tabular data found in the PDF.", "imported_count": 0}

    imported_count = 0
    unmatched_tags = set()

    for header, row in rows:
        if len(row) < 2:
            continue
        date_str = row[0]
        time_str = row[1] if len(row) > 1 else "00:00"
        ts, _ = parse_row_timestamp(date_str, time_str)

        for col_idx in range(2, len(header)):
            if col_idx >= len(row):
                break
            col_name = header[col_idx]
            raw_val = row[col_idx]
            if not col_name or not raw_val:
                continue

            clean_key = normalize_tag(col_name)
            device = device_lookup.get(clean_key)
            if not device:
                # Try finding closest match
                for d_name, dev in device_lookup.items():
                    if d_name in clean_key or clean_key in d_name:
                        device = dev
                        break

            if not device:
                unmatched_tags.add(col_name.replace("\n", " "))
                continue

            try:
                num_val = float(str(raw_val).replace(",", "").strip())
            except ValueError:
                continue

            # Upsert / insert reading
            reading = SensorReading(
                time=ts,
                sensor_id=device.id,
                value=num_val,
                quality="GOOD",
                status="OK"
            )
            db.merge(reading)
            imported_count += 1

    db.commit()

    return {
        "success": True,
        "message": f"Successfully imported {imported_count} telemetry records.",
        "imported_count": imported_count,
        "unmatched_tags": list(unmatched_tags)[:15]
    }
