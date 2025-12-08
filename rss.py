import feedparser
import socket
from datetime import datetime
import time

def parse_feed_urls(url_string):
    """
    Parse comma-separated URLs from a string.
    Returns list of cleaned URLs.
    """
    if not url_string:
        return []
    
    # Split by comma and clean each URL
    urls = [url.strip() for url in url_string.split(',')]
    # Filter out empty strings
    urls = [url for url in urls if url]
    
    return urls

def validate_feed(feed_url, timeout=10):
    """
    Validate RSS feed before adding. Returns (valid, error_message).
    Now supports comma-separated URLs for amalgamation.
    """
    try:
        # Basic URL validation
        if not feed_url or not isinstance(feed_url, str):
            return False, "URL must be a string"
        
        feed_url = feed_url.strip()
        
        if not feed_url:
            return False, "URL cannot be empty"
        
        # Parse multiple URLs if comma-separated
        urls = parse_feed_urls(feed_url)
        
        if not urls:
            return False, "No valid URLs found"
        
        # Validate each URL
        for i, url in enumerate(urls):
            if not url.startswith(('http://', 'https://')):
                return False, f"URL {i+1} must start with http:// or https://"
            
            # Set socket timeout for the request
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(timeout)
            
            try:
                # Try to fetch the feed
                feed = feedparser.parse(
                    url, 
                    request_headers={'User-Agent': 'NewsViewerApp/1.0'}
                )
            finally:
                # Restore original timeout
                socket.setdefaulttimeout(old_timeout)
            
            # Check for severe parsing errors
            if getattr(feed, "bozo", False):
                exception_type = feed.bozo_exception.__class__.__name__
                if exception_type not in ('NonXMLContentType', 'CharacterEncodingOverride'):
                    return False, f"URL {i+1} - Invalid feed format: {feed.bozo_exception}"
            
            # Check if feed has entries
            if not feed.entries:
                return False, f"URL {i+1} - Feed has no entries or is empty"
            
            # Check if feed has basic structure
            if not hasattr(feed, 'feed'):
                return False, f"URL {i+1} - Invalid feed structure"
        
        if len(urls) > 1:
            return True, f"Valid amalgamated feed ({len(urls)} sources)"
        else:
            return True, "Valid feed"
        
    except socket.timeout:
        return False, "Connection timeout - feed took too long to respond"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def get_entry_published_time(entry):
    """
    Extract published time from an entry and convert to timestamp.
    Tries multiple date fields and returns current time if none found.
    """
    # Try different date fields in order of preference
    date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']
    
    for field in date_fields:
        if hasattr(entry, field) and getattr(entry, field):
            try:
                time_struct = getattr(entry, field)
                return time.mktime(time_struct)
            except (TypeError, ValueError):
                continue
    
    # If no valid date found, return current time (will sort to top)
    return time.time()

def extract_domain_from_url(url):
    """
    Extract a clean domain name from URL for display.
    E.g., 'https://techcrunch.com/feed/' -> 'techcrunch.com'
    """
    try:
        # Remove protocol
        domain = url.split('://')[-1]
        # Remove path
        domain = domain.split('/')[0]
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return url

def fetch_feed_entries(feed_url, max_entries=100):
    """
    Fetch feed entries using feedparser. 
    Now supports comma-separated URLs for amalgamation.
    Returns merged and sorted list of entries.
    """
    # Ensure feed_url is a string, not a list
    if isinstance(feed_url, (list, tuple)):
        raise Exception(f"feed_url must be a string, not {type(feed_url).__name__}")
    
    if not isinstance(feed_url, str):
        raise Exception(f"feed_url must be a string, got {type(feed_url).__name__}")
    
    # Parse multiple URLs
    urls = parse_feed_urls(feed_url)
    
    if not urls:
        raise Exception("No valid URLs to fetch")
    
    all_entries = []
    errors = []
    
    # Fetch from each URL
    for url in urls:
        try:
            feed = feedparser.parse(url, request_headers={'User-Agent': 'NewsViewerApp/1.0'})
            
            # Check for severe parsing errors
            if getattr(feed, "bozo", False):
                exception_type = feed.bozo_exception.__class__.__name__
                if exception_type not in ('NonXMLContentType', 'CharacterEncodingOverride'):
                    errors.append(f"{url}: {feed.bozo_exception}")
                    continue
            
            # Extract clean domain name for display
            domain_name = extract_domain_from_url(url)
            
            # Add source info to each entry for tracking
            for entry in feed.entries:
                entry._source_url = url
                entry._source_domain = domain_name
                all_entries.append(entry)
                
        except Exception as e:
            errors.append(f"{url}: {str(e)}")
            continue
    
    if not all_entries and errors:
        raise Exception(f"Failed to fetch any feeds. Errors: {'; '.join(errors)}")
    
    # Sort all entries by publication time (newest first)
    all_entries.sort(key=get_entry_published_time, reverse=True)
    
    # Return up to max_entries
    return all_entries[:max_entries]