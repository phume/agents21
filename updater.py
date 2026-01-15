import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from urllib.parse import urljoin
try:
    from backend import database
    from backend import extractor
except ImportError:
  from backend import database, extractor

# Define Sources
SOURCES = [
    {
        'name': 'DOJ',
        'type': 'rss',
        'url': 'https://www.justice.gov/feeds/opa/justice-news.xml'
    },
    {
        'name': 'FATF',
        'type': 'rss',
        'url': 'https://www.fatf-gafi.org/en/pages/rss.xml'
    },
    {
        'name': 'FINTRAC',
        'type': 'rss',
        'url': 'https://www.fintrac-canafe.gc.ca/rss-eng.xml'
    },
    {
        'name': 'DHS',
        'type': 'rss',
        'url': 'https://www.dhs.gov/news-releases/rss.xml'
    },
    {
        'name': 'OFAC',
        'type': 'scrape',
        'url': 'https://ofac.treasury.gov/recent-actions'
    },
    {
        'name': 'US_Treasury',
        'type': 'scrape_treasury',
        'url': 'https://home.treasury.gov/news/press-releases'
    }
]

# Global Headers for WAF Bypass
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_rss(source):
    print(f"Fetching RSS: {source['name']} ({source['url']})")
    try:
        # Fetch with headers to bypass WAF/403
        response = requests.get(source['url'], headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"  [ERROR] RSS Fetch failed: {response.status_code}")
            return

        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            print(f"  [WARN] No entries found for {source['name']}. (Content-Length: {len(response.content)})")
            
        for entry in feed.entries:
            title = entry.get('title', 'No Title')
            link = entry.get('link', '')
            # Try to get published date, fallback to now
            pub_date = entry.get('published', entry.get('updated', datetime.now().isoformat()))
            content = entry.get('summary', entry.get('description', ''))
            
            # Combine title + content for better entity extraction
            full_text = f"{title}. {content}"
            
            # OPTIMIZATION: Check if exists to save LLM cost
            if database.article_exists(link):
                continue

            entities = extractor.extract_entities(full_text)
            
            # Filter: Only save if entities found
            if not entities:
                 # print(f"    [SKIPRSS] {title[:30]}...")
                 continue

            saved = database.save_article(source['name'], title, link, pub_date, content, entities)
            if saved:
                print(f"  [NEW] {title}")
    except Exception as e:
        print(f"  [ERROR] {e}")

from dateutil import parser

def should_skip_date(date_str):
    """
    Checks if date is older than June 1, 2025.
    """
    try:
        # Robust parsing with dateutil
        dt = parser.parse(date_str)
        # User requested cutoff: June 2025
        cutoff = datetime(2025, 6, 1)
        
        # print(f"    [Date Check] {date_str} -> {dt} (Cutoff: {cutoff}) -> {dt < cutoff}")
        return dt < cutoff
    except Exception as e:
        # If parsing fails, don't skip yet (safety)
        # print(f"    [Date Parse Error] {date_str}: {e}")
        return False

def fetch_ofac(source, historic=False):
    print(f"Scraping OFAC: {source['url']} (Historic: {historic})")
    
    # Simple pagination loop
    max_pages = 150 if historic else 1
    
    for page in range(max_pages):
        page_url = f"{source['url']}?page={page}" if page > 0 else source['url']
        print(f"  Fetching Page {page}...")
        time.sleep(1.0) # Rate limiting
        
        try:
            response = requests.get(page_url, headers=HEADERS)
            # print(f"    Status: {response.status_code}")
            if response.status_code != 200: 
                print(f"    [STOP] Read failed: {response.status_code}")
                break

            soup = BeautifulSoup(response.content, 'html.parser')
            rows = soup.select('.views-row')
            
            # print(f"    Rows found: {len(rows)}")
            
            if not rows: 
                print("    [STOP] No rows found on this page. Dumping HTML sample:")
                print(soup.prettify()[:500])
                break
            
            for row in rows:
                # Improved Date Extraction
                date_text = None
                date_el = row.select_one('time')
                if date_el:
                    date_text = date_el.get('datetime') or date_el.text.strip()
                
                # Fallback: Try finding date in text
                if not date_text:
                    import re
                    # Look for date patterns like "January 14, 2026" or "1/14/2026"
                    text_content = row.get_text(" ", strip=True)
                    date_match = re.search(r'([A-Z][a-z]+ \d{1,2}, \d{4})', text_content) 
                    if date_match:
                        date_text = date_match.group(1)

                if date_text:
                    # print(f"    [Date Found] {date_text}")
                    pass
                else:
                    print(f"    [WARN] Date Missing for item. Defaulting to NOW.")
                    # print(row.prettify()[:200]) 
                    date_text = datetime.now().isoformat()
                
                # Historic Check
                if historic and should_skip_date(date_text):
                    print("    [STOP] Reached cutoff date (Dec 2024).")
                    return 

                link_el = row.select_one('a')
                if not link_el: continue
                
                title = link_el.text.strip()
                href = link_el['href']
                full_link = urljoin(source['url'], href)
                content = title 
                
                # OPTIMIZATION: Check if exists to save LLM cost
                if database.article_exists(full_link):
                    # print(f"  [SKIP] {title}") 
                    continue

                entities = extractor.extract_entities(title)
                
                # Filter: Only save if entities found
                if not entities:
                    print(f"    [SKIP - No Risks] {title[:50]}...")
                    continue

                saved = database.save_article(source['name'], title, full_link, date_text, content, entities)
                if saved:
                    print(f"  [NEW] {title} ({len(entities)} entities)")
            
            print(f"  Finished Page {page}. Moving to next...")

        except Exception as e:
            print(f"  [ERROR] Page {page} failed: {e}")
            # Don't break on one page error
            continue

