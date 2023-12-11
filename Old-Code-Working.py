import cv2
import time
import requests
import base64
import threading
import pygame
from openai import OpenAI
from pathlib import Path
from mutagen.mp3 import MP3  # New import for checking MP3 length

from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=api_key)

pygame.mixer.init()

first_run = True

def upload_image_to_imgur(filename, client_id):
    headers = {'Authorization': f'Client-ID {client_id}'}
    with open(filename, 'rb') as image_file:
        image_b64 = base64.b64encode(image_file.read())
    data = {'image': image_b64, 'type': 'base64'}

    for attempt in range(3):
        try:
            response = requests.post('https://api.imgur.com/3/upload', headers=headers, data=data)
            if response.status_code == 200:
                print("Image uploaded successfully.")
                return response.json()['data']['link']
            else:
                print(f"Failed to upload image: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"Error during image upload: {e}")
        time.sleep(1)

    print("Failed to upload image after several attempts.")
    return None


def analyze_image_with_openai(client, image_url):
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[{"role": "user", "content": ["This is a snapshot of a video. Create a short voiceover script in the style of David Attenborough. Only include the narration. The second sentence should already focus on the action that is performed."
, {"type": "image_url", "image_url": {"url": image_url, "detail": "high"}}]}],
        max_tokens=150
    )
    return response.choices[0].message

# possible prompts:
# Tell me what object I'm holding in my hands. Tell me what's the text on the object say and what I could use it for.
# Analyze the following artwork and provide a critique focusing on its style, color usage, composition, and emotional impact. Consider the elements of art such as line, shape, form, space, texture, and value. Discuss how these elements contribute to the overall aesthetic and meaning of the piece. Also, speculate about the possible artistic influences and the era it might belong to if relevant

def text_to_speech_elevenlabs(text, filename, elevenlabs_api_key):
    url = "https://api.elevenlabs.io/v1/text-to-speech/ABfOeM3ERCjGV6vqOoSg"
    payload = {"text": text}
    headers = {
        "xi-api-key": elevenlabs_api_key,
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    if response.status_code == 200:
        # Assuming the API returns the audio file directly
        with open(filename, 'wb') as file:
            file.write(response.content)
        return True
    else:
        print(f"Error in TTS request: {response.status_code}, {response.text}")
        return False


def get_mp3_length(filename):
    audio = MP3(filename)
    return audio.info.length


def play_audio(filename):
    # Load and play the audio file
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

def process_image_async(client, imgur_client_id, img_filename, callback):
    def thread_function():
        try:
            image_url = upload_image_to_imgur(img_filename, imgur_client_id)
            if image_url:
                analysis_result = analyze_image_with_openai(client, image_url)
                text = analysis_result.content if hasattr(analysis_result, 'content') else str(analysis_result)

                # Convert text to speech and save
                speech_filename = Path(__file__).parent / f'speech_output_{int(time.time())}.mp3'
                text_to_speech_elevenlabs(text, speech_filename, "af078375fb276aa85b61e20c185945c4")


                callback(str(speech_filename))
            else:
                callback(None)
        except Exception as e:
            print(f"Error in thread: {e}")
            callback(None)

    threading.Thread(target=thread_function).start()

def on_audio_ready(filename):
    global next_audio_file
    next_audio_file = filename
    if filename:
        print(f"Audio file {filename} is ready.")


# Main script
client = OpenAI(api_key=api_key)
imgur_client_id = '0580ace497b71fe'


cap = cv2.VideoCapture(0)
time.sleep(2)  # Allow time for webcam to initialize
frame_ready = True
next_audio_file = None

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame from webcam.")
        continue
    cv2.imshow('Webcam Feed', frame)
    def is_valid_image(frame):
        return not (frame.max() == frame.min())

    # In the main loop, before processing the image
    if frame_ready and not next_audio_file:
        if is_valid_image(frame):
            img_filename = 'webcam_image.jpg'
            cv2.imwrite(img_filename, frame)
            print("Processing new frame...")
            process_image_async(client, imgur_client_id, img_filename, on_audio_ready)
            frame_ready = False
        else:
            print("Invalid frame captured.")

    if next_audio_file and not pygame.mixer.music.get_busy():
        play_audio(next_audio_file)
        audio_length = get_mp3_length(next_audio_file)
        threading.Timer(audio_length, lambda: globals().update(frame_ready=True)).start()

        next_audio_file = None
        frame_ready = True

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Exiting...")
        break

cap.release()
cv2.destroyAllWindows()

