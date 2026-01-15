import sqlite3
import pandas as pd

conn = sqlite3.connect(r'c:\Users\phume\Downloads\agent_S21\aml-agent\backend\aml.db')

print("--- Summary ---")
try:
    n_articles = pd.read_sql_query("SELECT count(*) FROM articles", conn).iloc[0,0]
    n_entities = pd.read_sql_query("SELECT count(*) FROM entities", conn).iloc[0,0]
    print(f"Total Articles: {n_articles}")
    print(f"Total Entities: {n_entities}")
except:
    print("Could not get counts.")

print("\n--- Top High-Risk Entities (LLM Detected) ---")
query_entities = """
SELECT 
    e.name, 
    e.type, 
    a.date
FROM entities e
JOIN articles a ON e.article_id = a.id
ORDER BY a.date DESC
LIMIT 15
"""
try:
    df_e = pd.read_sql_query(query_entities, conn)
    print(df_e.to_markdown(index=False))
except Exception as e:
    print(e)

print("\n--- Article Date Check (Oldest vs Newest) ---")
try:
    dates = pd.read_sql_query("SELECT min(date), max(date) FROM articles", conn)
    print(dates.to_markdown(index=False))
except:
    pass

conn.close()
