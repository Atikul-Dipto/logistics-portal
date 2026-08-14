"""Generates a synthetic but realistic logistics operations dataset:
shipments, inventory, warehouses, and carriers for a Bangladesh
e-commerce logistics network. Run once to (re)populate data/*.csv.
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

WAREHOUSES = [
    {"warehouse": "Dhaka Hub", "city": "Dhaka", "lat": 23.8103, "lon": 90.4125},
    {"warehouse": "Chattogram DC", "city": "Chattogram", "lat": 22.3569, "lon": 91.7832},
    {"warehouse": "Sylhet DC", "city": "Sylhet", "lat": 24.8949, "lon": 91.8687},
    {"warehouse": "Khulna DC", "city": "Khulna", "lat": 22.8456, "lon": 89.5403},
    {"warehouse": "Rajshahi DC", "city": "Rajshahi", "lat": 24.3745, "lon": 88.6042},
]

CARRIERS = ["Pathao Courier", "Sundarban Courier", "RedX", "eCourier", "Steadfast Courier"]

REGIONS = [
    "Dhaka", "Chattogram", "Sylhet", "Khulna", "Rajshahi",
    "Barisal", "Rangpur", "Mymensingh", "Comilla", "Narayanganj",
]

CATEGORIES = {
    "Electronics": ["Wireless Earbuds", "Power Bank", "Smartwatch", "Bluetooth Speaker", "Phone Case"],
    "Apparel": ["Cotton T-Shirt", "Panjabi", "Sneakers", "Saree", "Denim Jacket"],
    "Home & Living": ["Bedsheet Set", "Table Lamp", "Non-stick Pan", "Storage Box", "Curtain Set"],
    "Beauty": ["Face Wash", "Sunscreen SPF50", "Hair Serum", "Lipstick", "Perfume"],
    "Grocery": ["Basmati Rice 5kg", "Mustard Oil 1L", "Green Tea Pack", "Spice Combo", "Honey Jar"],
}

DELAY_REASONS = [
    "Weather disruption", "Vehicle breakdown", "Address issue", "Customs/checkpoint delay",
    "Warehouse backlog", "Failed delivery attempt", "Courier capacity shortage",
]

N_SHIPMENTS = 4200
START_DATE = pd.Timestamp("2025-09-01")
END_DATE = pd.Timestamp("2026-08-13")

# ---------- last-mile hub network ----------
HUBS = [
    "Probartak Hub", "3PL Hub", "Agrabad Hub", "Carry Bee Hub", "Badda Hub",
    "Jatrabari Hub", "Tejgaon Hub", "Dhanmondi Hub", "Old Town Hub", "Tongi Hub",
    "Uttara Hub", "Narayanganj Hub",
]

FLEET_TYPES = ["3PL", "Carrybee", "Ownfleet"]

DIVISIONS = [
    "Dhaka", "Chattogram", "Khulna", "Rajshahi", "Barisal", "Sylhet", "Rangpur", "Mymensingh",
]

DISTRICTS = [
    "Bagerhat", "Bandarban", "Barguna", "Barisal", "Bhola", "Bogra", "Brahmanbaria", "Chandpur",
    "Chapainawabganj", "Chattogram", "Chattogram Sadar", "Chuadanga", "Cox's Bazar", "Cumilla",
    "Dhaka North", "Dhaka South", "Dinajpur", "Faridpur", "Feni", "Gaibandha", "Gazipur",
    "Gopalganj", "Habiganj", "Jamalpur", "Jashore", "Jhalokati", "Jhenaidah", "Joypurhat",
    "Khagrachhari", "Khulna", "Kishoreganj", "Kurigram", "Kushtia", "Lakshmipur", "Lalmonirhat",
    "Madaripur", "Magura", "Manikganj", "Meherpur", "Moulvibazar", "Munshiganj", "Mymensingh",
    "Naogaon", "Narail", "Narayanganj", "Narsingdi", "Natore", "Netrokona", "Nilphamari",
    "Noakhali", "Pabna", "Panchagarh", "Patuakhali", "Pirojpur", "Rajbari", "Rajshahi",
    "Rangamati", "Rangpur", "Satkhira", "Shariatpur", "Sherpur", "Sirajganj", "Sunamganj",
    "Sylhet", "Tangail", "Thakurgaon",
]

N_LAST_MILE = 6000
N_FIRST_MILE = 5000


def build_skus():
    rows = []
    sku_id = 1000
    for category, products in CATEGORIES.items():
        for product in products:
            for variant in range(1, 3):
                rows.append(
                    {
                        "sku": f"SKU{sku_id}",
                        "product": f"{product}" if variant == 1 else f"{product} (V{variant})",
                        "category": category,
                        "unit_cost": round(RNG.uniform(150, 4500), 2),
                    }
                )
                sku_id += 1
    return pd.DataFrame(rows)


def build_shipments(skus: pd.DataFrame) -> pd.DataFrame:
    n = N_SHIPMENTS
    order_dates = START_DATE + pd.to_timedelta(
        RNG.integers(0, (END_DATE - START_DATE).days, size=n), unit="D"
    )
    warehouse_idx = RNG.integers(0, len(WAREHOUSES), size=n)
    warehouses = [WAREHOUSES[i]["warehouse"] for i in warehouse_idx]
    origin_city = [WAREHOUSES[i]["city"] for i in warehouse_idx]

    carrier = RNG.choice(CARRIERS, size=n, p=[0.28, 0.22, 0.2, 0.16, 0.14])
    destination_region = RNG.choice(REGIONS, size=n)
    sku_rows = skus.sample(n=n, replace=True, random_state=42).reset_index(drop=True)
    qty = RNG.integers(1, 6, size=n)
    weight_kg = np.round(RNG.uniform(0.2, 12.0, size=n), 2)

    # base transit time depends loosely on whether destination == origin city (local) or not
    is_local = np.array(destination_region) == np.array(origin_city)
    base_transit = np.where(is_local, RNG.uniform(1, 2, size=n), RNG.uniform(2, 6, size=n))

    # 78% delivered, 9% in transit, 8% delayed-but-delivered-late, 3% cancelled, 2% returned
    status_roll = RNG.random(n)
    status = np.select(
        [status_roll < 0.70, status_roll < 0.79, status_roll < 0.90, status_roll < 0.95, status_roll < 0.98],
        ["Delivered", "Delivered Late", "In Transit", "Delayed", "Cancelled"],
        default="Returned",
    )

    expected_delivery = order_dates + pd.to_timedelta(np.round(base_transit), unit="D")
    actual_delay_days = np.where(
        status == "Delivered Late",
        RNG.uniform(1, 5, size=n),
        np.where(status == "Delayed", RNG.uniform(0.5, 3, size=n), 0),
    )
    actual_delivery = expected_delivery + pd.to_timedelta(np.round(actual_delay_days), unit="D")

    now = END_DATE
    actual_delivery_out = []
    for s, d in zip(status, actual_delivery):
        if s in ("In Transit", "Delayed", "Cancelled"):
            actual_delivery_out.append(pd.NaT)
        else:
            actual_delivery_out.append(min(d, now))
    actual_delivery = pd.Series(actual_delivery_out)

    shipping_cost = np.round(
        40 + weight_kg * RNG.uniform(15, 28, size=n) + (~is_local) * RNG.uniform(20, 60, size=n),
        2,
    )
    unit_cost = sku_rows["unit_cost"].to_numpy()
    order_value = np.round(unit_cost * qty, 2)

    delay_reason = np.where(
        np.isin(status, ["Delayed", "Delivered Late"]),
        RNG.choice(DELAY_REASONS, size=n),
        "",
    )

    df = pd.DataFrame(
        {
            "shipment_id": [f"SHP{100000 + i}" for i in range(n)],
            "order_date": order_dates,
            "warehouse": warehouses,
            "origin_city": origin_city,
            "destination_region": destination_region,
            "carrier": carrier,
            "sku": sku_rows["sku"],
            "product": sku_rows["product"],
            "category": sku_rows["category"],
            "qty": qty,
            "weight_kg": weight_kg,
            "order_value": order_value,
            "shipping_cost": shipping_cost,
            "expected_delivery": expected_delivery,
            "actual_delivery": actual_delivery,
            "status": status,
            "delay_reason": delay_reason,
        }
    )
    return df


def build_inventory(skus: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for wh in WAREHOUSES:
        for _, sku in skus.iterrows():
            on_hand = int(RNG.integers(0, 800))
            reorder_point = int(RNG.integers(60, 200))
            rows.append(
                {
                    "warehouse": wh["warehouse"],
                    "city": wh["city"],
                    "sku": sku["sku"],
                    "product": sku["product"],
                    "category": sku["category"],
                    "on_hand": on_hand,
                    "reorder_point": reorder_point,
                    "unit_cost": sku["unit_cost"],
                    "stock_value": round(on_hand * sku["unit_cost"], 2),
                    "low_stock": on_hand < reorder_point,
                }
            )
    return pd.DataFrame(rows)


def build_last_mile() -> pd.DataFrame:
    n = N_LAST_MILE
    order_dates = START_DATE + pd.to_timedelta(
        RNG.integers(0, (END_DATE - START_DATE).days, size=n), unit="D"
    )

    hub_base = dict(zip(HUBS, RNG.uniform(38, 60, size=len(HUBS))))
    hub_base["Probartak Hub"] = 118  # known slow outlier hub
    hub_base["3PL Hub"] = 78

    source_hub = RNG.choice(HUBS, size=n)
    destination_hub = RNG.choice(HUBS, size=n)
    fleet_type = RNG.choice(FLEET_TYPES, size=n, p=[0.35, 0.30, 0.35])
    division = RNG.choice(DIVISIONS, size=n)
    district = RNG.choice(DISTRICTS, size=n)

    fleet_factor = np.select(
        [fleet_type == "Ownfleet", fleet_type == "Carrybee", fleet_type == "3PL"],
        [0.85, 1.0, 1.2],
    )
    district_factor = 1 + RNG.random(n) * 0.6  # remoter districts take longer
    base_hours = np.array([hub_base[h] for h in destination_hub])
    noise = RNG.normal(0, 6, size=n)
    hours = np.clip(base_hours * fleet_factor * district_factor * 0.6 + noise, 4, None)

    return pd.DataFrame(
        {
            "order_date": order_dates,
            "source_hub": source_hub,
            "destination_hub": destination_hub,
            "shipping_state": division,
            "shipping_city": district,
            "shipping_zone": district,
            "fleet_type": fleet_type,
            "pending_to_delivered_hours": np.round(hours, 2),
        }
    )


def build_first_mile() -> pd.DataFrame:
    """Seller pickup requests: request -> hub intake, before the
    last-mile leg takes over."""
    n = N_FIRST_MILE
    request_dates = START_DATE + pd.to_timedelta(
        RNG.integers(0, (END_DATE - START_DATE).days, size=n), unit="D"
    )

    hub_base = dict(zip(HUBS, RNG.uniform(2.0, 4.5, size=len(HUBS))))
    hub_base["Probartak Hub"] = 7.8  # same slow-outlier hub as last-mile
    hub_base["3PL Hub"] = 5.6

    origin_hub = RNG.choice(HUBS, size=n)
    seller_zone = RNG.choice(DISTRICTS, size=n)
    fleet_type = RNG.choice(FLEET_TYPES, size=n, p=[0.35, 0.30, 0.35])

    status_roll = RNG.random(n)
    pickup_status = np.select(
        [status_roll < 0.82, status_roll < 0.90, status_roll < 0.96],
        ["Completed", "Failed", "Pending"],
        default="Cancelled",
    )

    fleet_factor = np.select(
        [fleet_type == "Ownfleet", fleet_type == "Carrybee", fleet_type == "3PL"],
        [0.8, 1.0, 1.25],
    )
    base_hours = np.array([hub_base[h] for h in origin_hub])
    noise = RNG.normal(0, 0.8, size=n)
    duration = np.clip(base_hours * fleet_factor + noise, 0.5, None)
    pickup_duration_hours = np.where(np.isin(pickup_status, ["Completed", "Failed"]), np.round(duration, 2), np.nan)

    return pd.DataFrame(
        {
            "request_date": request_dates,
            "origin_hub": origin_hub,
            "seller_zone": seller_zone,
            "fleet_type": fleet_type,
            "pickup_status": pickup_status,
            "pickup_duration_hours": pickup_duration_hours,
        }
    )


if __name__ == "__main__":
    skus = build_skus()
    shipments = build_shipments(skus)
    inventory = build_inventory(skus)
    last_mile = build_last_mile()
    first_mile = build_first_mile()

    warehouses_df = pd.DataFrame(WAREHOUSES)

    skus.to_csv("data/skus.csv", index=False)
    shipments.to_csv("data/shipments.csv", index=False)
    inventory.to_csv("data/inventory.csv", index=False)
    warehouses_df.to_csv("data/warehouses.csv", index=False)
    last_mile.to_csv("data/last_mile.csv", index=False)
    first_mile.to_csv("data/first_mile.csv", index=False)

    print(f"shipments: {len(shipments)} rows")
    print(f"inventory: {len(inventory)} rows")
    print(f"skus: {len(skus)} rows")
    print(f"last_mile: {len(last_mile)} rows")
    print(f"first_mile: {len(first_mile)} rows")
