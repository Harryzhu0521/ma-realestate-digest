"""Main entry point: fetch data + news → summarize → email."""

import sys

from fetch_news import fetch_articles
from fetch_data import fetch_zillow_data, fetch_redfin_summary, fetch_mortgage_rate, format_market_summary
from summarize import summarize_articles
from send_email import render_email, send_email


def main():
    print("=== MA Real Estate Digest ===")

    # Step 1: Fetch market data
    print("\n[1/4] Fetching market data...")
    zillow = fetch_zillow_data()
    if zillow:
        print(f"  Zillow data loaded: {len(zillow.get('cities', {}))} cities")
    redfin = fetch_redfin_summary()
    if redfin and redfin.get("median_sale_price"):
        print(f"  Redfin data loaded")
    mortgage = fetch_mortgage_rate()
    if mortgage:
        print(f"  Mortgage rate: {mortgage.get('rate', 'N/A')}%")
    market_data = format_market_summary(zillow, redfin, mortgage)

    # Step 2: Fetch news
    print("\n[2/4] Fetching news from RSS feeds...")
    articles = fetch_articles()
    print(f"  Found {len(articles)} relevant articles")

    if not articles and not zillow and not redfin:
        print("  No articles or data found. Exiting.")
        sys.exit(0)

    # Step 3: Summarize
    if articles:
        print(f"\n[3/4] Generating AI summaries ({len(articles)} articles)...")
        articles = summarize_articles(articles)
        print("  Summaries done!")
    else:
        print("\n[3/4] No articles to summarize, skipping...")

    # Step 4: Send
    print("\n[4/4] Rendering and sending email...")
    html = render_email(articles, market_data)
    send_email(html, len(articles))

    print("\n=== Done! ===")


if __name__ == "__main__":
    main()
