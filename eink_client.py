import time
from spotipy_setup import *
from datetime import datetime
import serial


UPDATE_INTERVAL = 5 # ! small for testing
SERIAL_PORT = 'COM3'  # ! CHANGEME
BAUD_RATE = 115200

def send_to_esp32(data):
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
        time.sleep(2)  # Wait for ESP32 to reset after serial connection opens
        ser.write((data + '\n').encode('utf-8'))
        print("Sent:", data)
        response = ser.readline().decode('utf-8').strip()
        print("Response:", response)



if __name__ == '__main__':
    while True:
        print("checking for new songs")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        selected_artists = load_selected_artists()

        for artist in selected_artists:
            latest_song = get_most_recent_song(artist['id'])
            
            # if new song, update db and eink
            if latest_song != artist['most_recent_song']:
                cursor.execute(
                """
                UPDATE selected_artists
                SET most_recent_song = ?, last_updated = ?
                WHERE id = ?
                """, (latest_song, datetime.now().isoformat(), artist['id']))

                # update eink display
                send_to_esp32(f"{latest_song}|{artist['name']}")


        time.sleep(UPDATE_INTERVAL)