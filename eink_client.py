import requests
import time
from spotipy_setup import *

INDENT = "          "

# "http://epaper.local/" (mDNS arduino side)
ESP32_HOSTNAME = "epaper.local" 
URL = f"http://{ESP32_HOSTNAME}/update"
def send_message_to_display(message):
    """Sends a message to the ESP32 via an mDNS hostname."""
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


if __name__ == "__main__":
    lines_to_display = []
    max_song_length = 0

    for artist in load_selected_artists():
        song_name = get_most_recent_song(artist["id"])
        
        if len(song_name) > max_song_length:
            max_song_length = len(song_name)
            
        lines_to_display.append({"song": song_name, "artist": artist["name"]})

    message = ""
    for line_data in lines_to_display:
        song = line_data["song"]
        artist = line_data["artist"]
        
        message += f"{song:<{max_song_length + 2}} | {artist}\n"

    print(message)
    send_message_to_display(message)