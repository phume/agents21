import sqlite3
import os

DB_PATH = r'c:\Users\phume\Downloads\agent_S21\aml-agent\backend\aml.db'

def reset_recent():
    if not os.path.exists(DB_PATH):
        print("DB not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get last 20 article IDs
    c.execute('SELECT id FROM articles ORDER BY created_at DESC LIMIT 20')
    rows = c.fetchall()
    
    if not rows:
        print("No articles to delete.")
        return

    ids = [str(r[0]) for r in rows]
    id_str = ",".join(ids)
    
    print(f"Deleting articles: {id_str}")
    
    # Delete entities first (Foreign Key)
    c.execute(f'DELETE FROM entities WHERE article_id IN ({id_str})')
    # Delete articles
    c.execute(f'DELETE FROM articles WHERE id IN ({id_str})')
    
    conn.commit()
    conn.close()
    print("Deleted recent entries. Run fetcher to re-process with LLM.")

if __name__ == "__main__":
    reset_recent()
