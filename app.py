# app.py
from flask import Flask, render_template, request, jsonify
from transformers import AutoProcessor, PaliGemmaForConditionalGeneration, TextIteratorStreamer
import torch
from PIL import Image
import requests
from io import BytesIO
from huggingface_hub import login
from dotenv import load_dotenv
import os
from threading import Thread

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Hugging Face authentication
HF_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
if not HF_TOKEN:
    raise ValueError("HUGGINGFACE_TOKEN not found in .env file")
login(token=HF_TOKEN)

# Model configuration
model_id = "google/paligemma-3b-mix-224"
model_cache_path = os.getenv('MODEL_CACHE_PATH', os.path.join(os.getcwd(), "model_cache"))
model_dir = os.path.join(model_cache_path, model_id.split("/")[-1])

# Create cache directory if it doesn't exist
os.makedirs(model_cache_path, exist_ok=True)

# Check if model exists in the cache
if not os.path.exists(model_dir) or not os.listdir(model_dir):
    print(f"Model not found in cache. Downloading model to {model_dir}...")
    from huggingface_hub import snapshot_download
    snapshot_download(repo_id=model_id, local_dir=model_dir, token=HF_TOKEN)
    print("Model downloaded successfully.")
else:
    print(f"Using cached model from {model_dir}")

# Load model and processor from local directory
model = PaliGemmaForConditionalGeneration.from_pretrained(model_dir)
processor = AutoProcessor.from_pretrained(model_dir)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    prompt = request.form['prompt']
    image_source = request.form['image_source']
    
    if image_source == 'url':
        image_url = request.form['image_url']
        response = requests.get(image_url)
        raw_image = Image.open(BytesIO(response.content))
    else:
        image_file = request.files['image_file']
        raw_image = Image.open(image_file)

    inputs = processor(prompt, raw_image, return_tensors="pt")
    
    streamer = TextIteratorStreamer(processor.tokenizer, skip_prompt=True)
    generation_kwargs = dict(inputs, streamer=streamer, max_new_tokens=100)

    def generate():
        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()
        for text in streamer:
            yield text

    return app.response_class(generate(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)