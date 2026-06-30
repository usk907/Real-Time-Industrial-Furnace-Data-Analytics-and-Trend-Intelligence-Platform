# Software Requirements Specification (SRS)
## Real-Time Industrial Furnace Data Analytics and Trend Prediction System Using SCADA Data

---

### 1. Introduction

#### 1.1 Purpose
This document specifies the software requirements for the **Real-Time Industrial Furnace Data Analytics and Trend Prediction System**. It details functional, non-functional, interface, and performance requirements to guide developers, database administrators, data scientists, and plant engineers.

#### 1.2 Document Conventions
* All terminology aligns with industrial automation (SCADA, PLC, OPC UA, Modbus TCP) and data science standards.
* Requirements are assigned unique identifiers using the format `[REQ-SYS-XX]` for general requirements, `[REQ-FUN-XX]` for functional features, and `[REQ-NFR-XX]` for non-functional criteria.
* Key terms:
  * **SCADA**: Supervisory Control and Data Acquisition.
  * **PLC**: Programmable Logic Controller.
  * **Hypertables**: Partitions in TimescaleDB that optimize time-series queries.
  * **KPI**: Key Performance Indicator.

#### 1.3 Intended Audience and Reading Suggestions
* **Plant Operators & Control Engineers**: Focus on Section 2 (Overall Description), Section 3 (External Interfaces), and Section 4.9 (Visualization).
* **Software Backend & Frontend Developers**: Focus on Sections 3 (Interfaces), 4 (System Features), and 5 (Non-Functional Requirements).
* **Data Engineers & Database Administrators**: Focus on Section 4.2 (Preprocessing), Section 4.3 (Database Storage), and Section 5 (Performance).
* **Data Scientists**: Focus on Section 4.6 (Anomaly Detection) and Section 4.7 (Forecasting Engine).

#### 1.4 Project Scope
The system will ingest real-time telemetric tags from an industrial furnace control system via OPC UA, Modbus TCP, or MQTT. It will process, store, and analyze the telemetry data to compute operational KPIs, detect electrical and operational anomalies, forecast future furnace load, and generate reports. The system is designed to complement existing SCADA dashboards by providing analytical, historical, and predictive capabilities without modifying the physical furnace control logic.

---

### 2. Overall Description

#### 2.1 Product Perspective
The system operates as an analytical overlay to existing industrial control systems. It sits downstream from the SCADA/PLC environment, consuming data from standard interfaces (OPC UA, Modbus TCP, or MQTT) and acting as a read-only client.

```
┌─────────────────┐      ┌─────────────────────────┐      ┌─────────────────┐
│  PLCs / Sensors  │ ───> │ SCADA Server / Gateway  │ ───> │  This Analytics │
│ (Furnace/Trans.)│      │  (OPC UA / Modbus / MQ) │      │      System     │
└─────────────────┘      └─────────────────────────┘      └─────────────────┘
```

#### 2.2 Product Functions
The core capabilities of the system are divided into nine functional modules:
1. **SCADA Data Acquisition**: Live connection to OPC UA / Modbus TCP endpoints to stream sensor tags.
2. **Data Preprocessing**: Real-time cleaning, synchronization, and validation of incoming streams.
3. **Time-Series Storage**: Partitioned storage optimized for fast historical queries.
4. **Trend Analytics**: Computation of statistical rollups (moving averages, rolling std-dev).
5. **KPI Engine**: Calculation of industrial efficiencies, load factor, and energy consumption metrics.
6. **Anomaly Detection**: Automated detection of electrical transients, overloads, and unexpected shutdowns.
7. **Forecasting Engine**: Asynchronous inference using machine learning to predict loads.
8. **Report Generator**: Automated and on-demand report compiling for operational audits.
9. **Visualization Dashboard**: Web-based responsive portal presenting real-time telemetry, historical analysis, predictions, and alerts.

#### 2.3 User Classes and Characteristics
* **Plant Operations Manager**: Highly interested in KPIs, utilization reports, and forecasting. Requires consolidated views to optimize cost and production schedules.
* **Control/Plant Engineer**: Interacts with the real-time trend visualization and anomaly panel to troubleshoot equipment issues.
* **Maintenance Technician**: Needs access to historical alerts, anomaly patterns, and forecasted equipment health indicators to perform predictive maintenance.
* **System Administrator**: Manages database retention, user access, and SCADA driver configurations.

#### 2.4 Operating Environment
* **Hardware**: Dedicated server in the plant control room network (OT network) or a secure private cloud environment. Minimum requirements: 8-core CPU, 32 GB RAM, and high-speed SSD storage.
* **Software**: Docker-compatible host operating system (Linux Ubuntu 22.04 LTS or Windows Server 2022).
* **Database**: TimescaleDB 2.10+ (PostgreSQL 15 extension) and Redis 7.0+.
* **Networking**: Secure LAN connection to the plant network containing the SCADA servers/gateways.

