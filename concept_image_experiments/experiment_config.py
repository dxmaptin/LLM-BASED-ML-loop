"""
Configuration for Concept Image Extraction Experiments
"""
import os

# Base paths
BASE_DIR = r"C:\Users\d.zhang\Desktop\Experiments"
CONCEPT_IMAGES_DIR = os.path.join(BASE_DIR, "Concept Images")
OUTPUT_DIR = os.path.join(BASE_DIR, "concept_image_experiments", "results")

# Test images - selecting 3 diverse products
TEST_IMAGES = [
    "Witty Optimist_Jan24.Girls Night Out cool aid.jpg",  # Jelly cream product with lifestyle imagery
    "Witty Optimist_FY25.S&G Be Me Body Sprays.JPG",       # Body sprays - different product type
    "Witty Optimist_Jan24.Mission Possible Body Lotion.jpg" # Body lotion - another format
]

# OpenAI API configuration
OPENAI_MODEL = "gpt-4o"  # Best multimodal model

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
