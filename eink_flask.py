import sqlite3
import sys
from datetime import datetime

from flask import Flask, redirect, render_template, request, url_for

from spotipy_setup import *

load_dotenv()

# -----------------------------------------------------------------------------
# globals
# -----------------------------------------------------------------------------

app = Flask(__name__)
user_id = None
selected_artists = []
selected_ids_set = set() # to prevent duplicate artist adds

# -----------------------------------------------------------------------------
# flask routes
# -----------------------------------------------------------------------------


@app.route("/", methods=["GET"])
def home():
    return render_template("home.html", selected_artists=selected_artists)


@app.route("/select_artists", methods=["GET", "POST"])
def select_artists():
    artist_data = []

    if request.method == "POST":
        artist_name = request.form.get("artistName")
        artist_data = get_possible_artists(artist_name)

    return render_template("artist_input.html", artist_data=artist_data)


@app.route("/add_artist", methods=["POST"])
def add_artist():
    name = request.form.get("name")
    artist_id = request.form.get("id")

    if artist_id not in selected_ids_set:
        selected_artists.append({"artist_name": name, "artist_id": artist_id})
        selected_ids_set.add(artist_id)

    return redirect(url_for("home"))


@app.route("/remove_artist/<artist_id>", methods=["POST"])
def remove_artist(artist_id):
    global selected_artists
    selected_artists = [
        artist for artist in selected_artists if artist["artist_id"] != artist_id
    ]
    return redirect(url_for("home"))


@app.route("/save_artist_change")
def save_artist_change():
    global user_id
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Delete only this user's artists
    cursor.execute("DELETE FROM selected_artists WHERE user_id = ?", (user_id,))

    # Re-insert all artists for this user
    for artist in selected_artists:
        cursor.execute(
            """
            INSERT INTO selected_artists (artist_id, user_id, artist_name)
            VALUES (?, ?, ?)
            """,
            (
                artist["artist_id"],
                user_id,
                artist["artist_name"],
            ),
        )

    conn.commit()
    conn.close()

    return "<h3>Artist selection updated!</h3>"


# ------------------------------------------------------------------------------
# main
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Incorrect usage must provide a user_id (sahil/nihal): python app.py <user_id>"
        )
        sys.exit(1)

    if sys.argv[1] not in USER_IDS:
        print("invalid user_id - must be 'sahil' or 'nihal'")
        sys.exit(1)

    user_id = sys.argv[1]
    selected_artists = load_selected_artists(user_id)

    for artist in selected_artists:
        if artist['artist_id'] not in selected_ids_set:
            selected_ids_set.add(artist['artist_id'])

    print("note if port is busy, run `npx kill-port 5000`")

    app.run(port=5000)
