import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="Real-time AML Agent (DEMO)",
    page_icon="🕵️",
    layout="wide"
)

# Load Static Data (No Database Connection)
@st.cache_data
def load_data():
    if not os.path.exists('demo_entities.csv'):
        return pd.DataFrame(), pd.DataFrame()
    return pd.read_csv('demo_entities.csv'), pd.read_csv('demo_articles.csv')

df_entities, df_articles = load_data()

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2040/2040504.png", width=100)
    st.title("AML Agent (Demo)")
    st.markdown("---")
    st.info("ℹ️ Running in **Demo Mode**. Data is static content.")
    st.markdown("### Monitoring")
    st.markdown("- **Sources**: DOJ, OFAC, FATF, FINTRAC, DHS")
    st.markdown(f"- **Total Entities**: {len(df_entities)}")
    st.markdown(f"- **Total Articles**: {len(df_articles)}")

# Main Content
st.title("🕵️ Real-time AML Emerging Watchlist")
st.markdown("### 🚨 High Priority Entities (Detected by Gemini 2.0)")

# Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("New Entities (24h)", len(df_entities[df_entities['date'] >= pd.Timestamp.now().strftime('%Y-%m-%d')]))
with col2:
    st.metric("High Risks", len(df_entities[df_entities['type'].str.contains('High', case=False, na=False)]))
with col3:
    st.metric("Sources Active", df_articles['source'].nunique() if not df_articles.empty else 0)

# Filter
search = st.text_input("🔍 Search Entities", placeholder="Filter by name or risk type...")
if search and not df_entities.empty:
    df_entities = df_entities[
        df_entities['name'].str.contains(search, case=False, na=False) | 
        df_entities['type'].str.contains(search, case=False, na=False)
    ]

# Display Table
st.dataframe(
    df_entities,
    column_config={
        "url": st.column_config.LinkColumn("Source Link"),
        "type": st.column_config.TextColumn("Risk Classification"),
    },
    use_container_width=True,
    hide_index=True
)

st.markdown("---")
st.markdown("### 📰 Recent Intelligence Reports")

for _, row in df_articles.iterrows():
    with st.expander(f"{row['date']} | {row['source']} | {row['title']}"):
        st.markdown(f"**Source**: [{row['url']}]({row['url']})")
        st.write(row['content'])
