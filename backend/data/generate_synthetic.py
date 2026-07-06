"""
Synthetic Dataset Generator for PredictV.

Generates 100,000+ realistic vehicle emission and sensor records with
correlated fault labels, health scores, and maintenance history.

Uses automotive engineering principles to create realistic correlations:
- Rich fuel mixture → high CO, low O₂, lambda < 1
- Lean mixture → high NOx, high O₂, lambda > 1
- Bad catalytic converter → high HC, high NOx, low cat efficiency
- Engine wear → high HC, high oil consumption, low compression indicators
"""

import json
import os
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# Seed for reproducibility
np.random.seed(42)
random.seed(42)

# ──────────────────────────────────────────────
# Vehicle Definitions
# ──────────────────────────────────────────────

BRANDS_MODELS = {
    "Toyota": ["Camry", "Corolla", "RAV4", "Highlander", "Prius", "Yaris"],
    "Honda": ["Civic", "Accord", "CR-V", "HR-V", "Fit"],
    "BMW": ["3 Series", "5 Series", "X3", "X5", "1 Series"],
    "Mercedes": ["C-Class", "E-Class", "GLC", "A-Class", "GLA"],
    "Volkswagen": ["Golf", "Passat", "Tiguan", "Polo", "Arteon"],
    "Ford": ["Focus", "Fiesta", "Mustang", "Explorer", "F-150"],
    "Audi": ["A3", "A4", "A6", "Q5", "Q7"],
    "Hyundai": ["Elantra", "Tucson", "Santa Fe", "i30", "Kona"],
    "Nissan": ["Altima", "Sentra", "Rogue", "Qashqai", "X-Trail"],
    "Mazda": ["Mazda3", "Mazda6", "CX-5", "CX-30", "MX-5"],
    "Kia": ["Cerato", "Sportage", "Sorento", "Seltos", "Stinger"],
    "Chevrolet": ["Cruze", "Malibu", "Equinox", "Silverado", "Camaro"],
    "Subaru": ["Impreza", "Outback", "Forester", "WRX", "XV"],
    "Volvo": ["S60", "S90", "XC40", "XC60", "XC90"],
    "Lexus": ["IS", "ES", "RX", "NX", "UX"],
}

FUEL_TYPES = ["petrol", "diesel", "hybrid", "lpg", "cng"]
FUEL_WEIGHTS = [0.45, 0.25, 0.15, 0.10, 0.05]

ENGINE_CAPACITIES = {
    "petrol": [1.0, 1.2, 1.4, 1.5, 1.6, 1.8, 2.0, 2.4, 2.5, 3.0, 3.5],
    "diesel": [1.5, 1.6, 2.0, 2.2, 2.5, 3.0],
    "hybrid": [1.5, 1.8, 2.0, 2.5],
    "lpg": [1.4, 1.6, 1.8, 2.0, 2.4],
    "cng": [1.4, 1.6, 1.8, 2.0],
}

CLIMATES = ["tropical", "temperate", "arid", "continental", "subarctic"]
DRIVING_CONDITIONS = ["city", "highway", "mixed", "off_road", "stop_and_go"]

FAULT_LIST = [
    "Dirty Air Filter", "Bad Spark Plug", "Injector Problem", "Fuel Pump Issue",
    "Turbo Failure", "Catalytic Converter Failure", "Faulty Oxygen Sensor",
    "Vacuum Leak", "Poor Compression", "Engine Misfire", "Oil Burning",
    "Coolant Leakage", "Rich Fuel Mixture", "Lean Fuel Mixture", "EGR Failure",
    "DPF Blockage", "Valve Wear", "Piston Ring Wear", "Head Gasket Issue",
    "Timing Problem", "Sensor Failure",
]


def generate_vehicle() -> Dict:
    """Generate a random vehicle profile."""
    brand = random.choice(list(BRANDS_MODELS.keys()))
    model = random.choice(BRANDS_MODELS[brand])
    fuel_type = random.choices(FUEL_TYPES, weights=FUEL_WEIGHTS, k=1)[0]
    current_year = 2026
    year = random.randint(2005, current_year)
    age = current_year - year
    engine_capacity = random.choice(ENGINE_CAPACITIES[fuel_type])
    mileage = max(0, int(np.random.lognormal(mean=np.log(age * 15000 + 5000), sigma=0.4)))
    has_turbo = random.random() < (0.6 if fuel_type == "diesel" else 0.2)

    return {
        "brand": brand,
        "model": model,
        "year": year,
        "age": age,
        "fuel_type": fuel_type,
        "engine_capacity": engine_capacity,
        "mileage": mileage,
        "has_turbo": has_turbo,
        "cylinders": 4 if engine_capacity <= 2.5 else 6,
    }


