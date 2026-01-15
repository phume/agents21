import sqlite3
import pandas as pd
import os

# Ensure backend exists or path is correct
DB_PATH = r'c:\Users\phume\Downloads\agent_S21\aml-agent\backend\aml.db'

def export_data():
    conn = sqlite3.connect(DB_PATH)
    
    # Export Entities (Joined with metadata for the dashboard)
    print("Exporting Entities...")
    query_entities = """
        SELECT e.name, e.type, a.source, a.date, a.title, a.url 
        FROM entities e 
        JOIN articles a ON e.article_id = a.id 
        ORDER BY a.date DESC
    """
    df_entities = pd.read_sql_query(query_entities, conn)
    df_entities.to_csv('demo_entities.csv', index=False)
    print(f"Saved demo_entities.csv ({len(df_entities)} rows)")

    # Export Articles
    print("Exporting Articles...")
    query_articles = "SELECT * FROM articles ORDER BY date DESC"
    df_articles = pd.read_sql_query(query_articles, conn)
    df_articles.to_csv('demo_articles.csv', index=False)
    print(f"Saved demo_articles.csv ({len(df_articles)} rows)")
    
    conn.close()

if __name__ == "__main__":
    export_data()
