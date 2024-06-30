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
import numpy as np

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

def process_image(image):
    # Convert to RGB if it's not
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize the image to a standard size
    image = image.resize((224, 224))
    
    # Convert to numpy array
    image_array = np.array(image)
    
    # Ensure the image is in the correct format (H, W, C)
    if image_array.shape[0] == 3:
        image_array = np.transpose(image_array, (1, 2, 0))
    
    return image_array

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    prompt = request.form['prompt']
    image_source = request.form['image_source']
    
    try:
        if image_source == 'url':
            image_url = request.form['image_url']
            response = requests.get(image_url)
            raw_image = Image.open(BytesIO(response.content))
        else:
            image_file = request.files['image_file']
            raw_image = Image.open(image_file)
        
        processed_image = process_image(raw_image)
        
        inputs = processor(prompt, images=processed_image, return_tensors="pt")
        
        streamer = TextIteratorStreamer(processor.tokenizer, skip_prompt=True)
        generation_kwargs = dict(inputs, streamer=streamer, max_new_tokens=100)

        def generate():
            thread = Thread(target=model.generate, kwargs=generation_kwargs)
            thread.start()
            for text in streamer:
                yield text

        return app.response_class(generate(), mimetype='text/plain')
    
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)