import pandas as pd
import sqlite3
import os

try:
    # Check CSV first if it exists (Demo Mode)
    if os.path.exists('demo_articles.csv'):
        print("Reading from CSV...")
        df = pd.read_csv('demo_articles.csv')
    else:
        # Fallback to DB
        print("Reading from DB...")
        conn = sqlite3.connect(r'c:\Users\phume\Downloads\agent_S21\aml-agent\backend\aml.db')
        df = pd.read_sql_query("SELECT * FROM articles", conn)
        conn.close()

    print("\n--- Source Distribution ---")
    print(df['source'].value_counts().to_markdown())
    
    print("\n--- Recent Articles by Source ---")
    print(df.groupby('source').head(2)[['source', 'date', 'title']].to_markdown(index=False))

except Exception as e:
    print(e)
