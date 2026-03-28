"""Fetch real estate market data from free public sources."""

import io
import csv

import requests


# --- Boston area cities to track ---
MA_CITIES = [
    "Boston", "Cambridge", "Somerville", "Newton", "Brookline",
    "Quincy", "Medford", "Waltham", "Arlington", "Watertown",
    "Needham", "Wellesley", "Lexington", "Belmont", "Winchester",
    "Worcester", "Springfield", "Lowell", "Framingham",
]


def fetch_zillow_metro() -> dict:
    """Fetch Zillow ZHVI for MA metro areas."""
    url = "https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"

    ma_metros = {
        "Boston, MA": "Boston 都会区",
        "Worcester, MA": "Worcester 都会区",
        "Springfield, MA": "Springfield 都会区",
    }

    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()

        reader = csv.DictReader(io.StringIO(resp.text))
        fieldnames = reader.fieldnames
        date_cols = sorted([c for c in fieldnames if c and len(c) == 10 and c[4] == '-'])

        if len(date_cols) < 13:
            return {}

        latest_col = date_cols[-1]
        prev_month_col = date_cols[-2]
        year_ago_col = date_cols[-13]

        results = {}
        for row in reader:
            region = row.get("RegionName", "")
            for key, label in ma_metros.items():
                if key in region:
                    current = row.get(latest_col, "")
                    prev = row.get(prev_month_col, "")
                    year_ago = row.get(year_ago_col, "")

                    if current:
                        entry = {"value": float(current), "date": latest_col}
                        if prev:
                            entry["mom"] = (float(current) - float(prev)) / float(prev) * 100
                        if year_ago:
                            entry["yoy"] = (float(current) - float(year_ago)) / float(year_ago) * 100
                        results[label] = entry

        return {"cities": results, "period": latest_col}
    except Exception as e:
        print(f"  Warning: Failed to fetch Zillow metro data: {e}")
        return {}


def fetch_zillow_cities() -> dict:
    """Fetch Zillow ZHVI for individual MA cities."""
    url = "https://files.zillowstatic.com/research/public_csvs/zhvi/City_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"

    try:
        resp = requests.get(url, timeout=90)
        resp.raise_for_status()

        reader = csv.DictReader(io.StringIO(resp.text))
        fieldnames = reader.fieldnames
        date_cols = sorted([c for c in fieldnames if c and len(c) == 10 and c[4] == '-'])

        if len(date_cols) < 13:
            return {}

        latest_col = date_cols[-1]
        prev_month_col = date_cols[-2]
        year_ago_col = date_cols[-13]

        results = {}
        for row in reader:
            state = row.get("State", "")
            city = row.get("RegionName", "")
            if state == "MA" and city in MA_CITIES:
                current = row.get(latest_col, "")
                prev = row.get(prev_month_col, "")
                year_ago = row.get(year_ago_col, "")

                if current:
                    entry = {"value": float(current), "date": latest_col}
                    if prev:
                        entry["mom"] = (float(current) - float(prev)) / float(prev) * 100
                    if year_ago:
                        entry["yoy"] = (float(current) - float(year_ago)) / float(year_ago) * 100
                    results[city] = entry

        return {"cities": results, "period": latest_col}
    except Exception as e:
        print(f"  Warning: Failed to fetch Zillow city data: {e}")
        return {}


def fetch_mortgage_rate() -> dict:
    """Fetch latest 30-year mortgage rate from FRED."""
    try:
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US&cosd=2025-01-01&coed=2030-01-01"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()

        lines = resp.text.strip().split("\n")
        if len(lines) < 2:
            return {}

        last_line = lines[-1]
        parts = last_line.split(",")
        if len(parts) >= 2 and parts[1] != ".":
            return {"date": parts[0], "rate": parts[1]}
    except Exception as e:
        print(f"  Warning: Failed to fetch mortgage rate: {e}")
    return {}


def _fmt(val, fmt_type="price"):
    try:
        v = float(val)
        if fmt_type == "price":
            return f"${int(v):,}"
        elif fmt_type == "yoy":
            return f"{v*100:+.1f}%"
        elif fmt_type == "pct":
            return f"{v*100:.1f}%"
        elif fmt_type == "num":
            return f"{int(v):,}"
    except (ValueError, TypeError):
        pass
    return val or "N/A"


def format_market_summary(zillow_metro: dict, zillow_cities: dict, mortgage: dict) -> str:
    """Format all market data into a readable summary."""
    lines = []

    # City-level prices (sorted by value, highest first)
    if zillow_cities and zillow_cities.get("cities"):
        lines.append(f"🏘️ 波士顿周边城市房价 (Zillow ZHVI, {zillow_cities.get('period', '')})")
        lines.append("=" * 50)
        sorted_cities = sorted(zillow_cities["cities"].items(), key=lambda x: x[1]["value"], reverse=True)
        for city, data in sorted_cities:
            val = f"${int(data['value']):,}"
            parts = [f"  {city:<15} {val:>12}"]
            if "mom" in data:
                parts.append(f"月 {data['mom']:+.1f}%")
            if "yoy" in data:
                parts.append(f"年 {data['yoy']:+.1f}%")
            lines.append("  ".join(parts))
        lines.append("")

    # Metro area prices
    if zillow_metro and zillow_metro.get("cities"):
        lines.append(f"🏙️ 都会区房价 (Zillow ZHVI, {zillow_metro.get('period', '')})")
        lines.append("-" * 40)
        for area, data in sorted(zillow_metro["cities"].items(), key=lambda x: x[1]["value"], reverse=True):
            val = f"${int(data['value']):,}"
            parts = [f"  {area:<20} {val:>12}"]
            if "yoy" in data:
                parts.append(f"年同比 {data['yoy']:+.1f}%")
            lines.append("  ".join(parts))
        lines.append("")

    # Mortgage rate
    if mortgage:
        lines.append(f"📈 30年固定利率: {mortgage.get('rate', 'N/A')}% (截至 {mortgage.get('date', '')})")

    return "\n".join(lines) if lines else "暂无数据"
