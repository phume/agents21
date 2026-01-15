# Real-time AML Agent

**Real-time AML Agent** monitors global press releases (DOJ, OFAC, Treasury) to build a dynamic watchlist of emerging financial crime entities. Ideally suited for customer screening, it enables institutions to instantly detect links to high-risk actors before they appear on official sanction lists.

## Features
- **Global Monitoring**: Tracks RSS feeds and scrapes updates from DOJ, FATF, FINTRAC, DHS, and US Treasury.
- **Entity Extraction**: Automatically identifies names and organizations using Regex and optional LLM (Google Gemini).
- **Dynamic Watchlist**: Consolidates findings into a searchable database.
- **Screening Dashboard**: A user-friendly Streamlit interface to search and screen entities.

## Quick Start
1.  `pip install -r requirements.txt`
2.  `python -m streamlit run app.py`
