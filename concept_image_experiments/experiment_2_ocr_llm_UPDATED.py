"""
Experiment 2: OCR + LLM (UPDATED - Using GPT-4o Vision as OCR)
Extract text with GPT-4o vision (OCR mode), then enhance with LLM
"""
import os
import base64
from PIL import Image
from openai import OpenAI
from experiment_config import TEST_IMAGES, CONCEPT_IMAGES_DIR, OUTPUT_DIR, OPENAI_MODEL


def encode_image(image_path):
    """Encode image to base64 for OpenAI API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def extract_text_with_vision_ocr(image_path):
    """
    Extract text from image using GPT-4o Vision in OCR mode
    (Alternative to Tesseract when it's not available)
    """
    try:
        client = OpenAI()
        base64_image = encode_image(image_path)

        # Prompt focused ONLY on text extraction (OCR behavior)
        ocr_prompt = """Extract ALL text from this image exactly as it appears.

Your task is to act as an OCR system - extract every piece of text you can see, maintaining:
- Exact wording and spelling
- Text positioning/layout where possible
- All visible text including small print, labels, badges, etc.

Output ONLY the raw extracted text, without any interpretation or analysis.
List the text in the order you see it, with line breaks where appropriate."""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ocr_prompt},
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

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Vision OCR Error: {str(e)}"


def enhance_with_llm(ocr_text, image_name):
    """Enhance OCR text with LLM for better structure and interpretation"""
    client = OpenAI()

    prompt = f"""You are analyzing a product concept image. Below is the raw OCR text extracted from the image.

Your task:
1. Clean up and organize the OCR text into structured information
2. Identify and categorize:
   - Product name and brand
   - Product description
   - Product category
   - Key claims and benefits
   - Ingredients or formulation details
   - Packaging format and specifications
   - Usage instructions
   - Price and size information
   - Any taglines or marketing messages
3. Fix any OCR errors or typos
4. Preserve exact wording where possible
5. Note if critical information seems missing or unclear

RAW OCR TEXT:
{ocr_text}

Please provide a comprehensive, well-structured interpretation of this product concept."""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000
    )

    return response.choices[0].message.content


def extract_with_ocr_llm(image_path, output_path):
    """
    Extract content using Vision OCR + LLM pipeline
    Step 1: GPT-4o Vision for text extraction (OCR mode)
    Step 2: LLM to enhance and structure
    """
    print(f"  Step 1: Running Vision-based OCR...")
    ocr_text = extract_text_with_vision_ocr(image_path)

    print(f"  Step 2: Enhancing with LLM...")
    enhanced_text = enhance_with_llm(ocr_text, os.path.basename(image_path))

    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("EXPERIMENT 2: OCR + LLM (UPDATED)\n")
        f.write("="*80 + "\n\n")
        f.write(f"Image: {os.path.basename(image_path)}\n")
        f.write(f"Method: Image → GPT-4o Vision OCR → {OPENAI_MODEL} Enhancement\n")
        f.write(f"Note: Using GPT-4o Vision as OCR (Tesseract alternative)\n")
        f.write("="*80 + "\n\n")
        f.write("RAW OCR OUTPUT:\n")
        f.write("-"*80 + "\n")
        f.write(ocr_text if ocr_text else "[No text detected]")
        f.write("\n\n" + "="*80 + "\n\n")
        f.write("LLM ENHANCED OUTPUT:\n")
        f.write("-"*80 + "\n")
        f.write(enhanced_text)

    print(f"[OK] Experiment 2 completed for: {os.path.basename(image_path)}")
    return {"ocr": ocr_text, "enhanced": enhanced_text}


def run_experiment_2():
    """Run Experiment 2 on all test images"""
    print("\n" + "="*80)
    print("EXPERIMENT 2: OCR + LLM (UPDATED WITH VISION OCR)")
    print("="*80 + "\n")

    results = {}

    for image_name in TEST_IMAGES:
        image_path = os.path.join(CONCEPT_IMAGES_DIR, image_name)
        output_filename = f"exp2_ocr_llm_{os.path.splitext(image_name)[0]}.txt"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        print(f"\nProcessing: {image_name}")
        result = extract_with_ocr_llm(image_path, output_path)
        results[image_name] = result
        print(f"Saved to: {output_filename}")

    print("\n" + "="*80)
    print("EXPERIMENT 2 COMPLETE")
    print("="*80 + "\n")

    return results


if __name__ == "__main__":
    run_experiment_2()
