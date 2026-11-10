import sqlite3

connection = sqlite3.connect("database/internguide.db")
tables = connection.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()

print("Database tables:", tables)
connection.close()