def compute_base_health(vehicle: Dict, fault_severity: float) -> float:
    """Compute base engine health score from vehicle age, mileage, and fault severity."""
    # Base health decreases with age and mileage
    age_factor = max(0, 100 - vehicle["age"] * 3.5)
    mileage_factor = max(0, 100 - (vehicle["mileage"] / 3000))
    base = 0.4 * age_factor + 0.3 * mileage_factor + 0.3 * 100
    # Apply fault degradation
    health = base * (1 - fault_severity * 0.6)
    return np.clip(health + np.random.normal(0, 3), 0, 100)


def generate_faults(vehicle: Dict) -> Tuple[List[str], List[float], float]:
    """Generate fault labels with probabilities based on vehicle profile."""
    age = vehicle["age"]
    mileage = vehicle["mileage"]
    fuel_type = vehicle["fuel_type"]
    has_turbo = vehicle["has_turbo"]

    # Base fault probability increases with age and mileage
    base_prob = np.clip(0.02 + age * 0.015 + (mileage / 500000), 0, 0.7)

    fault_probs = {}
    for fault in FAULT_LIST:
        prob = base_prob * np.random.uniform(0.3, 1.5)

        # Fault-specific modifiers
        if fault == "Dirty Air Filter":
            prob *= 1.5  # Common fault
        elif fault == "Bad Spark Plug" and fuel_type != "diesel":
            prob *= 1.3 + age * 0.05
        elif fault == "Turbo Failure":
            prob = prob * 2.0 if has_turbo else 0.0
        elif fault == "DPF Blockage":
            prob = prob * 2.0 if fuel_type == "diesel" else 0.0
        elif fault in ["Piston Ring Wear", "Valve Wear", "Poor Compression"]:
            prob *= 1 + (mileage / 200000)
        elif fault == "Head Gasket Issue":
            prob *= 1 + (mileage / 250000)
        elif fault in ["Rich Fuel Mixture", "Lean Fuel Mixture"]:
            prob *= 1.2

        fault_probs[fault] = np.clip(prob, 0, 0.95)

    # Select active faults (typically 0-4 faults)
    active_faults = []
    active_probs = []
    for fault, prob in fault_probs.items():
        if random.random() < prob:
            active_faults.append(fault)
            active_probs.append(round(np.clip(prob + np.random.normal(0, 0.1), 0.1, 0.99), 3))

    severity = sum(active_probs) / max(len(active_probs), 1) if active_faults else 0
    return active_faults, active_probs, severity


