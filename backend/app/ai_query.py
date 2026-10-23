"""
Legacy AI Query Shim
Re-exports execute_ai_query and prompts from backend.app.services.ai_copilot for backward compatibility.
"""
from backend.app.services.ai_copilot import (
    SCHEMA_CONTEXT,
    SQL_SYSTEM_PROMPT,
    SUMMARY_SYSTEM_PROMPT,
    FORBIDDEN_PATTERN,
    is_safe_select,
    enforce_limit,
    get_gemini_client,
    generate_sql,
    summarize_results,
    execute_ai_query
)

__all__ = [
    "SCHEMA_CONTEXT",
    "SQL_SYSTEM_PROMPT",
    "SUMMARY_SYSTEM_PROMPT",
    "FORBIDDEN_PATTERN",
    "is_safe_select",
    "enforce_limit",
    "get_gemini_client",
    "generate_sql",
    "summarize_results",
    "execute_ai_query"
]
