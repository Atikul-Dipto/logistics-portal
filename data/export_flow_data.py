"""Exports the shipments dataset as a weighted directed graph (nodes +
lanes) for the standalone logistics-flow-map app. Static output, not
part of the Streamlit app's runtime -- run once, or re-run whenever
generate_data.py regenerates the CSVs, then copy flow_data.json into
the flow-map repo's public/data/.
"""
import json

import pandas as pd

WAREHOUSES = pd.read_csv("data/warehouses.csv")

# Same 10 region-hub coordinates used for the Overview map before it
# became a choropleth -- kept here so the flow map's node positions
# stay consistent with the rest of the project.
REGION_HUBS = {
    "Dhaka": (23.8103, 90.4125),
    "Chattogram": (22.3569, 91.7832),
    "Sylhet": (24.8949, 91.8687),
    "Khulna": (22.8456, 89.5403),
    "Rajshahi": (24.3745, 88.6042),
    "Barisal": (22.7010, 90.3535),
    "Rangpur": (25.7439, 89.2752),
    "Mymensingh": (24.7471, 90.4203),
    "Comilla": (23.4607, 91.1809),
    "Narayanganj": (23.6238, 90.5000),
}


def build_nodes() -> list[dict]:
    # One warehouse ("Dhaka Hub") and one region hub ("Dhaka Hub")
    # happen to share a display name -- id-prefix by type so every
    # node id is unique and edge source/target lookups are never
    # ambiguous, even though the label stays the plain original name.
    nodes = []
    for _, wh in WAREHOUSES.iterrows():
        nodes.append(
            {
                "id": f"wh:{wh['warehouse']}",
                "type": "warehouse",
                "label": wh["warehouse"],
                "lat": float(wh["lat"]),
                "lon": float(wh["lon"]),
            }
        )
    for region, (lat, lon) in REGION_HUBS.items():
        nodes.append(
            {
                "id": f"hub:{region} Hub",
                "type": "hub",
                "label": f"{region} Hub",
                "region": region,
                "lat": lat,
                "lon": lon,
            }
        )
    return nodes


def build_edges(shipments: pd.DataFrame) -> list[dict]:
    """One row per (origin warehouse, destination hub, carrier) lane,
    not collapsed across carriers -- so the flow map can filter to a
    single carrier's subgraph client-side instead of only ever
    showing the network as a whole."""
    shipments = shipments.copy()
    shipments["is_delivered"] = shipments["status"].isin(["Delivered", "Delivered Late"])
    shipments["actual_delivery"] = pd.to_datetime(shipments["actual_delivery"])
    shipments["expected_delivery"] = pd.to_datetime(shipments["expected_delivery"])
    shipments["on_time"] = shipments["is_delivered"] & (
        shipments["actual_delivery"] <= shipments["expected_delivery"]
    )
    shipments["destination_hub"] = shipments["destination_region"] + " Hub"

    edges = []
    grouped = shipments.groupby(["warehouse", "destination_hub", "carrier"])
    for (origin, destination, carrier), g in grouped:
        status_mix = g["status"].value_counts(normalize=True).round(3).to_dict()
        edges.append(
            {
                "source": f"wh:{origin}",
                "target": f"hub:{destination}",
                "carrier": carrier,
                "volume": int(len(g)),
                "avg_weight_kg": round(float(g["weight_kg"].mean()), 2),
                "avg_shipping_cost": round(float(g["shipping_cost"].mean()), 2),
                "on_time_rate": round(float(g["on_time"].mean()), 3),
                "status_mix": status_mix,
            }
        )
    return edges


if __name__ == "__main__":
    shipments = pd.read_csv("data/shipments.csv")
    nodes = build_nodes()
    edges = build_edges(shipments)

    out = {
        "generated_from": "logistics-portal/data/shipments.csv",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "total_volume": sum(e["volume"] for e in edges),
        "carriers": sorted(shipments["carrier"].unique().tolist()),
        "nodes": nodes,
        "edges": edges,
    }

    with open("data/flow_data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=None, separators=(",", ":"))

    print(f"nodes: {len(nodes)}  edges: {len(edges)}  total volume: {out['total_volume']}")
