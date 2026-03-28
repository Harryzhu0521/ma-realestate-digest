"""Fetch MA real estate news from RSS feeds."""

import re
from datetime import datetime, timedelta, timezone

import feedparser

from config import RSS_FEEDS, KEYWORDS, MAX_ARTICLES


def _matches_keywords(text: str) -> bool:
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in KEYWORDS)


def _clean_html(raw: str) -> str:
    return re.sub(r"<[^>]+>", "", raw).strip()


def _parse_date(entry) -> datetime:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def fetch_articles() -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    seen_titles = set()
    articles = []

    for feed_cfg in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_cfg["url"])
        except Exception:
            continue

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            if not title:
                continue

            title_norm = re.sub(r"\s+", " ", title.lower())
            if title_norm in seen_titles:
                continue

            summary_raw = entry.get("summary", "") or entry.get("description", "")
            summary_text = _clean_html(summary_raw)
            link = entry.get("link", "")
            pub_date = _parse_date(entry)

            if pub_date < cutoff:
                continue
            if not _matches_keywords(title + " " + summary_text):
                continue

            seen_titles.add(title_norm)
            articles.append({
                "title": title,
                "link": link,
                "summary": summary_text[:1000],
                "source": feed_cfg["name"],
                "published": pub_date.isoformat(),
            })

    articles.sort(key=lambda a: a["published"], reverse=True)
    return articles[:MAX_ARTICLES]