def generate_emissions(vehicle: Dict, faults: List[str], health: float) -> Dict:
    """Generate realistic emission values based on engine condition and faults."""
    fuel = vehicle["fuel_type"]
    is_diesel = fuel == "diesel"
    degradation = (100 - health) / 100

    # Base emission values for a healthy engine
    if is_diesel:
        co = np.random.normal(0.15, 0.05)
        co2 = np.random.normal(13.5, 0.5)
        hc = np.random.normal(80, 20)
        o2 = np.random.normal(2.0, 0.5)
        nox = np.random.normal(40, 15)
        lam = np.random.normal(1.3, 0.1)
        smoke = np.random.normal(8, 3)
    else:
        co = np.random.normal(0.08, 0.03)
        co2 = np.random.normal(14.5, 0.3)
        hc = np.random.normal(50, 15)
        o2 = np.random.normal(0.5, 0.2)
        nox = np.random.normal(25, 10)
        lam = np.random.normal(1.0, 0.02)
        smoke = np.random.normal(2, 1)

    # Apply fault effects
    for fault in faults:
        if fault == "Rich Fuel Mixture":
            co *= 2.5
            o2 *= 0.5
            lam *= 0.92
            hc *= 1.4
        elif fault == "Lean Fuel Mixture":
            nox *= 2.5
            o2 *= 2.0
            lam *= 1.08
        elif fault == "Catalytic Converter Failure":
            hc *= 3.0
            co *= 2.0
            nox *= 2.5
        elif fault == "Faulty Oxygen Sensor":
            lam += np.random.choice([-0.15, 0.15])
            co *= 1.5
        elif fault == "Bad Spark Plug":
            hc *= 2.0
            co *= 1.8
        elif fault == "Engine Misfire":
            hc *= 3.5
            co *= 2.0
        elif fault == "Injector Problem":
            hc *= 2.0
            co *= 1.5
            lam += np.random.normal(0, 0.05)
        elif fault == "Dirty Air Filter":
            co *= 1.5
            hc *= 1.3
            lam *= 0.97
        elif fault == "EGR Failure":
            nox *= 2.0
        elif fault == "DPF Blockage":
            smoke *= 3.0
        elif fault == "Oil Burning":
            hc *= 1.8
            smoke *= 2.0
        elif fault == "Poor Compression":
            hc *= 2.5
            co *= 1.5
        elif fault == "Vacuum Leak":
            hc *= 1.5
            lam *= 1.05
        elif fault == "Turbo Failure":
            smoke *= 2.5
        elif fault == "Piston Ring Wear":
            hc *= 2.0
            smoke *= 1.8
        elif fault == "Head Gasket Issue":
            co *= 1.5
            hc *= 1.5
        elif fault == "Valve Wear":
            hc *= 1.8
        elif fault == "Timing Problem":
            hc *= 2.0
            co *= 1.5

    # General degradation
    co *= (1 + degradation * 0.8)
    hc *= (1 + degradation * 0.6)
    nox *= (1 + degradation * 0.5)
    smoke *= (1 + degradation * 0.4)
    co2 *= (1 - degradation * 0.1)  # CO₂ drops with poor combustion

    return {
        "co_percent": round(np.clip(co, 0.01, 8.0), 3),
        "co2_percent": round(np.clip(co2, 5.0, 16.5), 1),
        "hc_ppm": round(np.clip(hc, 5, 5000), 0),
        "o2_percent": round(np.clip(o2, 0.0, 21.0), 2),
        "nox_ppm": round(np.clip(nox, 5, 3000), 0),
        "lambda_value": round(np.clip(lam, 0.7, 2.5), 3),
        "smoke_opacity": round(np.clip(smoke, 0, 100), 1),
    }


def generate_sensors(vehicle: Dict, health: float, faults: List[str]) -> Dict:
    """Generate realistic OBD-II sensor values."""
    degradation = (100 - health) / 100

    # Climate conditions
    ambient_temp = np.random.normal(25, 10)
    humidity = np.random.uniform(30, 90)

    # Engine sensors
    rpm = np.random.normal(800, 50)
    if "Engine Misfire" in faults:
        rpm += np.random.normal(0, 100)

    oil_temp = np.random.normal(95, 5)
    if "Oil Burning" in faults:
        oil_temp += 15

    coolant_temp = np.random.normal(90, 3)
    if "Coolant Leakage" in faults:
        coolant_temp += np.random.uniform(10, 25)
    if "Head Gasket Issue" in faults:
        coolant_temp += np.random.uniform(15, 30)

    exhaust_temp = np.random.normal(350, 50)
    if "Lean Fuel Mixture" in faults:
        exhaust_temp += 80

    afr = np.random.normal(14.7, 0.3)
    if "Rich Fuel Mixture" in faults:
        afr -= 1.5
    elif "Lean Fuel Mixture" in faults:
        afr += 1.5

    engine_load = np.random.normal(22, 5)
    throttle = np.random.normal(5, 2)

    fuel_consumption = np.random.normal(1.2, 0.3) * (vehicle["engine_capacity"] / 2.0)
    fuel_consumption *= (1 + degradation * 0.3)

    fuel_pressure = np.random.normal(350, 15)
    if "Fuel Pump Issue" in faults:
        fuel_pressure -= 80

    turbo_pressure = None
    if vehicle["has_turbo"]:
        turbo_pressure = np.random.normal(1.2, 0.2)
        if "Turbo Failure" in faults:
            turbo_pressure *= 0.4

    o2_sensor = np.random.normal(0.45, 0.1)
    if "Faulty Oxygen Sensor" in faults:
        o2_sensor = random.choice([0.1, 0.9])  # Stuck lean or rich

    cat_eff = np.random.normal(96, 2)
    if "Catalytic Converter Failure" in faults:
        cat_eff -= np.random.uniform(20, 50)

    maf = np.random.normal(15, 3) * (vehicle["engine_capacity"] / 2.0)
    if "Dirty Air Filter" in faults:
        maf *= 0.75

    map_sensor = np.random.normal(35, 5)
    if "Vacuum Leak" in faults:
        map_sensor += 15

    battery = np.random.normal(13.8, 0.3)
    running_time = max(100, vehicle["mileage"] / np.random.uniform(25, 40))

    return {
        "exhaust_temp": round(np.clip(exhaust_temp, 100, 900), 1),
        "engine_rpm": round(np.clip(rpm, 500, 1200), 0),
        "air_fuel_ratio": round(np.clip(afr, 10, 20), 2),
        "oil_temp": round(np.clip(oil_temp, 60, 150), 1),
        "coolant_temp": round(np.clip(coolant_temp, 60, 130), 1),
        "ambient_temp": round(np.clip(ambient_temp, -20, 50), 1),
        "relative_humidity": round(np.clip(humidity, 10, 99), 1),
        "engine_load": round(np.clip(engine_load, 5, 100), 1),
        "throttle_position": round(np.clip(throttle, 0, 100), 1),
        "fuel_consumption": round(np.clip(fuel_consumption, 0.3, 15), 2),
        "fuel_pressure": round(np.clip(fuel_pressure, 100, 500), 0),
        "turbo_pressure": round(np.clip(turbo_pressure, 0, 3.5), 2) if turbo_pressure else None,
        "o2_sensor_reading": round(np.clip(o2_sensor, 0.0, 1.0), 3),
        "catalytic_efficiency": round(np.clip(cat_eff, 30, 100), 1),
        "maf_sensor": round(np.clip(maf, 1, 200), 1),
        "map_sensor": round(np.clip(map_sensor, 15, 110), 1),
        "battery_voltage": round(np.clip(battery, 10, 15.5), 1),
        "engine_running_time": round(np.clip(running_time, 50, 20000), 0),
    }


