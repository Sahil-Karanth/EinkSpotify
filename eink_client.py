import requests
import time
from collections import deque
from spotipy_setup import *

UPDATE_INTERVAL = 1 # ! SMALL FOR TESTING
MAX_TEXT_LENGTH_ALLOWED = 15
NUM_DISPLAY_ENTRIES = 5

# "http://epaper.local/" (mDNS arduino side)
ESP32_HOSTNAME = "epaper.local" 
URL = f"http://{ESP32_HOSTNAME}/update"
def send_message_to_display(message):
    print(f"Attempting to send '{message}' to {ESP32_HOSTNAME}...")
    
    try:
        # Set a timeout to avoid waiting forever if the device isn't found
        response = requests.get(URL, params={'message': message}, timeout=10)
        
        # Check the HTTP response status code
        if response.status_code == 200:
            print("SUCCESS!")
            print(f"--> Response from device: {response.text}")
        else:
            print(f"ERROR: Device responded with status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"FAILED: Could not connect to {ESP32_HOSTNAME}.")
        print(f"--> Error details: {e}")


def truncate_text(text, max_length):
    if len(text) <= max_length:
        return text
    return f"{text[:max_length - 2]}.."

def create_line_data(artist, song_name):
    """Create a line data dict with properly formatted song and artist"""
    displayed_song_name = truncate_text(song_name, MAX_TEXT_LENGTH_ALLOWED)
    truncated_artist = truncate_text(artist["name"], MAX_TEXT_LENGTH_ALLOWED)
    
    return {
        "song": displayed_song_name,
        "artist": truncated_artist,
        "original_song_length": len(song_name)
    }

def calculate_max_song_length(lines_to_display):
    return max(
        min(line["original_song_length"], MAX_TEXT_LENGTH_ALLOWED)
        for line in lines_to_display
    )

def format_display_message(lines_to_display, max_song_length):
    message = ""
    for line_data in lines_to_display:
        song = line_data["song"]
        artist = line_data["artist"]
        message += f"{song:<{max_song_length}} | {artist}\n"
    return message

def check_for_new_releases(lines_to_display):
    for artist in load_selected_artists():
        current_song = get_most_recent_song(artist["id"])
        
        if current_song != artist["most_recent_song"]:
            # New release detected - add to top of display
            new_line = create_line_data(artist, current_song)
            lines_to_display.appendleft(new_line)

if __name__ == "__main__":
    # Initial setup
    lines_to_display = deque(maxlen=NUM_DISPLAY_ENTRIES)

    # Load initial data
    for artist in load_selected_artists():
        song_name = get_most_recent_song(artist["id"])
        line_data = create_line_data(artist, song_name)
        lines_to_display.append(line_data)

        if len(lines_to_display) == NUM_DISPLAY_ENTRIES:
            break
    
    # Main loop
    while True:
        time.sleep(UPDATE_INTERVAL)
        
        # Check for updates
        check_for_new_releases(lines_to_display)
        
        # Calculate formatting and display
        max_song_length = calculate_max_song_length(lines_to_display)
        message = format_display_message(lines_to_display, max_song_length)
        send_message_to_display(message)

        break # ! TESTING
