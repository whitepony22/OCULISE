import requests

BLYNK_AUTH_TOKEN = "kqY3NQGJaYGQPaLKpZ8GoFCxygYJBl5T"
BASE_URL = f"http://blynk.cloud/external/api"

#Sending Message
url_1 = "https://blynk.cloud/external/api/logEvent"

def message(emergency_message):
    event_code="alert"
    params = {"token": BLYNK_AUTH_TOKEN,
              "code": event_code,
              "description": emergency_message
              }
    try:
        # Sending the alert message
        response = requests.get(url_1, params=params)

        # Check the response status
        if response.status_code == 200:
            print("Message sent successfully!")
        else:
            print(f"Failed to send message. Status code: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def set_led_state(led_state):

    url = f"{BASE_URL}/update?token={BLYNK_AUTH_TOKEN}&V0={led_state}"
    response = requests.get(url)
    if response.status_code == 200:
        print(f"LED {'ON' if led_state == 1 else 'OFF'} successfully.")
    else:
        print("Failed to control the LED. Error:", response.text)


def set_fan_state(fan_state):

    url = f"{BASE_URL}/update?token={BLYNK_AUTH_TOKEN}&V1={fan_state}"
    response = requests.get(url)
    if response.status_code == 200:
        print(f"FAN {'ON' if fan_state == 1 else 'OFF'} successfully.")
    else:
        print("Failed to control the FAN Error:", response.text)

