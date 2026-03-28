"""Fetch real estate market data from free public sources."""

import io
import csv
from datetime import datetime, timezone

import requests


def fetch_redfin_data() -> dict:
    """Fetch latest MA housing data from Redfin Data Center."""
    url = "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/state_market_tracker.tsv000.gz"

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()

        import gzip
        content = gzip.decompress(resp.content).decode("utf-8")
        reader = csv.DictReader(io.StringIO(content), delimiter="\t")

        ma_data = []
        for row in reader:
            if row.get("state_code") == "MA":
                ma_data.append(row)

        if not ma_data:
            return {}

        # Get the most recent period
        ma_data.sort(key=lambda r: r.get("period_end", ""), reverse=True)
        latest = ma_data[0]

        return {
            "period": latest.get("period_end", "N/A"),
            "median_sale_price": latest.get("median_sale_price", "N/A"),
            "median_sale_price_yoy": latest.get("median_sale_price_yoy", "N/A"),
            "homes_sold": latest.get("homes_sold", "N/A"),
            "homes_sold_yoy": latest.get("homes_sold_yoy", "N/A"),
            "inventory": latest.get("inventory", "N/A"),
            "inventory_yoy": latest.get("inventory_yoy", "N/A"),
            "months_of_supply": latest.get("months_of_supply", "N/A"),
            "median_dom": latest.get("median_dom", "N/A"),
            "avg_sale_to_list": latest.get("avg_sale_to_list", "N/A"),
            "new_listings": latest.get("new_listings", "N/A"),
            "new_listings_yoy": latest.get("new_listings_yoy", "N/A"),
        }
    except Exception as e:
        print(f"  Warning: Failed to fetch Redfin data: {e}")
        return {}


def fetch_mortgage_rate() -> dict:
    """Fetch latest 30-year mortgage rate from FRED (no API key needed for this endpoint)."""
    try:
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23e1e9f0&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=1168&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=MORTGAGE30US&scale=left&cosd=2024-01-01&coed=2030-01-01&line_color=%234572a7&link_values=false&line_style=solid&mark_type=none&mw=3&lw=2&ost=-99999&oet=99999&mma=0&fml=a&fq=Weekly%2C+Ending+Thursday&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date=2030-01-01&revision_date=2030-01-01&nd=1971-04-02"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()

        lines = resp.text.strip().split("\n")
        if len(lines) < 2:
            return {}

        # Get last row
        last_line = lines[-1]
        parts = last_line.split(",")
        if len(parts) >= 2:
            return {
                "date": parts[0],
                "rate": parts[1],
            }
    except Exception as e:
        print(f"  Warning: Failed to fetch mortgage rate: {e}")

    return {}


def format_market_summary(redfin: dict, mortgage: dict) -> str:
    """Format market data into a readable summary string for the email."""
    lines = []

    if redfin:
        lines.append(f"📅 数据截至: {redfin.get('period', 'N/A')}")
        lines.append("")

        # Price
        price = redfin.get("median_sale_price", "N/A")
        price_yoy = redfin.get("median_sale_price_yoy", "N/A")
        try:
            price_fmt = f"${int(float(price)):,}"
            yoy_fmt = f"{float(price_yoy)*100:+.1f}%" if price_yoy != "N/A" else "N/A"
        except (ValueError, TypeError):
            price_fmt = price
            yoy_fmt = price_yoy
        lines.append(f"🏠 中位售价: {price_fmt} (同比 {yoy_fmt})")

        # Inventory
        inv = redfin.get("inventory", "N/A")
        inv_yoy = redfin.get("inventory_yoy", "N/A")
        try:
            inv_fmt = f"{int(float(inv)):,}"
            inv_yoy_fmt = f"{float(inv_yoy)*100:+.1f}%" if inv_yoy != "N/A" else "N/A"
        except (ValueError, TypeError):
            inv_fmt = inv
            inv_yoy_fmt = inv_yoy
        lines.append(f"📦 活跃库存: {inv_fmt} 套 (同比 {inv_yoy_fmt})")

        # Supply
        mos = redfin.get("months_of_supply", "N/A")
        lines.append(f"⏳ 库存月数: {mos} 个月")

        # DOM
        dom = redfin.get("median_dom", "N/A")
        lines.append(f"📆 中位在售天数: {dom} 天")

        # Sale to list
        stl = redfin.get("avg_sale_to_list", "N/A")
        try:
            stl_fmt = f"{float(stl)*100:.1f}%"
        except (ValueError, TypeError):
            stl_fmt = stl
        lines.append(f"💰 成交价/挂牌价: {stl_fmt}")

        # Sales volume
        sold = redfin.get("homes_sold", "N/A")
        sold_yoy = redfin.get("homes_sold_yoy", "N/A")
        try:
            sold_fmt = f"{int(float(sold)):,}"
            sold_yoy_fmt = f"{float(sold_yoy)*100:+.1f}%" if sold_yoy != "N/A" else "N/A"
        except (ValueError, TypeError):
            sold_fmt = sold
            sold_yoy_fmt = sold_yoy
        lines.append(f"🔑 成交量: {sold_fmt} 套 (同比 {sold_yoy_fmt})")

        # New listings
        nl = redfin.get("new_listings", "N/A")
        nl_yoy = redfin.get("new_listings_yoy", "N/A")
        try:
            nl_fmt = f"{int(float(nl)):,}"
            nl_yoy_fmt = f"{float(nl_yoy)*100:+.1f}%" if nl_yoy != "N/A" else "N/A"
        except (ValueError, TypeError):
            nl_fmt = nl
            nl_yoy_fmt = nl_yoy
        lines.append(f"🆕 新挂牌: {nl_fmt} 套 (同比 {nl_yoy_fmt})")

    if mortgage:
        lines.append("")
        lines.append(f"📈 30年固定利率: {mortgage.get('rate', 'N/A')}% ({mortgage.get('date', '')})")

    return "\n".join(lines) if lines else "暂无数据"
