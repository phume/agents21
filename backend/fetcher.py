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
    import database
    import extractor

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

def fetch_rss(source):
    print(f"Fetching RSS: {source['name']} ({source['url']})")
    try:
        feed = feedparser.parse(source['url'])
        for entry in feed.entries:
            title = entry.get('title', 'No Title')
            link = entry.get('link', '')
            # Try to get published date, fallback to now
            pub_date = entry.get('published', entry.get('updated', datetime.now().isoformat()))
            content = entry.get('summary', entry.get('description', ''))
            
            # Combine title + content for better entity extraction
            full_text = f"{title}. {content}"
            entities = extractor.extract_entities(full_text)
            
            saved = database.save_article(source['name'], title, link, pub_date, content, entities)
            if saved:
                print(f"  [NEW] {title}")
    except Exception as e:
        print(f"  [ERROR] {e}")

def fetch_ofac(source):
    print(f"Scraping OFAC: {source['url']}")
    try:
        response = requests.get(source['url'])
        if response.status_code != 200:
            print(f"  [ERROR] Status code {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # OFAC Recent Actions specific structure
        # Usually inside a view or list. We look for rows.
        # This selector is generic based on typical Drupal/Gov sites, might need tuning.
        rows = soup.select('.views-row')
        
        for row in rows:
            # Date
            date_el = row.select_one('time')
            date_text = date_el['datetime'] if date_el and 'datetime' in date_el.attrs else (date_el.text.strip() if date_el else datetime.now().isoformat())
            
            # Link & Title
            link_el = row.select_one('a')
            if not link_el: continue
            
            title = link_el.text.strip()
            href = link_el['href']
            full_link = urljoin(source['url'], href)
            
            # For content, we rely on title since we aren't clicking through yet
            content = title 
            
            entities = extractor.extract_entities(title)
            
            saved = database.save_article(source['name'], title, full_link, date_text, content, entities)
            if saved:
                print(f"  [NEW] {title}")
                
    except Exception as e:
        print(f"  [ERROR] {e}")

def fetch_treasury(source):
    print(f"Scraping US Treasury: {source['url']}")
    try:
        # Treasury press releases page often needs headers to act like a browser
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(source['url'], headers=headers)
        if response.status_code != 200:
            print(f"  [ERROR] Status code {response.status_code}")
            return
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Select rows/items. Based on generic identification of recent items.
        # Looking for generic news listing structure
        # Treasury uses <h3 class="field-content"><a ...>
        
        articles = soup.find_all('h3', class_='field-content')
        if not articles:
             # Fallback for different layout
             articles = soup.select('.views-row h3 a')

        for item in articles:
            link_el = item.find('a') if item.name != 'a' else item
            if not link_el: continue
            
            title = link_el.text.strip()
            href = link_el.get('href')
            full_link = urljoin(source['url'], href)
            
            # Date often in a sibling or parent container. For now defaulting to today if not easily found
            # or fetching from the article page itself (expensive).
            # Let's try to find a date in strict proximity
            date_text = datetime.now().isoformat()
            
            parent = item.find_parent('div')
            if parent:
                time_el = parent.find_previous('time')
                if time_el:
                    date_text = time_el.get('datetime', time_el.text.strip())

            # Fetch inner content for better extraction? 
            # The user wants specific names from inside the page. 
            # We must visit the page to get the list of names.
            try:
                art_resp = requests.get(full_link, headers=headers)
                art_soup = BeautifulSoup(art_resp.content, 'html.parser')
                body_content = art_soup.find('div', class_='field-item') # generic drupal content
                content_text = body_content.get_text() if body_content else title
            except:
                content_text = title

            entities = extractor.extract_entities(content_text)
            
            saved = database.save_article(source['name'], title, full_link, date_text, content_text, entities)
            if saved:
                print(f"  [NEW] {title}")

    except Exception as e:
        print(f"  [ERROR] {e}")

def run():
    print("Starting Fetch Job...")
    database.init_db()
    for source in SOURCES:
        if source['type'] == 'rss':
            fetch_rss(source)
        elif source['type'] == 'scrape':
            fetch_ofac(source)
        elif source['type'] == 'scrape_treasury':
            fetch_treasury(source)
    print("Fetch Job Completed.")

if __name__ == "__main__":
    run()
