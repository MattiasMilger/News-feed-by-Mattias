import feedparser
import socket

def validate_feed(feed_url, timeout=10):
    """
    Validate RSS feed before adding. Returns (valid, error_message).
    Checks for:
    - Valid URL format
    - Accessible endpoint
    - Valid RSS/Atom feed
    - Non-empty entries
    """
    try:
        # Basic URL validation
        if not feed_url or not isinstance(feed_url, str):
            return False, "URL must be a string"
        
        feed_url = feed_url.strip()
        
        if not feed_url:
            return False, "URL cannot be empty"
        
        if not feed_url.startswith(('http://', 'https://')):
            return False, "URL must start with http:// or https://"
        
        # Set socket timeout for the request
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        
        try:
            # Try to fetch the feed
            feed = feedparser.parse(
                feed_url, 
                request_headers={'User-Agent': 'NewsViewerApp/1.0'}
            )
        finally:
            # Restore original timeout
            socket.setdefaulttimeout(old_timeout)
        
        # Check for severe parsing errors
        if getattr(feed, "bozo", False):
            exception_type = feed.bozo_exception.__class__.__name__
            if exception_type not in ('NonXMLContentType', 'CharacterEncodingOverride'):
                return False, f"Invalid feed format: {feed.bozo_exception}"
        
        # Check if feed has entries
        if not feed.entries:
            return False, "Feed has no entries or is empty"
        
        # Check if feed has basic structure
        if not hasattr(feed, 'feed'):
            return False, "Invalid feed structure"
        
        return True, "Valid feed"
        
    except socket.timeout:
        return False, "Connection timeout - feed took too long to respond"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def fetch_feed_entries(feed_url, max_entries=100):
    """
    Fetch feed entries using feedparser. Returns list of entries (possibly empty).
    Raises on severe parse errors.
    """
    # Ensure feed_url is a string, not a list
    if isinstance(feed_url, (list, tuple)):
        raise Exception(f"feed_url must be a string, not {type(feed_url).__name__}")
    
    if not isinstance(feed_url, str):
        raise Exception(f"feed_url must be a string, got {type(feed_url).__name__}")
    
    feed = feedparser.parse(feed_url, request_headers={'User-Agent': 'NewsViewerApp/1.0'})
    if getattr(feed, "bozo", False) and feed.bozo_exception.__class__.__name__ not in ('NonXMLContentType', 'CharacterEncodingOverride'):
        # propagate the error so UI can show messagebox
        raise Exception(f"Malformed feed: {feed.bozo_exception}")
    return feed.entries[:max_entries]