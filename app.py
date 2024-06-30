# app.py
from flask import Flask, render_template, request, jsonify, Response
from transformers import AutoProcessor, PaliGemmaForConditionalGeneration, TextIteratorStreamer
import torch
from PIL import Image
import requests
from io import BytesIO
from huggingface_hub import login
from dotenv import load_dotenv
import os
from threading import Thread
import logging
import traceback
import numpy as np

load_dotenv()

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

HF_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
if not HF_TOKEN:
    raise ValueError("HUGGINGFACE_TOKEN not found in .env file")
login(token=HF_TOKEN)

model_id = "google/paligemma-3b-mix-224"
model_cache_path = os.getenv('MODEL_CACHE_PATH', './model')
model_dir = os.path.join(model_cache_path, model_id.split("/")[-1])

os.makedirs(model_cache_path, exist_ok=True)

if not os.path.exists(model_dir) or not os.listdir(model_dir):
    app.logger.info(f"Model not found in cache. Downloading model to {model_dir}...")
    from huggingface_hub import snapshot_download
    snapshot_download(repo_id=model_id, local_dir=model_dir, token=HF_TOKEN)
    app.logger.info("Model downloaded successfully.")
else:
    app.logger.info(f"Using cached model from {model_dir}")

try:
    model = PaliGemmaForConditionalGeneration.from_pretrained(model_dir)
    processor = AutoProcessor.from_pretrained(model_dir)
except Exception as e:
    app.logger.error(f"Error loading model: {str(e)}")
    raise

def preprocess_image(image):
    # Ensure image is in RGB format
    image = image.convert('RGB')
    
    # Resize image to a standard size
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
        app.logger.info(f"Analyzing image. Source: {image_source}, Prompt: {prompt}")
        
        if image_source == 'url':
            image_url = request.form['image_url']
            app.logger.debug(f"Fetching image from URL: {image_url}")
            response = requests.get(image_url)
            raw_image = Image.open(BytesIO(response.content))
        else:
            app.logger.debug("Processing uploaded image file")
            image_file = request.files['image_file']
            raw_image = Image.open(image_file)
        
        app.logger.debug("Preprocessing image")
        processed_image = preprocess_image(raw_image)
        
        app.logger.debug("Preparing inputs for model")
        inputs = processor(prompt, images=processed_image, return_tensors="pt")
        
        app.logger.debug("Setting up streamer")
        streamer = TextIteratorStreamer(processor.tokenizer, skip_special_tokens=True)
        generation_kwargs = dict(inputs, streamer=streamer, max_new_tokens=100)

        def generate():
            app.logger.debug("Starting generation thread")
            thread = Thread(target=model.generate, kwargs=generation_kwargs)
            thread.start()
            for text in streamer:
                yield text
                if text.endswith('<eos>'):
                    break
            app.logger.debug("Generation complete")

        app.logger.info("Returning response stream")
        return Response(generate(), mimetype='text/plain')
    
    except Exception as e:
        app.logger.error(f"Error during analysis: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)