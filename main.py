from flask import Flask, render_template, request, redirect, url_for
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

app = Flask(__name__)

selected_artists = []

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

@app.route('/', methods=['GET'])
def home():
    return render_template('home.html', selected_artists=selected_artists)

@app.route('/select_artists', methods=['GET', 'POST'])
def select_artists():
    artist_data = []

    if request.method == 'POST':
        artist_name = request.form.get('artistName')
        artist_data = get_possible_artists(artist_name)
    
    return render_template('artist_input.html', artist_data=artist_data)

@app.route('/add_artist', methods=['POST'])
def add_artist():
    name = request.form.get('name')
    artist_id = request.form.get('id')
    popularity = request.form.get('popularity')
    selected_artists.append({'name': name, 'id': artist_id, 'popularity': popularity})
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(port=5000)
