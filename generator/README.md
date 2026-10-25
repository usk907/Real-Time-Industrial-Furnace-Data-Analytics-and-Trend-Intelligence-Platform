# IEIP Telemetry Generator (Part 1)

Dedicated, standalone industrial SCADA simulator and MySQL data stream generator for the Industrial Energy Intelligence Platform.

## Overview
- **Cadence**: Emits 60 SCADA tags once per second (`GEN_INTERVAL_SECONDS=1.0`).
- **Destination**: Writes directly to local MySQL (`127.0.0.1:3306`) tables:
  - `furnace_readings`: Continuous time-series archive with `(ts, tag, value, quality)`.
  - `furnace_latest`: In-memory / indexed latest-state cache with `(tag, value, ts)`.
- **Atomic Commits**: Batches both table operations into a single transaction per tick using `executemany`.
- **Bounded Random Walks**: Values fluctuate realistically within physical operational limits; cumulative tags only increase.
- **Anomaly Demonstration**: Injects an out-of-bounds anomaly approximately every 500 ticks to trigger live alarms.

## Tags Configured (60 Total)
- **Electric Arc Furnace 1 (EAF-1)**: 15 tags (Active/Reactive/Apparent Power, Voltage, Current, Power Factor, Shell/Roof/Bath Temperatures, Cooling Water Flow/Pressure, Hydraulic Pressure, Electrode Current, Gas Pressure, Cumulative kWh).
- **Ladle Refining Furnace 2 (LRF-2)**: 15 tags (Power metrics, Bath Temp, Argon Stirring Flow/Pressure, Cooling Water, Vacuum Pressure, Electrode Current, Heating Rate, Cumulative kWh).
- **Main Substation Transformers (TR-1 & TR-2)**: 15 tags (33kV/690V Voltages, Primary/Secondary Currents, Active/Reactive Power, Power Factors, Winding & Oil Temps, Grid Cumulative kWh).
- **Hot Rolling Mill (RM-1)**: 8 tags (Stand 1 Drive Power, Speed RPM, Motor Current, Reheat Furnace Zones 1 & 2 Temps, Descaler Pressure, Cooling Flow, Cumulative kWh).
- **Water Treatment & Utilities (WTP-1)**: 7 tags (Main Pump Power/Current, Supply Header Pressure/Flow/Temp, Return Header Temp, Cumulative kWh).

## Installation & Execution

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env

# 3. Run continuously
python generator.py

# 4. Or run for a specific number of ticks (e.g. 10 ticks for testing):
python generator.py 10
```
