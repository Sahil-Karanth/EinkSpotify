import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import json


load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIST_JSON_PATH = os.path.join(BASE_DIR, "selected_artists.json")

auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

def load_selected_artists():
    try:
        with open(ARTIST_JSON_PATH, "r") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print("Error: output.json not found.")
        return []


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

def get_most_recent_song(artist_id):

    releases = sp.artist_albums(artist_id, album_type='single,album', country='US', limit=50)
    albums = sorted(releases['items'], key=lambda x: x['release_date'], reverse=True)
    
    for album in albums:
        album_id = album['id']
        tracks = sp.album_tracks(album_id)
        if tracks['items']:
            latest_track = tracks['items'][0]
            print(f"\nMost Recent Song: {latest_track['name']}")
            print(f"Spotify URL: {latest_track['external_urls']['spotify']}")
            return
    
    print("No tracks found in latest releases.")