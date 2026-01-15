import sqlite3
import os

DB_PATH = r'c:\Users\phume\Downloads\agent_S21\aml-agent\backend\aml.db'

def wipe_db():
    if not os.path.exists(DB_PATH):
        print("DB not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("Wiping all data...")
    c.execute('DELETE FROM entities')
    c.execute('DELETE FROM articles')
    
    conn.commit()
    conn.close()
    print("Database wiped clean.")

if __name__ == "__main__":
    wipe_db()
