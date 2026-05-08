import sqlite3
try:
    conn = sqlite3.connect('d:/Software/ASKBot/data/askbot.db')
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE generatedpost ADD COLUMN hashtags VARCHAR DEFAULT ''")
    cursor.execute("ALTER TABLE generatedpost ADD COLUMN ai_prompt_used VARCHAR DEFAULT ''")
    cursor.execute("ALTER TABLE generatedpost ADD COLUMN layout_used VARCHAR DEFAULT ''")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS postmetrics (
        id INTEGER PRIMARY KEY,
        post_id INTEGER NOT NULL,
        impressions INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        engagement_rate FLOAT DEFAULT 0.0,
        fetched_at DATETIME NOT NULL
    )
    """)
    conn.commit()
    print("Migration successful")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
