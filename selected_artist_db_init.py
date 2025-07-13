import sqlite3

def init_db():
    conn = sqlite3.connect('artists.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS selected_artists (
            artist_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            image_url TEXT,
            most_recent_song TEXT,
            last_updated TEXT,
            PRIMARY KEY (artist_id, user_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == '__main__':
    init_db()