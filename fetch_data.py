"""Fetch real estate market data from free public sources."""

import io
import csv

import requests


def fetch_zillow_data() -> dict:
    """Fetch Zillow Home Value Index (ZHVI) for MA cities."""
    # ZHVI All Homes - Metro level (small CSV ~2MB)
    url = "https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"

    ma_metros = {
        "Boston, MA": "Boston",
        "Worcester, MA": "Worcester",
        "Springfield, MA": "Springfield",
        "Providence, RI": "Providence/Fall River",  # includes SE MA
        "Cambridge, MA": "Cambridge",
    }

    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()

        reader = csv.DictReader(io.StringIO(resp.text))
        fieldnames = reader.fieldnames
        # Last 2 date columns for current and previous month
        date_cols = [c for c in fieldnames if c and len(c) == 10 and c[4] == '-']
        date_cols.sort()

        if len(date_cols) < 13:
            return {}

        latest_col = date_cols[-1]
        prev_month_col = date_cols[-2]
        year_ago_col = date_cols[-13] if len(date_cols) >= 13 else None

        results = {}
        for row in reader:
            region = row.get("RegionName", "")
            for key, label in ma_metros.items():
                if key in region:
                    current = row.get(latest_col, "")
                    prev = row.get(prev_month_col, "")
                    year_ago = row.get(year_ago_col, "") if year_ago_col else ""

                    if current:
                        entry = {"value": float(current), "date": latest_col}
                        if prev:
                            mom = (float(current) - float(prev)) / float(prev) * 100
                            entry["mom"] = mom
                        if year_ago:
                            yoy = (float(current) - float(year_ago)) / float(year_ago) * 100
                            entry["yoy"] = yoy
                        results[label] = entry

        return {"cities": results, "period": latest_col}

    except Exception as e:
        print(f"  Warning: Failed to fetch Zillow data: {e}")
        return {}


def fetch_redfin_summary() -> dict:
    """Fetch Redfin weekly housing market summary for MA via their lighter weekly data."""
    url = "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/weekly_housing_market_data_most_recent.tsv000.gz"

    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()

        import gzip
        content = gzip.decompress(resp.content).decode("utf-8")
        reader = csv.DictReader(io.StringIO(content), delimiter="\t")

        ma_data = []
        for row in reader:
            if row.get("state_code") == "MA" and row.get("property_type") == "All Residential":
                region = row.get("region", "")
                # Only keep state-level or major metro data
                if row.get("region_type") in ("state", "metro"):
                    ma_data.append(row)

        if not ma_data:
            return {}

        # Prefer state-level data
        state_rows = [r for r in ma_data if r.get("region_type") == "state"]
        row = state_rows[0] if state_rows else ma_data[0]

        return {
            "period": row.get("period_end", "N/A"),
            "median_sale_price": row.get("median_sale_price", ""),
            "median_sale_price_yoy": row.get("median_sale_price_yoy", ""),
            "median_list_price": row.get("median_list_price", ""),
            "median_list_price_yoy": row.get("median_list_price_yoy", ""),
            "homes_sold": row.get("homes_sold", ""),
            "homes_sold_yoy": row.get("homes_sold_yoy", ""),
            "new_listings": row.get("new_listings", ""),
            "new_listings_yoy": row.get("new_listings_yoy", ""),
            "inventory": row.get("inventory", ""),
            "inventory_yoy": row.get("inventory_yoy", ""),
            "months_of_supply": row.get("months_of_supply", ""),
            "median_dom": row.get("median_dom", ""),
            "avg_sale_to_list": row.get("avg_sale_to_list", ""),
        }
    except Exception as e:
        print(f"  Warning: Failed to fetch Redfin data: {e}")
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


def _fmt_price(val: str) -> str:
    try:
        return f"${int(float(val)):,}"
    except (ValueError, TypeError):
        return val or "N/A"


def _fmt_yoy(val: str) -> str:
    try:
        return f"{float(val)*100:+.1f}%"
    except (ValueError, TypeError):
        return val or "N/A"


def _fmt_pct(val: str) -> str:
    try:
        return f"{float(val)*100:.1f}%"
    except (ValueError, TypeError):
        return val or "N/A"


def _fmt_num(val: str) -> str:
    try:
        return f"{int(float(val)):,}"
    except (ValueError, TypeError):
        return val or "N/A"


def format_market_summary(zillow: dict, redfin: dict, mortgage: dict) -> str:
    """Format all market data into a readable summary."""
    lines = []

    # --- Zillow city price data ---
    if zillow and zillow.get("cities"):
        lines.append(f"🏘️ 各城市房价指数 (Zillow ZHVI, {zillow.get('period', '')})")
        lines.append("")
        for city, data in sorted(zillow["cities"].items(), key=lambda x: x[1]["value"], reverse=True):
            val = f"${int(data['value']):,}"
            parts = [f"  {city}: {val}"]
            if "mom" in data:
                parts.append(f"月环比 {data['mom']:+.1f}%")
            if "yoy" in data:
                parts.append(f"年同比 {data['yoy']:+.1f}%")
            lines.append(" | ".join(parts))
        lines.append("")

    # --- Redfin state summary ---
    if redfin and redfin.get("median_sale_price"):
        lines.append(f"📊 麻州整体市场 (Redfin, 截至 {redfin.get('period', 'N/A')})")
        lines.append("")
        lines.append(f"  🏠 中位售价: {_fmt_price(redfin['median_sale_price'])} (同比 {_fmt_yoy(redfin.get('median_sale_price_yoy', ''))})")
        lines.append(f"  🏷️ 中位挂牌价: {_fmt_price(redfin.get('median_list_price', ''))} (同比 {_fmt_yoy(redfin.get('median_list_price_yoy', ''))})")

        if redfin.get("inventory"):
            lines.append(f"  📦 活跃库存: {_fmt_num(redfin['inventory'])} 套 (同比 {_fmt_yoy(redfin.get('inventory_yoy', ''))})")
        if redfin.get("months_of_supply"):
            lines.append(f"  ⏳ 库存月数: {redfin['months_of_supply']} 个月")
        if redfin.get("median_dom"):
            lines.append(f"  📆 中位在售天数: {redfin['median_dom']} 天")
        if redfin.get("avg_sale_to_list"):
            lines.append(f"  💰 成交价/挂牌价: {_fmt_pct(redfin['avg_sale_to_list'])}")
        if redfin.get("homes_sold"):
            lines.append(f"  🔑 成交量: {_fmt_num(redfin['homes_sold'])} 套 (同比 {_fmt_yoy(redfin.get('homes_sold_yoy', ''))})")
        if redfin.get("new_listings"):
            lines.append(f"  🆕 新挂牌: {_fmt_num(redfin['new_listings'])} 套 (同比 {_fmt_yoy(redfin.get('new_listings_yoy', ''))})")
        lines.append("")

    # --- Mortgage rate ---
    if mortgage:
        lines.append(f"📈 30年固定利率: {mortgage.get('rate', 'N/A')}% (截至 {mortgage.get('date', '')})")

    return "\n".join(lines) if lines else "暂无数据"