def determine_compliance(emissions: Dict, fuel_type: str) -> str:
    """Determine emission compliance status."""
    is_diesel = fuel_type == "diesel"
    fails = 0
    warnings = 0

    co_limit = 0.5 if is_diesel else 0.3
    hc_limit = 200 if is_diesel else 100
    nox_limit = 80 if is_diesel else 60
    smoke_limit = 30 if is_diesel else 10

    if emissions["co_percent"] > co_limit * 1.5:
        fails += 1
    elif emissions["co_percent"] > co_limit:
        warnings += 1

    if emissions["hc_ppm"] > hc_limit * 1.5:
        fails += 1
    elif emissions["hc_ppm"] > hc_limit:
        warnings += 1

    if emissions["nox_ppm"] > nox_limit * 1.5:
        fails += 1
    elif emissions["nox_ppm"] > nox_limit:
        warnings += 1

    if emissions["smoke_opacity"] > smoke_limit * 1.5:
        fails += 1
    elif emissions["smoke_opacity"] > smoke_limit:
        warnings += 1

    if fails >= 1:
        return "Fail"
    elif warnings >= 2:
        return "Warning"
    elif warnings >= 1:
        return "Warning"
    else:
        return "Pass"


def generate_rul(vehicle: Dict, health: float) -> Dict:
    """Generate remaining useful life predictions."""
    base_life = 300000  # 300K km base life
    remaining_life = max(0, (base_life - vehicle["mileage"]) * (health / 100))

    # Time to maintenance
    km_since_service = vehicle["mileage"] % 15000  # assume 15K km service interval
    km_to_maintenance = max(500, 15000 - km_since_service - (100 - health) * 50)

    # Major repair estimate
    km_to_major = remaining_life * 0.3 if health < 50 else remaining_life * 0.7

    # Breakdown probability
    breakdown_prob = np.clip((100 - health) / 200 + (vehicle["mileage"] / 1000000), 0, 0.95)

    return {
        "remaining_life_km": round(remaining_life),
        "km_to_maintenance": round(km_to_maintenance),
        "km_to_major_repair": round(km_to_major),
        "breakdown_probability": round(breakdown_prob, 3),
    }


def generate_forecasts(health: float, degradation_rate: float) -> List[Dict]:
    """Generate future condition forecasts for 30, 90, 180, 365 days."""
    forecasts = []
    for days in [30, 90, 180, 365]:
        daily_deg = degradation_rate / 365
        future_health = max(0, health - daily_deg * days + np.random.normal(0, 1))
        health_drop = health - future_health

        forecasts.append({
            "horizon_days": days,
            "health_score": round(future_health, 1),
            "emission_increase_pct": round(health_drop * 0.5 + np.random.normal(0, 1), 1),
            "fuel_efficiency_loss_pct": round(health_drop * 0.3 + np.random.normal(0, 0.5), 1),
            "maintenance_cost": round(max(0, health_drop * 15 + np.random.normal(0, 20)), 0),
            "risk_score": round(np.clip((100 - future_health) / 100, 0, 1), 3),
            "engine_degradation_pct": round(health_drop, 1),
        })

    return forecasts


