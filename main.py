from pathlib import Path
from openai import OpenAI

api_key = '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'  # Replace with your actual OpenAI API key
client = OpenAI(api_key=api_key)

speech_file_path = Path(__file__).parent / "speech.mp3"

response = client.audio.speech.create(
  model="tts-1",
  voice="alloy",
  input="Today is a wonderful day to build something people love!"
)

response.stream_to_file(speech_file_path)