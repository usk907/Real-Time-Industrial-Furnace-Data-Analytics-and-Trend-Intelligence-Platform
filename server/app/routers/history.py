"""
Historical Telemetry Query Endpoint
Provides time-series data with dynamic bucket downsampling (raw, 1m, 5m, 1h).
Limits results to 5000 points with helpful error feedback.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from server.app.database import get_db
from server.app.models import User
from server.app.schemas import HistoryResponse, HistoryPoint
from server.app.auth import get_current_user

router = APIRouter(prefix="/api/history", tags=["Historical Telemetry"])

BUCKET_SECONDS = {
    "1m": 60,
    "5m": 300,
    "1h": 3600
}

@router.get("", response_model=HistoryResponse)
def get_historical_telemetry(
    tag: str = Query(..., description="Tag name to query"),
    from_ts: Optional[datetime] = Query(None, alias="from", description="Start timestamp (ISO-8601)"),
    to_ts: Optional[datetime] = Query(None, alias="to", description="End timestamp (ISO-8601)"),
    bucket: str = Query("raw", pattern="^(raw|1m|5m|1h)$", description="Downsampling bucket (raw, 1m, 5m, 1h)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves time-series data for a specific tag.
    Supports SQL downsampling via GROUP BY (1m, 5m, 1h).
    Enforces a hard limit of 5000 points.
    """
    now = datetime.now()
    if to_ts is None:
        to_ts = now
    if from_ts is None:
        from_ts = to_ts - timedelta(hours=1)

    if from_ts > to_ts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'from' timestamp must be before 'to' timestamp."
        )

    dialect = db.bind.dialect.name if db.bind else "mysql"

    if bucket == "raw":
        query_sql = text("""
            SELECT ts, value
            FROM furnace_readings
            WHERE tag = :tag AND ts >= :from_ts AND ts <= :to_ts
            ORDER BY ts ASC
            LIMIT 5001
        """)
        params = {"tag": tag, "from_ts": from_ts, "to_ts": to_ts}
        result = db.execute(query_sql, params).fetchall()

        if len(result) > 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requested time range returned more than 5000 raw points. "
                       "Please select a bucket aggregation (e.g. 1m, 5m, or 1h) or narrow the time range."
            )

        points = [
            HistoryPoint(
                ts=r[0] if isinstance(r[0], datetime) else datetime.fromisoformat(str(r[0])),
                value=round(float(r[1]), 3),
                count=1
            )
            for r in result
        ]

    else:
        sec = BUCKET_SECONDS[bucket]
        if dialect == "mysql":
            query_sql = text("""
                SELECT 
                    FROM_UNIXTIME(FLOOR(UNIX_TIMESTAMP(ts) / :sec) * :sec) AS b_ts,
                    AVG(value) AS avg_val,
                    MIN(value) AS min_val,
                    MAX(value) AS max_val,
                    COUNT(*) AS pt_count
                FROM furnace_readings
                WHERE tag = :tag AND ts >= :from_ts AND ts <= :to_ts
                GROUP BY b_ts
                ORDER BY b_ts ASC
                LIMIT 5001
            """)
            params = {"tag": tag, "from_ts": from_ts, "to_ts": to_ts, "sec": sec}
        else:
            # SQLite fallback for test environments
            query_sql = text("""
                SELECT 
                    datetime((strftime('%s', ts) / :sec) * :sec, 'unixepoch') AS b_ts,
                    AVG(value) AS avg_val,
                    MIN(value) AS min_val,
                    MAX(value) AS max_val,
                    COUNT(*) AS pt_count
                FROM furnace_readings
                WHERE tag = :tag AND ts >= :from_ts AND ts <= :to_ts
                GROUP BY b_ts
                ORDER BY b_ts ASC
                LIMIT 5001
            """)
            params = {"tag": tag, "from_ts": from_ts, "to_ts": to_ts, "sec": sec}

        result = db.execute(query_sql, params).fetchall()

        if len(result) > 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested range with bucket '{bucket}' returned more than 5000 points. "
                       f"Please select a larger bucket size (e.g. 5m or 1h) or narrow the query range."
            )

        points = []
        for r in result:
            ts_val = r[0]
            if isinstance(ts_val, str):
                ts_val = datetime.fromisoformat(ts_val)
            points.append(HistoryPoint(
                ts=ts_val,
                value=round(float(r[1]), 3),
                min_value=round(float(r[2]), 3),
                max_value=round(float(r[3]), 3),
                count=int(r[4])
            ))

    return HistoryResponse(
        tag=tag,
        bucket=bucket,
        from_ts=from_ts,
        to_ts=to_ts,
        count=len(points),
        points=points
    )