#### 2.5 Design and Implementation Constraints
* **[REQ-CON-01] Read-Only Isolation**: The system must never send command strings, setpoints, or control variables back to the PLC or SCADA system.
* **[REQ-CON-02] Python Ecosystem**: Backend operations and ML inference must use Python 3.10+ for scikit-learn, PyTorch, and FastAPI compatibility.
* **[REQ-CON-03] Database Partitioning**: To maintain performance, the database must partition sensor data dynamically based on time intervals (e.g., daily chunks).

#### 2.6 Assumptions and Dependencies
* **Tag Configuration Stability**: It is assumed that the SCADA/PLC tag addresses and registers remain constant. Any physical configuration changes must be manually updated in the driver schema.
* **Network Reliability**: A continuous local network connection is required between the SCADA gateway and the analytics server. Intermittent connections will rely on local caching at the SCADA gateway level.

---

### 3. External Interface Requirements

#### 3.1 User Interfaces
The web interface must be responsive (support 1080p desktop monitors up to 4K control room displays).
* **Live Telemetry Dashboard**: Gauges, charts, and live cards updated at 1 Hz.
* **Analytics Workbench**: Multi-series line charts with zooming, panning, and date filtering.
* **Alert Center**: High-contrast alarm indicators with filtering, categorization, and acknowledgment inputs.
* **Configuration Portal**: Forms to configure tag properties, anomaly thresholds, and email/SMS report schedules.

#### 3.2 Hardware Interfaces
* The physical system connects to the network via standard Ethernet (RJ45) or fiber interfaces, utilizing standard TCP/IP protocol suites.

#### 3.3 Software Interfaces
* **SCADA Protocols**: 
  * OPC UA Client interface conforming to IEC 62541.
  * Modbus TCP Client interface conforming to Modbus Application Protocol Specification V1.1b.
* **MQTT Broker**: Connection to an external or local MQTT Broker (e.g., Eclipse Mosquitto) for event-driven pub/sub.
* **Storage Interfaces**: PostgreSQL driver (asyncpg/psycopg2) for TimescaleDB access, Redis client for caching and session state.

#### 3.4 Communications Interfaces
* **REST API**: Secure HTTPS API for frontend web consumption.
* **WebSockets**: WSS connection for streaming live sensor values from the backend FastAPI to the React client at 1-second intervals.
* **Notification Protocols**: SMTP client for email reports and custom HTTP webhook hooks for instant SMS alerts.

---

### 4. System Features (Functional Requirements)

#### 4.1 SCADA Data Acquisition (Module 1)
* **[REQ-FUN-101] PLC Tag Reading**: The acquisition module shall read tag registers (Voltage, Current, Grid kW, Transformer Load, SMS Furnace status, Power Factor) at a configurable polling frequency (default: 1 Hz).
* **[REQ-FUN-102] Timestamp Synchronization**: Incoming SCADA frames must be timestamped with millisecond precision at the time of ingest, synchronized via NTP.
* **[REQ-FUN-103] Range Validation**: Incoming telemetry values must be checked against defined physical boundaries (e.g., Power Factor between -1.0 and 1.0; Voltage between 0V and 15,000V). Values outside bounds must be marked as invalid.

#### 4.2 Data Preprocessing (Module 2)
* **[REQ-FUN-201] Missing Value Handling**: Missing telemetric values must be imputed using forward-fill or linear interpolation, up to a maximum duration of 10 seconds. Beyond 10 seconds, the stream state must be marked as "Degraded".
* **[REQ-FUN-202] Deduplication**: Identical sequential frames containing duplicate SCADA timestamps must be discarded, retaining only the first instance.
* **[REQ-FUN-203] Data Normalization**: The system must convert all physical readings to SI units (e.g., converting kW to MW or Volts to kV) and normalize features dynamically for ML ingestion.

#### 4.3 Database Ingestion & Storage (Module 3)
* **[REQ-FUN-301] Hypertable Ingestion**: Telemetry data must be ingested into TimescaleDB hypertables, partitioned by the `time` field.
* **[REQ-FUN-302] Historical Storage**: The database shall retain raw sensor data for 90 days, compressed data for 365 days, and aggregated statistics (KPIs, trends) indefinitely.
* **[REQ-FUN-303] Relational Metadata**: Separate relational tables must store operational metadata including sensor mappings, alert profiles, and furnace characteristics.

