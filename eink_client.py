import requests
import time

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
    time.sleep(3)
    test_message = f"Hello from Python at {time.strftime('%H:%M:%S')}"
    send_message_to_display(test_message)
