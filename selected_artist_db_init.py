import sqlite3

def init_db():
    conn = sqlite3.connect('artists.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS selected_artists (
            artist_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            artist_name TEXT NOT NULL,
            PRIMARY KEY (artist_id, user_id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == '__main__':
    init_db()