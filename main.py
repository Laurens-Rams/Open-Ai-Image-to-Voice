import requests
from openai import OpenAI
from pathlib import Path
import os
import base64
import time

from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')

client = OpenAI(api_key=api_key)

def upload_image_to_imgur(filename, client_id):
    headers = {'Authorization': f'Client-ID {client_id}'}
    with open(filename, 'rb') as image_file:
        image_b64 = base64.b64encode(image_file.read())
    data = {'image': image_b64, 'type': 'base64'}

    for attempt in range(3):
        try:
            response = requests.post('https://api.imgur.com/3/upload', headers=headers, data=data)
            if response.status_code == 200:
                return response.json()['data']['link']
            else:
                print(f"Failed to upload image: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"Error during image upload: {e}")
        time.sleep(1)

    return None

def analyze_image_with_openai(client, image_url, prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{"role": "user", "content": [prompt, {"type": "image_url", "image_url": {"url": image_url, "detail": "high"}}]}],
            max_tokens=150
        )
        return response.choices[0].message
    except Exception as e:
        print(f"Exception in analyze_image_with_openai: {e}")
        return None

def text_to_speech_elevenlabs(text, filename):
    url = "https://api.elevenlabs.io/v1/text-to-speech/ABfOeM3ERCjGV6vqOoSg"
    payload = {"text": text}
    headers = {
        "xi-api-key": elevenlabs_api_key,
        "Content-Type": "application/json"
    }
    try:
        response = requests.request("POST", url, json=payload, headers=headers)
        if response.status_code == 200:
            with open(filename, 'wb') as file:
                file.write(response.content)
            return True
        else:
            print(f"Error in TTS request: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print(f"Exception in text_to_speech_elevenlabs: {e}")
        return False


def process_image_async(imgur_client_id, img_filename, prompt, callback):
    try:
        image_url = upload_image_to_imgur(img_filename, imgur_client_id)
        if image_url:
            analysis_result = analyze_image_with_openai(client, image_url, prompt)
            if analysis_result:
                speech_filename = Path('static/audio') / f'speech_output_{int(time.time())}.mp3'
                if text_to_speech_elevenlabs(analysis_result, speech_filename):
                    callback(str(speech_filename), analysis_result)
                else:
                    callback(None, None)
            else:
                callback(None, None)
        else:
            callback(None, None)
    except Exception as e:
        print(f"Error in processing: {e}")
        callback(None, None)