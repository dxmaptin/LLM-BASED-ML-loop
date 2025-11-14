"""
Experiment 2: OCR + LLM
Extract text with OCR first, then enhance with LLM
"""
import os
from PIL import Image
import pytesseract
from openai import OpenAI
from experiment_config import TEST_IMAGES, CONCEPT_IMAGES_DIR, OUTPUT_DIR, OPENAI_MODEL


def extract_text_with_ocr(image_path):
    """Extract text from image using Tesseract OCR"""
    try:
        # Check if Tesseract is installed
        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            return "TESSERACT NOT INSTALLED: Please install Tesseract OCR. See README.md for instructions."

        # Open image
        image = Image.open(image_path)

        # Perform OCR
        text = pytesseract.image_to_string(image)

        return text.strip()
    except Exception as e:
        return f"OCR Error: {str(e)}"


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
    Extract content using OCR + LLM pipeline
    Step 1: OCR to extract text
    Step 2: LLM to enhance and structure
    """
    print(f"  Step 1: Running OCR...")
    ocr_text = extract_text_with_ocr(image_path)

    print(f"  Step 2: Enhancing with LLM...")
    enhanced_text = enhance_with_llm(ocr_text, os.path.basename(image_path))

    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("EXPERIMENT 2: OCR + LLM\n")
        f.write("="*80 + "\n\n")
        f.write(f"Image: {os.path.basename(image_path)}\n")
        f.write(f"Method: Image → Tesseract OCR → {OPENAI_MODEL} → Text output\n")
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
    print("EXPERIMENT 2: OCR + LLM")
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
