import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'aml.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Articles Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            date TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Entities Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            article_id INTEGER,
            FOREIGN KEY(article_id) REFERENCES articles(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def article_exists(url):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT 1 FROM articles WHERE url = ?', (url,))
    result = c.fetchone()
    conn.close()
    return result is not None

def save_article(source, title, url, date, content, entities):
    if article_exists(url):
        return False
        
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(
            'INSERT INTO articles (source, title, url, date, content) VALUES (?, ?, ?, ?, ?)',
            (source, title, url, date, content)
        )
        article_id = c.lastrowid
        
        for entity in entities:
             c.execute(
                'INSERT INTO entities (name, type, article_id) VALUES (?, ?, ?)',
                (entity['name'], entity['type'], article_id)
            )
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_recent_articles(limit=50):
    conn = get_db_connection()
    articles = conn.execute('SELECT * FROM articles ORDER BY date DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return articles

def get_recent_entities(limit=50):
    conn = get_db_connection()
    query = '''
        SELECT e.name, e.type, a.source, a.date, a.title, a.url 
        FROM entities e 
        JOIN articles a ON e.article_id = a.id 
        ORDER BY a.date DESC 
        LIMIT ?
    '''
    entities = conn.execute(query, (limit,)).fetchall()
    conn.close()
    return entities
