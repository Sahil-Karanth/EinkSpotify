from flask import Flask, render_template, request, redirect, url_for
import json

from spotipy_setup import *

load_dotenv()




# -----------------------------------------------------------------------------#
# helper functions
# -----------------------------------------------------------------------------#







# -----------------------------------------------------------------------------#
# globals functions
# -----------------------------------------------------------------------------#



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
    
    return render_template("artist_input.html", artist_data=artist_data)

@app.route('/add_artist', methods=['POST'])
def add_artist():
    name = request.form.get('name')
    artist_id = request.form.get('id')
    popularity = request.form.get('popularity')
    selected_artists.append({'name': name, 'id': artist_id, 'popularity': popularity})
    return redirect(url_for('home'))

@app.route('/remove_artist/<artist_id>', methods=['POST'])
def remove_artist(artist_id):
    global selected_artists
    selected_artists = [artist for artist in selected_artists if artist['id'] != artist_id]
    return redirect(url_for('home'))


@app.route('/save_artist_change')
def save_artist_change():

    with open(ARTIST_JSON_PATH, "w") as file:
        json.dump(selected_artists, file)

    return "<h3>Artist selection updated!<h3>"

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