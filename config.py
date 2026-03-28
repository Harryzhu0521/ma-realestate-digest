import os

# --- RSS Feeds: MA Real Estate News & Policy ---
RSS_FEEDS = [
    # MA real estate news via Google News
    {"name": "MA房产新闻", "url": "https://news.google.com/rss/search?q=Massachusetts+real+estate+housing&hl=en-US&gl=US&ceid=US:en"},
    {"name": "MA房产政策", "url": "https://news.google.com/rss/search?q=Massachusetts+housing+policy+OR+zoning+OR+%22building+permit%22&hl=en-US&gl=US&ceid=US:en"},
    {"name": "MA房产税/法规", "url": "https://news.google.com/rss/search?q=Massachusetts+property+tax+OR+%22real+estate+law%22+OR+%22housing+regulation%22&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Boston房产", "url": "https://news.google.com/rss/search?q=Boston+real+estate+OR+housing+market&hl=en-US&gl=US&ceid=US:en"},
    {"name": "MA开发项目", "url": "https://news.google.com/rss/search?q=Massachusetts+%22new+development%22+OR+%22construction+project%22+OR+%22building+permit%22+housing&hl=en-US&gl=US&ceid=US:en"},

    # National housing news (affects MA)
    {"name": "全美房产", "url": "https://news.google.com/rss/search?q=US+housing+market+OR+mortgage+rate+OR+%22home+prices%22&hl=en-US&gl=US&ceid=US:en"},

    # HousingWire
    {"name": "HousingWire", "url": "https://www.housingwire.com/feed/"},
]

# --- Filter keywords ---
KEYWORDS = [
    # MA specific
    "Massachusetts", "MA", "Boston", "Cambridge", "Somerville", "Newton",
    "Brookline", "Worcester", "Springfield", "Quincy", "Medford",
    "Waltham", "Framingham", "Lowell", "Brockton", "New Bedford",
    # Policy & regulation
    "zoning", "building permit", "housing policy", "property tax",
    "regulation", "affordable housing", "rent control", "MBTA communities",
    "housing act", "development approval", "variance",
    # Market
    "home price", "house price", "median price", "housing market",
    "listing", "inventory", "days on market", "pending sales",
    "new construction", "housing starts", "building permits",
    # Finance
    "mortgage rate", "interest rate", "housing supply",
    "home sales", "existing home", "new home",
    # Development
    "land sale", "development", "developer", "construction",
    "condo", "townhouse", "multifamily", "mixed-use",
]

# --- Redfin Data Center URLs (MA metro areas) ---
# These are CSV download URLs for monthly data
REDFIN_METROS = [
    {"name": "Boston", "region_id": "11"},
    {"name": "Worcester", "region_id": "49"},
    {"name": "Springfield", "region_id": "44"},
]

# --- FRED API (for mortgage rates etc.) ---
FRED_SERIES = {
    "mortgage_30yr": "MORTGAGE30US",  # 30-Year Fixed Rate
    "housing_starts": "HOUST",         # Housing Starts
    "building_permits": "PERMIT",      # Building Permits
}

# --- Gemini ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"

# --- Email ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT", "")

# --- Digest settings ---
MAX_ARTICLES = 20
