import os
from flask import Flask, render_template, request
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

app = Flask(__name__)

def get_possible_artists(artist_name):
    result = sp.search(q=f'artist:{artist_name}', type='artist', limit=10)
    items = result['artists']['items']
    
    if not items:
        return []

    artist_data = []

    for artist in items:
        image_url = artist['images'][0]['url'] if artist['images'] else ""
        artist_data.append((artist['name'], artist['id'], image_url))
    
    return artist_data

@app.route('/', methods=['GET', 'POST'])
def home():
    artist_data_lst = None
    artist_name = None

    if request.method == 'POST':
        artist_name = request.form.get('artistName')
        artist_data_lst = get_possible_artists(artist_name)

    return render_template('artist_input.html', artist_name=artist_name, artist_data=artist_data_lst)

if __name__ == '__main__':
    app.run(port=5000)
