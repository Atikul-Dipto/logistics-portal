"""Exports real aggregates from shipments.csv that the logistics-
flow-map "Command Center" needs to ground its operational UI (hub
stats, delay-reason breakdown, carrier stats, date bounds) in actual
data instead of inventing numbers client-side. Companion to
export_flow_data.py -- run once, or re-run whenever generate_data.py
regenerates the CSVs, then copy ops_data.json into the flow-map
repo's public/data/.
"""
import json

import pandas as pd

DELAY_REASONS = [
    "Weather disruption", "Vehicle breakdown", "Address issue", "Customs/checkpoint delay",
    "Warehouse backlog", "Failed delivery attempt", "Courier capacity shortage",
]


def build_hub_stats(shipments: pd.DataFrame) -> list[dict]:
    shipments = shipments.copy()
    shipments["destination_hub"] = shipments["destination_region"] + " Hub"
    rows = []
    for hub, g in shipments.groupby("destination_hub"):
        delay_mix = (
            g[g["delay_reason"] != ""]["delay_reason"].value_counts(normalize=True).round(3).to_dict()
        )
        rows.append(
            {
                "hub": hub,
                "region": hub.replace(" Hub", ""),
                "shipment_count": int(len(g)),
                "on_time_rate": round(float((g["status"].isin(["Delivered", "Delivered Late"])).mean()), 3),
                "avg_shipping_cost": round(float(g["shipping_cost"].mean()), 2),
                "avg_weight_kg": round(float(g["weight_kg"].mean()), 2),
                "delay_reason_mix": delay_mix,
                "status_mix": g["status"].value_counts(normalize=True).round(3).to_dict(),
            }
        )
    return rows


def build_warehouse_stats(shipments: pd.DataFrame) -> list[dict]:
    rows = []
    for wh, g in shipments.groupby("warehouse"):
        rows.append(
            {
                "warehouse": wh,
                "shipment_count": int(len(g)),
                "on_time_rate": round(float((g["status"].isin(["Delivered", "Delivered Late"])).mean()), 3),
                "avg_shipping_cost": round(float(g["shipping_cost"].mean()), 2),
            }
        )
    return rows


def build_carrier_stats(shipments: pd.DataFrame) -> list[dict]:
    rows = []
    for carrier, g in shipments.groupby("carrier"):
        rows.append(
            {
                "carrier": carrier,
                "shipment_count": int(len(g)),
                "on_time_rate": round(float((g["status"].isin(["Delivered", "Delivered Late"])).mean()), 3),
                "avg_shipping_cost": round(float(g["shipping_cost"].mean()), 2),
                "cod_value": round(float(g["order_value"].sum()), 2),
            }
        )
    return rows


def build_network_delay_reasons(shipments: pd.DataFrame) -> dict:
    counts = shipments[shipments["delay_reason"] != ""]["delay_reason"].value_counts()
    total = int(counts.sum())
    return {
        "total_delayed": total,
        "breakdown": [
            {"reason": reason, "count": int(counts.get(reason, 0)), "pct": round(float(counts.get(reason, 0) / total), 3) if total else 0}
            for reason in DELAY_REASONS
        ],
    }


if __name__ == "__main__":
    shipments = pd.read_csv("data/shipments.csv")

    out = {
        "generated_from": "logistics-portal/data/shipments.csv",
        "total_shipments": int(len(shipments)),
        "total_order_value": round(float(shipments["order_value"].sum()), 2),
        "date_bounds": {
            "min_order_date": shipments["order_date"].min(),
            "max_order_date": shipments["order_date"].max(),
        },
        "hub_stats": build_hub_stats(shipments),
        "warehouse_stats": build_warehouse_stats(shipments),
        "carrier_stats": build_carrier_stats(shipments),
        "network_delay_reasons": build_network_delay_reasons(shipments),
    }

    with open("data/ops_data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=None, separators=(",", ":"))

    print(f"hubs: {len(out['hub_stats'])}  warehouses: {len(out['warehouse_stats'])}  carriers: {len(out['carrier_stats'])}")
    print(f"date bounds: {out['date_bounds']}")
