import cv2
import time
import requests
import base64
import threading
from openai import OpenAI
from pathlib import Path
import pygame
def upload_image_to_imgur(filename, client_id):
    headers = {'Authorization': f'Client-ID {client_id}'}
    with open(filename, 'rb') as image_file:
        image_b64 = base64.b64encode(image_file.read())
    data = {'image': image_b64, 'type': 'base64'}
    response = requests.post('https://api.imgur.com/3/upload', headers=headers, data=data)
    if response.status_code == 200:
        return response.json()['data']['link']
    else:
        return None

def analyze_image_with_openai(client, image_url):
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[{"role": "user", "content": ["This is a snapshot of a video. Create a short voiceover script in the style of David Attenborough. Only include the narration.", {"type": "image_url", "image_url": {"url": image_url}}]}],
        max_tokens=200
    )
    return response.choices[0].message

def text_to_speech(client, text, filename):
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=text
    )
    response.stream_to_file(filename)
def play_audio(filename):
    # Initialize pygame mixer
    pygame.mixer.init()
    # Load the audio file
    pygame.mixer.music.load(filename)
    # Play the audio file
    pygame.mixer.music.play()
    # Wait for playback to finish
    while pygame.mixer.music.get_busy():
        time.sleep(1)

def process_image(client, imgur_client_id, img_filename):
    image_url = upload_image_to_imgur(img_filename, imgur_client_id)
    if image_url:
        analysis_result = analyze_image_with_openai(client, image_url)
        print("Analysis Result:", analysis_result)

        text = analysis_result.content if hasattr(analysis_result, 'content') else str(analysis_result)

        print("Text to be converted to speech:", text)

        limited_text = ' '.join(text.split()[:30])

        # Convert text to speech and save
        speech_filename = Path(__file__).parent / f'speech_output_{int(time.time())}.mp3'
        text_to_speech(client, limited_text, speech_filename)

        # Play the audio
        play_audio(str(speech_filename))

# Main script
api_key = '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'
client = OpenAI(api_key=api_key)
imgur_client_id = '0580ace497b71fe'

cap = cv2.VideoCapture(0)
last_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow('Webcam Feed', frame)

    current_time = time.time()
    if current_time - last_time >= 5:
        last_time = current_time
        img_filename = 'webcam_image.jpg'
        cv2.imwrite(img_filename, frame)

        threading.Thread(target=process_image, args=(client, imgur_client_id, img_filename)).start()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()