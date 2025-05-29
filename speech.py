# speech.py
import pyttsx3

# Initialize the pyttsx3 engine
engine = pyttsx3.init()

# Define a function to speak a given phrase
def speak_phrase(phrase):
    engine.say(phrase)
    engine.runAndWait()

# Optional: You can customize the speech rate or voice properties
def set_speech_rate(rate):
    engine.setProperty('rate', rate)

def set_voice(voice_id):
    engine.setProperty('voice', voice_id)