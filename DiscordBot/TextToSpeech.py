# Import the required module for text
# to speech conversion
from gtts import gTTS
from playsound import playsound

def create_sound_file(speech_string, output_filepath):
    myobj = gTTS(text=speech_string, lang='en', slow=False)
    myobj.save(output_filepath)
    return True

