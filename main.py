import cv2
import time
import requests
import base64
import threading
import pygame


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


cap.release()
cv2.destroyAllWindows()