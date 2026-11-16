# Data source

**EngineFaultDB** — `backend/data/raw/EngineFaultDB_Final.csv` (unmodified copy)

- Downloaded from: https://github.com/leoxthomas/EngineFaultDB (file `EngineFaultDB_Final.csv`)
- Paper: "EngineFaultDB: A Novel Dataset for Automotive Engine Fault Classification and
  Baseline Results", IEEE Access, 2023 — https://ieeexplore.ieee.org/abstract/document/10311597
- Licence: GPL-3.0 (copy in `backend/data/EngineFaultDB_LICENSE`)
- What it is: 55,999 laboratory readings from a C14NE 1.4 L petrol spark-ignition car engine,
  recorded with an NGA 6000 exhaust-gas analyser and an NI USB-6008 acquisition card.
- Columns: MAP, TPS, Force, Power, RPM, fuel consumption (L/h, L/100 km), Speed,
  CO (%), HC (ppm), CO2 (%), O2 (%), Lambda, AFR, and the label `Fault`.
- Labels: 0 = no fault (16,000), 1 = rich mixture (10,998), 2 = lean mixture (15,000),
  3 = low voltage (14,001).

No synthetic or generated data is used anywhere in this project.
