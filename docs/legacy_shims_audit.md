# Legacy Shims & Backward-Compatibility Audit

This document catalogizes all backward-compatible forwarders and re-export shims preserved during the architectural refactoring of the **Industrial Energy Intelligence Platform (IEIP)**.

---

## 1. Summary of Active Legacy Shims

| Legacy Path (Root / Module) | Forwarding Destination | Type | Reason for Preservation |
| :--- | :--- | :--- | :--- |
| `start_local.bat` | `scripts/windows/start_local.bat` | Batch Wrapper | Preserves 1-click desktop double-click launcher habits. |
| `start_local.ps1` | `scripts/windows/start_local.ps1` | PowerShell Wrapper | Preserves automated PowerShell launching from root. |
| `stop_local.bat` | `scripts/windows/stop_local.bat` | Batch Wrapper | Preserves 1-click teardown habits. |
| `tunnel.bat` | `scripts/windows/tunnel.bat` | Batch Wrapper | Preserves Cloudflare live edge tunnel execution from root. |
| `build_apk.bat` | `scripts/windows/build_apk.bat` | Batch Wrapper | Preserves automated mobile build invocation from root. |
| `view_db.py` | `scripts/tools/db_tool.py` | Python Shim | Preserves `python view_db.py` inspection CLI syntax. |
| `query_db.py` | `scripts/tools/db_tool.py` | Python Shim | Preserves `python query_db.py "<SQL>"` CLI syntax. |
| `run_diagnostics.py` | `tests/diagnostics.py` | Python Shim | Preserves `python run_diagnostics.py` diagnostic runs. |
| `check_connectivity.py` | `tests/diagnostics.py` | Python Shim | Preserves standalone connectivity check command. |
| `test_tap_pipeline.py` | `tests/test_tap_pipeline.py` | Python Shim | Preserves standalone TAP pipeline check command. |
| `test_all_pages.py` | `tests/test_all_pages.py` | Python Shim | Preserves 12-page latency benchmark command. |
| `backend/app/router.py` | `backend/app/routers/*` | Router Aggregate | Aggregates all 10 sub-routers and re-exports `router` and `api_router`. |
| `backend/app/ai_query.py` | `backend/app/services/ai_copilot.py` | Re-export Module | Re-exports `execute_ai_query` and SQL prompts for backward-compatibility. |
| `tap_server/__init__.py` | `services/tap_server/` | Package Re-export | Allows `import tap_server` and `uvicorn tap_server.main:app`. |
| `tap_server/main.py` | `services/tap_server/main.py` | Module Re-export | Re-exports `app`, `metrics`, and endpoint handlers. |
| `tap_server/config.py` | `services/tap_server/config.py` | Module Re-export | Re-exports `tap_settings` and `TapSettings`. |
| `tap_server/database.py` | `services/tap_server/database.py` | Module Re-export | Re-exports `get_tap_db`, `engine`, and `TapBase`. |
| `tap_server/models.py` | `services/tap_server/models.py` | Module Re-export | Re-exports `TapTelemetryReading` and `SensorReading`. |
| `tap_server/Dockerfile` | `services/tap_server/Dockerfile` | Container Mirror | Ensures `docker build` using legacy path succeeds. |
| `simulator/scada_simulator.py` | `services/simulator/scada_simulator.py` | Python Forwarder | Allows `python simulator/scada_simulator.py` to run seamlessly. |
| `simulator/requirements.txt` | `services/simulator/requirements.txt` | File Mirror | Preserves dependencies file at root. |
| `simulator/Dockerfile` | `services/simulator/Dockerfile` | Container Mirror | Ensures `docker build` using legacy path succeeds. |
| `frontend/src/components/Sidebar.tsx` | `frontend/src/components/layout/index.ts` | Dual Support | Allows importing from `@/components/Sidebar` or `@/components/layout`. |
| `frontend/src/components/Header.tsx` | `frontend/src/components/layout/index.ts` | Dual Support | Allows importing from `@/components/Header` or `@/components/layout`. |

---

## 2. Deprecation Policy
- None of the above shims contain duplicated business logic; they are 5-to-15 line forwarding wrappers.
- They incur zero measurable runtime overhead.
- They can remain permanently for maximum backward compatibility or be scheduled for deprecation in a future major version (v2.0) once all external workflows transition to the new paths.
