"""
Experiment 3: OCR + Vision Embeddings
Combine OCR text with visual feature embeddings to capture:
- Text content (OCR)
- Visual signals: colors, design style, lifestyle vs product-only, badges, etc.
"""
import os
import base64
from PIL import Image
import pytesseract
from openai import OpenAI
import numpy as np
from experiment_config import TEST_IMAGES, CONCEPT_IMAGES_DIR, OUTPUT_DIR, OPENAI_MODEL


def extract_text_with_ocr(image_path):
    """Extract text from image using Tesseract OCR"""
    try:
        # Check if Tesseract is installed
        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            return "TESSERACT NOT INSTALLED: Please install Tesseract OCR. See README.md for instructions."

        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        return f"OCR Error: {str(e)}"


def encode_image(image_path):
    """Encode image to base64 for OpenAI API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def extract_visual_features(image_path):
    """
    Extract visual features/embeddings from the image
    This captures non-textual information like:
    - Color schemes and palettes
    - Design style and aesthetics
    - Lifestyle vs product-only imagery
    - Badges, labels, visual callouts
    - Layout and composition
    """
    client = OpenAI()
    base64_image = encode_image(image_path)

    # Prompt focused on VISUAL features only (not text)
    visual_prompt = """Analyze the VISUAL and DESIGN elements of this image (ignore text content for now).

Describe:
1. **Color Palette**: Dominant colors, color scheme, color psychology/emotions conveyed
2. **Imagery Type**:
   - Is this lifestyle imagery (people/models shown)?
   - Product photography only?
   - Illustrations/graphics?
   - Mixed approach?
3. **Visual Style**: Premium, casual, clinical, playful, modern, vintage, minimalist, bold, etc.
4. **Design Elements**:
   - Any badges, seals, or callout elements?
   - Icons or symbols used?
   - Layout structure (grid, asymmetric, centered, etc.)
5. **Photography/Illustration Quality**: Professional, artistic, editorial, commercial, etc.
6. **Target Audience Signals (visual cues only)**:
   - Age demographic suggested by visuals?
   - Gender presentation?
   - Lifestyle signals (luxury, everyday, active, etc.)
7. **Packaging Visibility**: Can you see product packaging? What does it look like?
8. **Emotional Tone**: What feeling does the visual design evoke?

Focus ONLY on visual elements - we have the text separately."""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": visual_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=1500
    )

    return response.choices[0].message.content


def synthesize_with_llm(ocr_text, visual_features, image_name):
    """
    Synthesize OCR text and visual features into comprehensive output
    This is where we combine textual and visual information
    """
    client = OpenAI()

    synthesis_prompt = f"""You are analyzing a product concept image. You have two types of information:

1. **TEXT CONTENT** (from OCR):
{ocr_text}

2. **VISUAL FEATURES** (from vision analysis):
{visual_features}

Your task is to create a COMPREHENSIVE product concept analysis that combines both text and visual information.

Provide:
1. **Product Overview**:
   - Name, brand, category
   - Complete description (from text)

2. **Product Details**:
   - Key claims and benefits
   - Ingredients or formulation details
   - Packaging specs, size, price
   - Usage instructions

3. **Visual Positioning Analysis**:
   - How the visual design supports the product message
   - Target audience signals from BOTH text and visuals
   - Design choices and their marketing implications
   - Color psychology and brand alignment

4. **Complete Feature Set**:
   - Text-based features (from OCR)
   - Visual-based features (color, style, imagery type)
   - Combined interpretation

5. **Marketing Insights**:
   - What does the combination of text + visuals tell us about positioning?
   - Lifestyle vs clinical positioning?
   - Premium vs accessible market?
   - Emotional appeal?

Preserve exact text wording from OCR while adding visual context and insights."""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "user", "content": synthesis_prompt}
        ],
        max_tokens=2500
    )

    return response.choices[0].message.content


def extract_with_ocr_vision(image_path, output_path):
    """
    Extract content using OCR + Vision Embeddings pipeline
    Step 1: OCR for text
    Step 2: Vision model for visual features
    Step 3: LLM synthesis of both
    """
    print(f"  Step 1: Running OCR for text extraction...")
    ocr_text = extract_text_with_ocr(image_path)

    print(f"  Step 2: Extracting visual features/embeddings...")
    visual_features = extract_visual_features(image_path)

    print(f"  Step 3: Synthesizing OCR + Visual features...")
    synthesis = synthesize_with_llm(ocr_text, visual_features, os.path.basename(image_path))

    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("EXPERIMENT 3: OCR + VISION EMBEDDINGS\n")
        f.write("="*80 + "\n\n")
        f.write(f"Image: {os.path.basename(image_path)}\n")
        f.write(f"Method: Image → [Tesseract OCR + Vision Model] → {OPENAI_MODEL} Synthesis\n")
        f.write("="*80 + "\n\n")

        f.write("RAW OCR OUTPUT:\n")
        f.write("-"*80 + "\n")
        f.write(ocr_text if ocr_text else "[No text detected]")
        f.write("\n\n" + "="*80 + "\n\n")

        f.write("VISUAL FEATURES ANALYSIS:\n")
        f.write("-"*80 + "\n")
        f.write(visual_features)
        f.write("\n\n" + "="*80 + "\n\n")

        f.write("SYNTHESIZED OUTPUT (OCR + VISUAL):\n")
        f.write("-"*80 + "\n")
        f.write(synthesis)

    print(f"[OK] Experiment 3 completed for: {os.path.basename(image_path)}")
    return {
        "ocr": ocr_text,
        "visual_features": visual_features,
        "synthesis": synthesis
    }


def run_experiment_3():
    """Run Experiment 3 on all test images"""
    print("\n" + "="*80)
    print("EXPERIMENT 3: OCR + VISION EMBEDDINGS")
    print("="*80 + "\n")

    results = {}

    for image_name in TEST_IMAGES:
        image_path = os.path.join(CONCEPT_IMAGES_DIR, image_name)
        output_filename = f"exp3_ocr_vision_{os.path.splitext(image_name)[0]}.txt"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        print(f"\nProcessing: {image_name}")
        result = extract_with_ocr_vision(image_path, output_path)
        results[image_name] = result
        print(f"Saved to: {output_filename}")

    print("\n" + "="*80)
    print("EXPERIMENT 3 COMPLETE")
    print("="*80 + "\n")

    return results


if __name__ == "__main__":
    run_experiment_3()