def fetch_treasury(source, historic=False):
    print(f"Scraping US Treasury: {source['url']} (Historic: {historic})")
    # Headers now global
    
    max_pages = 150 if historic else 1
    
    for page in range(max_pages):
        page_url = f"{source['url']}?page={page}" if page > 0 else source['url']
        print(f"  Fetching Page {page}...")

        try:
            response = requests.get(page_url, headers=HEADERS)
            if response.status_code != 200: break
                
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find_all('h3', class_='field-content')
            if not articles:
                 articles = soup.select('.views-row h3 a')

            if not articles: break

            for item in articles:
                link_el = item.find('a') if item.name != 'a' else item
                if not link_el: continue
                
                title = link_el.text.strip()
                href = link_el.get('href')
                full_link = urljoin(source['url'], href)
                
                date_text = datetime.now().isoformat()
                parent = item.find_parent('div')
                if parent:
                    time_el = parent.find_previous('time')
                    if time_el:
                        date_text = time_el.get('datetime', time_el.text.strip())
                
                # Historic Check
                if historic and should_skip_date(date_text):
                    print("    [STOP] Reached cutoff date (Dec 2024).")
                    return

                # OPTIMIZATION: Check if exists to save LLM cost
                if database.article_exists(full_link):
                    # print(f"  [SKIP] {title}")
                    continue

                # Fetch inner content
                try:
                    art_resp = requests.get(full_link, headers=headers)
                    art_soup = BeautifulSoup(art_resp.content, 'html.parser')
                    body_content = art_soup.find('div', class_='field-item') 
                    content_text = body_content.get_text() if body_content else title
                except:
                    content_text = title

                entities = extractor.extract_entities(content_text)
                
                # Filter: Only save if entities found
                if not entities:
                    print(f"    [SKIP - No Risks] {title[:50]}...")
                    continue

                saved = database.save_article(source['name'], title, full_link, date_text, content_text, entities)
                if saved:
                    print(f"  [NEW] {title} ({len(entities)} entities)")

        except Exception as e:
            print(f"  [ERROR] {e}")
            break

def fetch_doj(source, historic=False):
    print(f"Scraping DOJ: {source['url']} (Historic: {historic})")
    max_pages = 20 if historic else 1
    
    for page in range(max_pages):
        # DOJ uses query param ?page=X
        page_url = f"{source['url']}?page={page}" if page > 0 else source['url']
        print(f"  Fetching Page {page}...")
        time.sleep(1.0)

        try:
            response = requests.get(page_url, headers=HEADERS)
            if response.status_code != 200:
                print(f"    [STOP] Failed: {response.status_code}")
                break

            soup = BeautifulSoup(response.content, 'html.parser')
            # Look for Views Rows
            rows = soup.select('.views-row')
            if not rows:
                print("    [STOP] No rows found.")
                break
            
            for row in rows:
                # Extract Title & Link
                link_el = row.select_one('.views-field-title a')
                if not link_el: continue
                
                title = link_el.text.strip()
                href = link_el.get('href')
                full_link = urljoin(source['url'], href)
                
                # Extract Date
                date_text = datetime.now().isoformat()
                date_el = row.select_one('.views-field-created time')
                if date_el:
                    date_text = date_el.get('datetime', date_el.text.strip())

                # Check Cutoff
                if historic and should_skip_date(date_text):
                     print("    [STOP] Reached cutoff date.")
                     return

                # Check Existence
                if database.article_exists(full_link):
                    continue

                # Content (Description)
                body_el = row.select_one('.views-field-body')
                content = body_el.text.strip() if body_el else title
                
                # Extract
                entities = extractor.extract_entities(title + ". " + content)
                if not entities:
                     # print(f"    [SKIP] {title[:30]}")
                     continue

                saved = database.save_article(source['name'], title, full_link, date_text, content, entities)
                if saved:
                    print(f"  [NEW] {title}")

        except Exception as e:
            print(f"  [ERROR] DOJ Page {page}: {e}")
            break

def run():
    print("Starting Fetch Job...")
    database.init_db()
    
    # Updated Sources map
    for source in SOURCES:
        if source['name'] == 'DOJ':
             # Override URL for scraping if it's still the RSS one
             source['url'] = 'https://www.justice.gov/news'
             fetch_doj(source, historic=True)
        elif source['name'] == 'FATF':
             # FATF is hard to scrape generic news, keep RSS check or try specific page? 
             # For now, let's skip FATF scraping as it's complex/dynamic. 
             # Attempt RSS again just in case, or skip.
             # fetch_rss(source)
             print("Skipping FATF (RSS Dead, Scraper TODO)")
        elif source['type'] == 'rss':
            fetch_rss(source)
        elif source['type'] == 'scrape':
            fetch_ofac(source, historic=True)
        elif source['type'] == 'scrape_treasury':
            fetch_treasury(source, historic=True)
    
    print("Fetch Job Completed.")

if __name__ == "__main__":
    run()
