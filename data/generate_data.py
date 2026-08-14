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

# ---------- unified last-mile / first-mile hub network ----------
# One hub per shipping region, so hub names tie directly back to the
# same `destination_region` values already used in the shipments
# table above instead of an unrelated, made-up hub list.
HUBS = [f"{region} Hub" for region in REGIONS]

HUB_WEIGHTS = [0.28, 0.14, 0.08, 0.09, 0.08, 0.07, 0.07, 0.07, 0.06, 0.06]

CARRIER_SPEED = {
    "Pathao Courier": 0.9,
    "RedX": 0.85,
    "eCourier": 1.05,
    "Steadfast Courier": 1.0,
    "Sundarban Courier": 1.2,
}

# ---------- marketplace sellers ----------
SHOP_PREFIXES = [
    "Urban", "Metro", "Bengal", "Green", "Prime", "Royal", "Smart", "Nova", "Suncity", "Riverside",
    "Golden", "Silver", "Classic", "Modern", "Trendy", "Elite", "Value", "Fresh", "Delta", "Horizon",
]
SHOP_SUFFIXES = [
    "Mart", "Bazaar", "Store", "Collection", "Trading", "Fashion House", "Emporium", "Corner",
    "Hub", "Depot", "Gallery", "Outlet", "Shop", "Retail", "Traders",
]
N_SELLERS = 60


def _unique_shop_names(n: int) -> list[str]:
    names = set()
    while len(names) < n:
        names.add(f"{RNG.choice(SHOP_PREFIXES)} {RNG.choice(SHOP_SUFFIXES)}")
    return sorted(names)


def build_sellers() -> pd.DataFrame:
    shop_names = _unique_shop_names(N_SELLERS)
    seller_region = RNG.choice(REGIONS, size=N_SELLERS, p=HUB_WEIGHTS)
    return pd.DataFrame(
        {
            "seller_code": [f"SEL{1000 + i}" for i in range(N_SELLERS)],
            "shop_name": shop_names,
            "seller_region": seller_region,
        }
    )


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


def build_shipments(skus: pd.DataFrame, sellers: pd.DataFrame) -> pd.DataFrame:
    n = N_SHIPMENTS
    order_dates = START_DATE + pd.to_timedelta(
        RNG.integers(0, (END_DATE - START_DATE).days, size=n), unit="D"
    )
    warehouse_idx = RNG.integers(0, len(WAREHOUSES), size=n)
    warehouses = [WAREHOUSES[i]["warehouse"] for i in warehouse_idx]
    origin_city = [WAREHOUSES[i]["city"] for i in warehouse_idx]

    seller_idx = RNG.integers(0, len(sellers), size=n)
    seller_code = sellers["seller_code"].to_numpy()[seller_idx]
    shop_name = sellers["shop_name"].to_numpy()[seller_idx]
    seller_region = sellers["seller_region"].to_numpy()[seller_idx]

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
            "order_code": [f"ORD{100000 + i}" for i in range(n)],
            "package_code": [f"PKG{100000 + i}" for i in range(n)],
            "order_date": order_dates,
            "warehouse": warehouses,
            "origin_city": origin_city,
            "seller_code": seller_code,
            "shop_name": shop_name,
            "seller_region": seller_region,
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


