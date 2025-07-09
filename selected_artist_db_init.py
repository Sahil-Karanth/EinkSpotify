import sqlite3

def init_db():
    conn = sqlite3.connect('artists.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS selected_artists (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            image_url TEXT,
            most_recent_song TEXT,
            last_updated TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == '__main__':
    init_db()