def generate_dataset(n_records: int = 100000, output_dir: str = "./data") -> str:
    """Generate the complete synthetic dataset."""
    os.makedirs(output_dir, exist_ok=True)
    records = []

    for i in range(n_records):
        vehicle = generate_vehicle()
        faults, fault_probs, severity = generate_faults(vehicle)
        health = compute_base_health(vehicle, severity)
        emissions = generate_emissions(vehicle, faults, health)
        sensors = generate_sensors(vehicle, health, faults)
        compliance = determine_compliance(emissions, vehicle["fuel_type"])
        rul = generate_rul(vehicle, health)
        forecasts = generate_forecasts(health, degradation_rate=np.random.uniform(3, 15))

        record = {
            # Vehicle info
            "brand": vehicle["brand"],
            "model": vehicle["model"],
            "year": vehicle["year"],
            "vehicle_age": vehicle["age"],
            "fuel_type": vehicle["fuel_type"],
            "engine_capacity": vehicle["engine_capacity"],
            "mileage": vehicle["mileage"],
            "has_turbo": vehicle["has_turbo"],
            "cylinders": vehicle["cylinders"],
            "climate": random.choice(CLIMATES),
            "driving_condition": random.choice(DRIVING_CONDITIONS),

            # Emissions
            **emissions,

            # Sensors
            **sensors,

            # Labels
            "health_score": round(health, 1),
            "health_class": (
                "Excellent" if health >= 85 else
                "Good" if health >= 70 else
                "Moderate" if health >= 50 else
                "Poor" if health >= 30 else
                "Critical"
            ),
            "emission_compliance": compliance,

            # Faults (multi-label)
            "fault_count": len(faults),
            "active_faults": json.dumps(faults),
            "fault_probabilities": json.dumps(dict(zip(faults, fault_probs))),

            # Individual fault columns (binary)
            **{f"fault_{f.lower().replace(' ', '_')}": 1 if f in faults else 0 for f in FAULT_LIST},

            # RUL
            **rul,

            # Forecasts
            "forecast_30d_health": forecasts[0]["health_score"],
            "forecast_90d_health": forecasts[1]["health_score"],
            "forecast_180d_health": forecasts[2]["health_score"],
            "forecast_365d_health": forecasts[3]["health_score"],
            "forecast_30d_risk": forecasts[0]["risk_score"],
            "forecast_90d_risk": forecasts[1]["risk_score"],
            "forecast_180d_risk": forecasts[2]["risk_score"],
            "forecast_365d_risk": forecasts[3]["risk_score"],
        }
        records.append(record)

        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1:,} / {n_records:,} records...")

    df = pd.DataFrame(records)
    output_path = os.path.join(output_dir, "synthetic_vehicle_data.csv")
    df.to_csv(output_path, index=False)
    print(f"\n✅ Dataset saved to {output_path}")
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {len(df.columns)}")
    print(f"\n📊 Health Distribution:")
    print(df["health_class"].value_counts().to_string())
    print(f"\n📊 Compliance Distribution:")
    print(df["emission_compliance"].value_counts().to_string())
    print(f"\n📊 Average Fault Count: {df['fault_count'].mean():.2f}")

    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic vehicle emission dataset")
    parser.add_argument("--count", type=int, default=100000, help="Number of records to generate")
    parser.add_argument("--output", type=str, default="./data", help="Output directory")
    parser.add_argument("--verify", action="store_true", help="Run verification checks")
    args = parser.parse_args()

    path = generate_dataset(n_records=args.count, output_dir=args.output)

    if args.verify:
        df = pd.read_csv(path)
        print("\n── Verification ──")
        print(f"Records: {len(df)}")
        print(f"Null counts:\n{df.isnull().sum()[df.isnull().sum() > 0]}")
        print(f"Health score range: [{df['health_score'].min()}, {df['health_score'].max()}]")
        print(f"CO range: [{df['co_percent'].min()}, {df['co_percent'].max()}]")
        print("✅ Verification passed")
