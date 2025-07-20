import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import sqlite3
from datetime import datetime, timezone

load_dotenv()

# -----------------------------------------------------------------------------#
# globals
# -----------------------------------------------------------------------------#

DB_PATH = "artists.db"
USER_IDS = ["sahil", "nanna"]

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

# -----------------------------------------------------------------------------#
# spotify helper functions
# -----------------------------------------------------------------------------#

def load_selected_artists(user_id):

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT artist_name, artist_id
            FROM selected_artists
            WHERE user_id = ?
        """, (user_id,))

        db_tuples = c.fetchall()

        artists = []

        for db_tuple in db_tuples:
            
            artist = {
                'artist_name': db_tuple[0],
                'artist_id': db_tuple[1],
            }
            
            artists.append(artist)

            print(artist['artist_name'])

        return artists


def get_possible_artists(artist_name):
    result = sp.search(q=f'artist:{artist_name}', type='artist', limit=10)
    items = result['artists']['items']
    
    if not items:
        return []

    sorted_items = sorted(items, key=lambda x: x['popularity'], reverse=True)

    artist_data = []
    for artist in sorted_items:
        image_url = artist['images'][0]['url'] if artist['images'] else ""
        artist_data.append((artist['name'], artist['id'], image_url, artist['popularity']))

    return artist_data


def __format_release_date(date_str, prec):
    if (prec == "day"):
        return date_str
    elif (prec == "month"):
        return f"{date_str}-01"
    elif (prec == "year"):
        return f"{date_str}-01-01"
    else:
        raise Exception("BAD PRECISION FROM SPOTIFY")

def get_most_recent_song(artist_id):
    
    releases = sp.artist_albums(artist_id, album_type='single,album', country='US', limit=50)
    albums = sorted(releases['items'], key=lambda x: x['release_date'], reverse=True)
    
    for album in albums:
        album_id = album['id']
        tracks = sp.album_tracks(album_id)
        if tracks['items']:
            latest_track = tracks['items'][0]
            # Return tuple with song name and album release date
            return latest_track['name'], __format_release_date(album['release_date'], album['release_date_precision'])
    
    # Return None if no tracks found
    return None, None

def get_last_checked_date():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT value FROM metadata WHERE key = 'last_checked_date'")
        row = c.fetchone()
        if row:
            return row[0]
        else:
            return None
        
def update_last_checked_date():

    new_date_str = datetime.now(timezone.utc).date().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            ('last_checked_date', new_date_str)
        )
        conn.commit()