from flask import Flask, render_template, request, redirect, url_for
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import json

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# TODO make capitals
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
artist_json_path = os.path.join(BASE_DIR, "selected_artists.json")

# -----------------------------------------------------------------------------#
# helper functions
# -----------------------------------------------------------------------------#

def load_selected_artists():
    try:
        with open(artist_json_path, "r") as file:
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

# -----------------------------------------------------------------------------#
# globals functions
# -----------------------------------------------------------------------------#

auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

app = Flask(__name__)

selected_artists = load_selected_artists()


# -----------------------------------------------------------------------------#
# flask routes
# -----------------------------------------------------------------------------#

@app.route('/', methods=['GET'])
def home():
    return render_template('home.html', selected_artists=selected_artists)

@app.route('/select_artists', methods=['GET', 'POST'])
def select_artists():
    artist_data = []

    if request.method == 'POST':
        artist_name = request.form.get('artistName')
        artist_data = get_possible_artists(artist_name)
    
    select_artists_path = os.path.join(BASE_DIR, "templates", "artist_input.html")

    return render_template(select_artists_path, artist_data=artist_data)

@app.route('/add_artist', methods=['POST'])
def add_artist():
    name = request.form.get('name')
    artist_id = request.form.get('id')
    popularity = request.form.get('popularity')
    selected_artists.append({'name': name, 'id': artist_id, 'popularity': popularity})
    return redirect(url_for('home'))

@app.route('/send_to_esp32') # TODO rename this as I'm no longer sending artists to the esp32 just strings to write
def send_to_esp32():
    print("Sending selected artists to ESP32...")

    with open(artist_json_path, "w") as file:
        json.dump(selected_artists, file)

    return "Data sent to ESP32!"

if __name__ == '__main__':

    while True:
        inp = input("Enter command (launch/quit): ").strip().lower()
        
        if inp == "launch":
            app.run(port=5000)
        elif inp == "quit":
            print("Exiting program.")
            break
        else:
            print("Unknown command. Please enter 'launch' or 'quit'.")