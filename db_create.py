import sqlite3
 
conn = sqlite3.connect("db.db") 
cursor = conn.cursor()
 
cursor.execute("""CREATE TABLE IF NOT EXISTS Users (
                    id	INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                    login TEXT NOT NULL UNIQUE,
                    password TEXT
                    );
               """)

cursor.execute("""CREATE TABLE IF NOT EXISTS Urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    short_url TEXT UNIQUE,
                    custom_short_url TEXT UNIQUE,
                    type TEXT NOT NULL,
                    times_opened INTEGER DEFAULT 0 NOT NULL,
                    user_id INTEGER REFERENCES Users(login)
                    );
               """)