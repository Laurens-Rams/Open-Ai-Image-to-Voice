from flask import Flask, render_template, request, jsonify
import os
import threading
from main import process_image_async, client

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Ensure this directory exists
imgur_client_id = '0580ace497b71fe'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_image', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['image']
    prompt = request.form.get('prompt', '')  # Retrieve the prompt from the form
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filename)

    def callback(audio_path, analysis_text):
        return jsonify({
            'audio_path': audio_path,
            'analysis_text': analysis_text
        })

    threading.Thread(target=process_image_async, args=(imgur_client_id, filename, prompt, callback)).start()
    return jsonify({'message': 'Processing image...'}), 202

if __name__ == '__main__':
    app.run(debug=True)