#### 4.4 Trend Analytics Engine (Module 4)
* **[REQ-FUN-401] Statistical Rolling Rollups**: The engine shall compute rolling averages, standard deviation, and variance on time-series windows (e.g., 5-minute, 15-minute, 1-hour, and 24-hour windows).
* **[REQ-FUN-402] Trend Trajectory Analysis**: The engine must compute linear regression slopes over moving windows to categorize trend directions (e.g., Voltage Trend: Rising, Stable, Falling).

#### 4.5 KPI Calculation Engine (Module 5)
* **[REQ-FUN-501] Efficiency & Utilization Computation**: The engine shall compute Peak Demand, Load Factor, Transformer Utilization, Generator Efficiency, and Specific Energy Consumption (SEC, calculated as Energy consumed per unit of output).
* **[REQ-FUN-502] Asynchronous Rollup Execution**: Daily, weekly, and monthly KPIs must be calculated asynchronously (via Celery/Cron jobs) and written to the `kpi_data` database table.

#### 4.6 Anomaly Detection Engine (Module 6)
* **[REQ-FUN-601] Rule-Based Alerts**: The system must trigger alarms for immediate threshold violations (e.g., Voltage Spike > 115% nominal, Voltage Dip < 85% nominal, Power Factor < 0.8).
* **[REQ-FUN-602] Statistical/ML Anomaly Detection**: The engine must execute an Isolation Forest or Z-score sliding window model to detect multi-variable anomalies, such as current imbalance or unexpected furnace shutdowns.
* **[REQ-FUN-603] Alarm Management**: Alarms must be persisted with start time, end time, severity (Critical, Warning, Info), and state (Active, Acknowledged, Cleared).

#### 4.7 Forecasting Engine (Module 7)
* **[REQ-FUN-701] Multi-Horizon Forecasting**: The system must predict active load (kW) and cumulative energy consumption for horizons of 5m, 15m, 30m, 1h, and 24h.
* **[REQ-FUN-702] Automated Re-training**: The prediction models (LSTM/PatchTST) must automatically re-train weekly on historical datasets.

#### 4.8 Automated Report Generator (Module 8)
* **[REQ-FUN-801] Scheduled Report Compiling**: The reporting module must automatically generate Daily (at 00:05), Weekly (Mondays at 00:10), and Monthly reports summarizing operational health, energy usage, and alarms.
* **[REQ-FUN-802] Dynamic Format Support**: Reports must be downloadable in PDF and Excel formats, containing both raw tables and pre-rendered performance charts.

#### 4.9 Visualization Dashboard (Module 9)
* **[REQ-FUN-901] Real-time Widgets**: The web application must display real-time dials and charts for Voltage, Current, Power Factor, and Furnace Load.
* **[REQ-FUN-902] Predictive Line Overlay**: Historical chart views must overlay predicted values alongside actual sensor readings for comparison.
* **[REQ-FUN-903] Interactive Alarm Management**: Operators must be able to view, sort, filter, and acknowledge active and historical alarms from a dedicated console pane.

---

### 5. Other Non-Functional Requirements

#### 5.1 Performance Requirements
* **[REQ-NFR-511] UI Ingestion Latency**: The total latency from sensor tag generation at the PLC to visual rendering on the web dashboard must be less than 1.5 seconds.
* **[REQ-NFR-512] Query Response Time**: Standard historical queries for any 30-day window must return data in less than 2.0 seconds.
* **[REQ-NFR-513] Concurrent Connections**: The FastAPI backend must support up to 50 concurrent active WebSocket dashboards.

#### 5.2 Safety and Security Requirements
* **[REQ-NFR-521] Access Control**: Role-Based Access Control (RBAC) must distinguish between Administrator, Engineer, and Operator roles.
* **[REQ-NFR-522] Data Encryption**: All API calls must utilize HTTPS (TLS 1.3), and backend credentials must be encrypted at rest.
* **[REQ-NFR-523] Network Separation**: The system must run behind a firewall separating the Control Network (OT) from the Business Network (IT), with access strictly restricted.

#### 5.3 Reliability and Availability
* **[REQ-NFR-531] Uptime SLA**: The analytics system must maintain an availability of 99.9% (excluding scheduled maintenance).
* **[REQ-NFR-532] Crash Recovery**: If the ingestion service fails, it must automatically restart and reconnect to the OPC UA/MQTT source within 10 seconds.

#### 5.4 Scalability
* **[REQ-NFR-541] Multi-tag Capability**: The ingestion engine must scale to support up to 10,000 SCADA tag points without degrading dashboard ingestion performance.
* **[REQ-NFR-542] Database Auto-Partitioning**: TimescaleDB must automatically provision new daily tables dynamically as time-series metrics grow.

#### 5.5 Maintainability
* **[REQ-NFR-551] Centralized Logging**: All exceptions, preprocessing failures, database operations, and model runs must be logged using structured JSON logging (e.g., Python structlog) written to a persistent file rotation system.
