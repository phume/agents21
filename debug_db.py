import sqlite3
import pandas as pd

conn = sqlite3.connect(r'c:\Users\phume\Downloads\agent_S21\aml-agent\backend\aml.db')

print("--- Articles Count ---")
print(pd.read_sql_query("SELECT count(*) FROM articles", conn))

print("\n--- Recent Articles (Top 5) ---")
print(pd.read_sql_query("SELECT id, title, created_at FROM articles ORDER BY created_at DESC LIMIT 5", conn))

print("\n--- Entities Count ---")
print(pd.read_sql_query("SELECT count(*) FROM entities", conn))

print("\n--- Recent Entities (Top 5) ---")
print(pd.read_sql_query("SELECT * FROM entities ORDER BY id DESC LIMIT 5", conn))

conn.close()
