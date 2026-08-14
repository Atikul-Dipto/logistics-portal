"""Cached data loading + derived-column helpers shared across pages."""
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@st.cache_data
def load_shipments() -> pd.DataFrame:
    df = pd.read_csv(
        DATA_DIR / "shipments.csv",
        parse_dates=["order_date", "expected_delivery", "actual_delivery"],
    )
    df["is_delivered"] = df["status"].isin(["Delivered", "Delivered Late"])
    df["on_time"] = df["is_delivered"] & (df["actual_delivery"] <= df["expected_delivery"])
    df["delivery_days"] = (df["actual_delivery"] - df["order_date"]).dt.days
    df["order_month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
    return df


@st.cache_data
def load_inventory() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "inventory.csv")


@st.cache_data
def load_skus() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "skus.csv")


@st.cache_data
def load_warehouses() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "warehouses.csv")


@st.cache_data
def load_last_mile() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "last_mile.csv", parse_dates=["order_date"])


def compact_parts(value: float) -> tuple[float, str]:
    for divisor, suffix in ((1_000_000, "M"), (1_000, "K")):
        if abs(value) >= divisor:
            return round(value / divisor), suffix
    return round(value), ""


def compact_number(value: float) -> str:
    amount, suffix = compact_parts(value)
    return f"{amount:,.0f}{suffix}"


def kpi_delta_color(value: float, higher_is_better: bool = True) -> str:
    if value == 0:
        return "off"
    positive = value > 0
    good = positive if higher_is_better else not positive
    return "normal" if good else "inverse"
