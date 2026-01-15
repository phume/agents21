import streamlit as st
import pandas as pd
from backend import database
# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2040/2040504.png", width=100) # Placeholder icon
    st.title("AML Agent Control")
    st.markdown("---")
    
    st.markdown("### Monitoring")
    st.markdown("- **Sources**: DOJ, OFAC, FATF, FINTRAC, DHS")
    st.markdown("- **Status**: System Active")
    st.info("Data updates run automatically in the background via `updater.py`.")

# Main Content
st.title("🕵️ Real-time AML Emerging Watchlist")
st.markdown("Monitoring global press releases for emerging financial crime entities and red flags.")

# Initialize DB on first load (safe to call multiple times)
database.init_db()

# Fetch Data (Increased limit to show historical November data)
recent_entities = database.get_recent_entities(limit=500)
recent_articles = database.get_recent_articles(limit=200)

# Metrics
col1, col2 = st.columns(2)
with col1:
    st.metric("Entities Detected (24h)", len(recent_entities))
with col2:
    st.metric("Articles Scanned", len(recent_articles))

st.markdown("---")

# Tabs
tab1, tab2 = st.tabs(["📋 Emerging Entities", "📰 News Feed"])

with tab1:
    st.subheader("Extracted Entities & Organizations")
    if recent_entities:
        df_entities = pd.DataFrame(recent_entities, columns=['Name', 'Type', 'Source', 'Date', 'Article Title', 'URL'])
        
        # Search/Filter
        search = st.text_input("Search Entities", placeholder="Filter by name...")
        if search:
            df_entities = df_entities[df_entities['Name'].str.contains(search, case=False) | df_entities['Article Title'].str.contains(search, case=False)]

        st.dataframe(
            df_entities,
            column_config={
                "URL": st.column_config.LinkColumn("Source Link"),
                "Date": st.column_config.DatetimeColumn("Date Detected", format="D MMM YYYY, HH:mm")
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No entities detected yet. Click 'Refresh Data Now' in the sidebar to start.")

with tab2:
    st.subheader("Recent Press Releases")
    if recent_articles:
        df_articles = pd.DataFrame(recent_articles, columns=['ID', 'Source', 'Title', 'URL', 'Date', 'Content', 'Created At'])
        # Simplified view
        df_display = df_articles[['Date', 'Source', 'Title', 'URL']]
        
        st.dataframe(
            df_display,
            column_config={
                "URL": st.column_config.LinkColumn("Read Article"),
                "Date": st.column_config.TextColumn("Published Date")
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No articles found.")
