# PaLI-GeMMA Image Analyzer

PaLI-GeMMA Image Analyzer is a web application that utilizes the PaLI-GeMMA (Pathways Language and Image Model - Generalist Multimodal Agent) to analyze images based on user prompts. This application allows users to upload images or provide image URLs and ask questions or provide prompts about the image content.

![PaLI-GeMMA Image Analyzer Screenshot](assets/127.0.0.1_5000_.png)

## Features

- Drag and drop image upload from local files or web pages
- Image URL input support
- Real-time analysis streaming
- Responsive design with dark mode support
- Download analysis results as text files

## Prerequisites

- Python 3.9+
- Flask
- Transformers library
- PyTorch
- Hugging Face account and API token

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/TanaroSch/pali-gemma-image-analyzer.git
   cd pali-gemma-image-analyzer
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root, accept the conditions [here](https://huggingface.co/google/paligemma-3b-pt-224) and add your Hugging Face API token:
   ```
   HUGGINGFACE_TOKEN=your_token_here
   MODEL_PATH=./model  # Optional: Set a custom path for model storage
   ```

   Note: If `MODEL_PATH` is not set, the application will use `./model` as the default path.

## Usage

1. Start the Flask application:
   ```
   python app.py
   ```

2. On first startup the model will be downloaded if not existant in the model_cache folder.

3. Open a web browser and navigate to `http://localhost:5000`.

4. Upload an image by dragging and dropping it onto the page, or by providing an image URL.

5. Enter a prompt or question about the image in the text area.

6. Click "Analyze" or press Enter to start the analysis.

7. View the analysis results in real-time as they stream in.

8. Optionally, click "Download Result" to save the analysis as a text file.

## Custom Model Path

You can specify a custom path for storing the PaLI-GeMMA model by setting the `MODEL_PATH` environment variable in your `.env` file. If not set, the application will use `./model` as the default path.

## Acknowledgments

- PaLI-GeMMA model by Google
- Hugging Face for providing the model hosting and API