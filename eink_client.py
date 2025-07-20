import requests
import time
from collections import deque
from spotipy_setup import *
from dotenv import load_dotenv
import json
import os
import schedule
from lang_translation import transliterate_mixed

load_dotenv()

MAX_TEXT_LENGTH_ALLOWED = 18
NUM_DISPLAY_ENTRIES = 8
SCREEN_CHAR_WIDTH = 37
SEND_TIME = "15:15"

def authenticate_and_get_token():
    """Authenticate with Firebase and get an ID token"""
    api_key = os.getenv("FIREBASE_API_KEY")
    email = os.getenv("FIREBASE_EMAIL")
    password = os.getenv("FIREBASE_PASSWORD")
    
    auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    
    auth_data = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    
    response = requests.post(auth_url, json=auth_data)
    
    if response.status_code == 200:
        print("FIREBASE AUTH SUCCEEDED")
        return response.json()["idToken"]
    else:
        print(f"Authentication failed: {response.text}")
        return None

def send_message_to_display(message, user_id):

    if len(message) == 0:
        message = "No artists selected!"

    # Get authenticated token
    token = authenticate_and_get_token()
    if not token:
        print("Failed to authenticate with Firebase")
        return

    # Send to Firebase with auth token
    firebase_url_with_auth = f"https://eink-spotify-middleman-default-rtdb.firebaseio.com/messages/from_device/{user_id}.json?auth={token}"
    
    data = {"message": message}
    
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.put(firebase_url_with_auth, data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        print("Success! Message written to Firebase.")
    else:
        print(f"Failed to write to Firebase: {response.status_code}")
        print(response.text)

    esp32_hostname = f"{user_id}-epaper.local"
    url = f"http://{esp32_hostname}/update"
    print(url)

    # ESP32 communication
    print(f"Attempting to send '{message}' to {esp32_hostname}...")
    try:
        # Set a timeout to avoid waiting forever if the device isn't found
        response = requests.get(url, params={'message': message}, timeout=10)
        
        # Check the HTTP response status code
        if response.status_code == 200:
            print("SUCCESS!")
            print(f"--> Response from device: {response.text}")
        else:
            print(f"ERROR: Device responded with status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"FAILED: Could not connect to {esp32_hostname}.")
        print(f"--> Error details: {e}")

def truncate_text(text, max_length):
    if len(text) <= max_length:
        return text
    return f"{text[:max_length - 2]}.."

def create_line_data(artist, song_name):
    """Create a line data dict with properly formatted song and artist"""

    translated_song_name = transliterate_mixed(song_name)
    translated_artist_name = transliterate_mixed(artist["artist_name"])

    displayed_song_name = truncate_text(translated_song_name, MAX_TEXT_LENGTH_ALLOWED)
    truncated_artist = truncate_text(translated_artist_name, MAX_TEXT_LENGTH_ALLOWED)

    return {
        "song": displayed_song_name,
        "artist": truncated_artist,
        "original_song_length": len(translated_song_name)
    }

def calculate_max_song_length(lines_to_display):

    if len(lines_to_display) == 0:
        return 0
    else:
        return max(
            min(line["original_song_length"], MAX_TEXT_LENGTH_ALLOWED)
            for line in lines_to_display
        )

def format_display_message(lines_to_display, max_song_length):

    message = ""
    for line_data in lines_to_display:
        song = line_data["song"]
        artist = line_data["artist"]
        message += truncate_text(f"{song:<{max_song_length}} | {artist}", SCREEN_CHAR_WIDTH)
        message += "\n"
    return message

def check_for_new_releases(lines_to_display, user_id):
    for artist in load_selected_artists(user_id):
        current_song, release_date = get_most_recent_song(artist["artist_id"])
        
        # check if it's new
        if release_date < get_last_checked_date():
            new_line = create_line_data(artist, current_song)
            lines_to_display.appendleft(new_line)

def initial_message_create(lines_to_display, user_id):
    # Load initial data
    for artist in load_selected_artists(user_id):
        song_name, _ = get_most_recent_song(artist["id"])
        line_data = create_line_data(artist, song_name)
        lines_to_display.append(line_data)

        if len(lines_to_display) == NUM_DISPLAY_ENTRIES:
            break

class UserLines:
    def __init__(self, user_id):
        self.user_id = user_id
        self.queue = deque(maxlen=NUM_DISPLAY_ENTRIES)


def main_cron_job(lines_arr):
    print("CRON JOB TIME!")
    # Check for updates
    for lines in lines_arr:
        # modify the queue with new releases
        check_for_new_releases(lines.queue, lines.user_id)
        
        # Calculate formatting and display
        max_song_length = calculate_max_song_length(lines.queue)
        message = format_display_message(lines.queue, max_song_length)
        send_message_to_display(message, lines.user_id)

    update_last_checked_date()

if __name__ == "__main__":

    print("eink client program start")

    lines_arr = [UserLines(USER_IDS[0]), UserLines(USER_IDS[1])]

    # schedule.every().day.at(SEND_TIME).do(main_cron_job, lines_arr=lines_arr)
    schedule.every(1).seconds.do(main_cron_job, lines_arr=lines_arr)

    while True:
        schedule.run_pending()
        time.sleep(1)

