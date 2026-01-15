import sqlite3
import pandas as pd

conn = sqlite3.connect(r'c:\Users\phume\Downloads\agent_S21\aml-agent\backend\aml.db')

print("--- Date Range in Articles ---")
try:
    df = pd.read_sql_query("SELECT min(date), max(date), count(*) FROM articles", conn)
    print(df.to_markdown())
except Exception as e:
    print(e)
    
print("\n--- Sample Dates (Oldest 10) ---")
try:
    df = pd.read_sql_query("SELECT id, date, source FROM articles ORDER BY date ASC LIMIT 10", conn)
    print(df.to_markdown())
except:
    pass

conn.close()
