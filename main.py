import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

# Authenticate
auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

def choose_artist(artist_name):
    result = sp.search(q=f'artist:{artist_name}', type='artist', limit=10)
    items = result['artists']['items']
    
    if not items:
        print("Artist not found.")
        return None
    
    print("Artists found:")
    for i, artist in enumerate(items):
        print(f"{i+1}. {artist['name']} (ID: {artist['id']})")
        if artist['images']:
            print(f"   Image URL: {artist['images'][0]['url']}")
        else:
            print("   No image available")
    
    choice = input("Enter the number of the correct artist (or 0 to cancel): ")
    if not choice.isdigit() or int(choice) == 0 or int(choice) > len(items):
        print("Cancelled or invalid choice.")
        return None
    
    selected_artist = items[int(choice) - 1]
    print(f"Selected artist: {selected_artist['name']}")
    return selected_artist

# Function to get the most recent song
def get_most_recent_song(artist_name):
    artist = choose_artist(artist_name)
    if not artist:
        return
    
    artist_id = artist['id']
    
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

get_most_recent_song("Jay Z")
