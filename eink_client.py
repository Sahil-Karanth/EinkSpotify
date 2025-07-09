import time
import json
from spotipy_setup import *


UPDATE_INTERVAL = 5 # ! small for testing

if __name__ == '__main__':
    while True:

        print("checking for new songs")

        with open("selected_artists.json", "r") as file:
            selected_artists_dict = json.load(file)

        for artist in selected_artists_dict:
            get_most_recent_song()

        time.sleep(UPDATE_INTERVAL)