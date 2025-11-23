import feedparser

def fetch_feed_entries(feed_url, max_entries=100):
    """
    Fetch feed entries using feedparser. Returns list of entries (possibly empty).
    Raises on severe parse errors.
    """
    feed = feedparser.parse(feed_url, request_headers={'User-Agent': 'NewsViewerApp/1.0'})
    if getattr(feed, "bozo", False) and feed.bozo_exception.__class__.__name__ not in ('NonXMLContentType', 'CharacterEncodingOverride'):
        # propagate the error so UI can show messagebox
        raise Exception(f"Malformed feed: {feed.bozo_exception}")
    return feed.entries[:max_entries]