def build_last_mile(shipments: pd.DataFrame) -> pd.DataFrame:
    """One last-mile leg per shipment. Reuses the shipment's own id,
    date, origin warehouse, destination region, carrier, and status
    so this table stays in lockstep with the shipments table instead
    of drifting off as an unrelated synthetic population."""
    n = len(shipments)
    destination_region = shipments["destination_region"].to_numpy()
    destination_hub = np.array([f"{r} Hub" for r in destination_region])
    origin_warehouse = shipments["warehouse"].to_numpy()
    carrier = shipments["carrier"].to_numpy()
    is_local = shipments["origin_city"].to_numpy() == destination_region

    hub_base = dict(zip(HUBS, RNG.uniform(20, 34, size=len(HUBS))))
    base_hours = np.array([hub_base[h] for h in destination_hub])
    carrier_factor = np.array([CARRIER_SPEED[c] for c in carrier])
    remote_factor = np.where(is_local, 1.0, RNG.uniform(1.15, 1.6, size=n))
    noise = RNG.normal(0, 4, size=n)
    hours = np.clip(base_hours * carrier_factor * remote_factor + noise, 3, None)

    return pd.DataFrame(
        {
            "shipment_id": shipments["shipment_id"].to_numpy(),
            "order_code": shipments["order_code"].to_numpy(),
            "package_code": shipments["package_code"].to_numpy(),
            "order_date": shipments["order_date"].to_numpy(),
            "origin_warehouse": origin_warehouse,
            "destination_hub": destination_hub,
            "destination_region": destination_region,
            "carrier": carrier,
            "status": shipments["status"].to_numpy(),
            "seller_code": shipments["seller_code"].to_numpy(),
            "shop_name": shipments["shop_name"].to_numpy(),
            "seller_region": shipments["seller_region"].to_numpy(),
            "weight_kg": shipments["weight_kg"].to_numpy(),
            "pending_to_delivered_hours": np.round(hours, 2),
        }
    )


def build_first_mile(shipments: pd.DataFrame) -> pd.DataFrame:
    """One seller-pickup leg per shipment: request -> hub intake,
    before the last-mile leg takes over. Draws on the same hub
    network and carrier list as the last-mile leg above, and the
    pickup outcome is correlated with the shipment's own status
    (a cancelled order never had a pickup happen)."""
    n = len(shipments)
    origin_hub = RNG.choice(HUBS, size=n, p=HUB_WEIGHTS)
    carrier = shipments["carrier"].to_numpy()

    status_roll = RNG.random(n)
    pickup_status = np.select(
        [shipments["status"].to_numpy() == "Cancelled", status_roll < 0.86, status_roll < 0.94],
        ["Cancelled", "Completed", "Failed"],
        default="Pending",
    )

    hub_base = dict(zip(HUBS, RNG.uniform(2.2, 4.2, size=len(HUBS))))
    base_hours = np.array([hub_base[h] for h in origin_hub])
    carrier_factor = np.array([CARRIER_SPEED[c] for c in carrier])
    noise = RNG.normal(0, 0.7, size=n)
    duration = np.clip(base_hours * carrier_factor + noise, 0.5, None)
    pickup_duration_hours = np.where(np.isin(pickup_status, ["Completed", "Failed"]), np.round(duration, 2), np.nan)

    return pd.DataFrame(
        {
            "shipment_id": shipments["shipment_id"].to_numpy(),
            "order_code": shipments["order_code"].to_numpy(),
            "package_code": shipments["package_code"].to_numpy(),
            "request_date": shipments["order_date"].to_numpy(),
            "origin_hub": origin_hub,
            "carrier": carrier,
            "seller_code": shipments["seller_code"].to_numpy(),
            "shop_name": shipments["shop_name"].to_numpy(),
            "seller_region": shipments["seller_region"].to_numpy(),
            "weight_kg": shipments["weight_kg"].to_numpy(),
            "pickup_status": pickup_status,
            "pickup_duration_hours": pickup_duration_hours,
        }
    )


if __name__ == "__main__":
    skus = build_skus()
    sellers = build_sellers()
    shipments = build_shipments(skus, sellers)
    inventory = build_inventory(skus)
    last_mile = build_last_mile(shipments)
    first_mile = build_first_mile(shipments)

    warehouses_df = pd.DataFrame(WAREHOUSES)

    skus.to_csv("data/skus.csv", index=False)
    sellers.to_csv("data/sellers.csv", index=False)
    shipments.to_csv("data/shipments.csv", index=False)
    inventory.to_csv("data/inventory.csv", index=False)
    warehouses_df.to_csv("data/warehouses.csv", index=False)
    last_mile.to_csv("data/last_mile.csv", index=False)
    first_mile.to_csv("data/first_mile.csv", index=False)

    print(f"shipments: {len(shipments)} rows")
    print(f"inventory: {len(inventory)} rows")
    print(f"skus: {len(skus)} rows")
    print(f"sellers: {len(sellers)} rows")
    print(f"last_mile: {len(last_mile)} rows")
    print(f"first_mile: {len(first_mile)} rows")
