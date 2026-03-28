"""Main entry point: fetch data + news → summarize → email."""

import sys

from fetch_news import fetch_articles
from fetch_data import fetch_redfin_data, fetch_mortgage_rate, format_market_summary
from summarize import summarize_articles
from send_email import render_email, send_email


def main():
    print("=== MA Real Estate Digest ===")

    # Step 1: Fetch market data
    print("\n[1/4] Fetching market data...")
    redfin = fetch_redfin_data()
    mortgage = fetch_mortgage_rate()
    market_data = format_market_summary(redfin, mortgage)
    if redfin:
        print("  Redfin data loaded")
    if mortgage:
        print(f"  Mortgage rate: {mortgage.get('rate', 'N/A')}%")

    # Step 2: Fetch news
    print("\n[2/4] Fetching news from RSS feeds...")
    articles = fetch_articles()
    print(f"  Found {len(articles)} relevant articles")

    if not articles and not redfin:
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
