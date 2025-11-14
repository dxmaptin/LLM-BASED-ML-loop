"""
Batch process ALL images in Concept Images folder using Experiment 1 (Multimodal LLM)
Saves individual text files for each image to concept_image_experiments/results/batch_all/
"""
import os
import base64
from openai import OpenAI
from pathlib import Path
import time

# Configuration
BASE_DIR = r"C:\Users\d.zhang\Desktop\Experiments"
CONCEPT_IMAGES_DIR = os.path.join(BASE_DIR, "Concept Images")
OUTPUT_DIR = os.path.join(BASE_DIR, "concept_image_experiments", "results", "batch_all")
OPENAI_MODEL = "gpt-4o"

# Supported image extensions
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.JPG', '.JPEG', '.png', '.PNG']


def encode_image(image_path):
    """Encode image to base64 for OpenAI API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def extract_with_multimodal_llm(image_path, output_path):
    """
    Extract content using multimodal LLM only
    No preprocessing - direct image to LLM
    """
    client = OpenAI()

    # Encode image
    print(f"  - Encoding image...")
    base64_image = encode_image(image_path)

    # Prompt for comprehensive extraction
    prompt = """Analyze this product concept image in detail and extract ALL information present.

Please provide:
1. **Product Name and Brand**: Exact text as shown
2. **Product Description**: Complete description text
3. **Product Category**: Type of product (e.g., cream, spray, lotion)
4. **Key Claims/Benefits**: All stated benefits and features
5. **Ingredients**: Active ingredients or formulation details mentioned
6. **Packaging Information**: Format, size, price if visible
7. **Usage Instructions**: How to use the product
8. **Visual Design Elements**:
   - Color scheme and dominant colors
   - Is this lifestyle imagery (models/people) or product-only?
   - Any badges, labels, or special callouts
   - Overall design style (premium, casual, playful, clinical, etc.)
9. **Target Audience Signals**: Visual or textual cues about intended users
10. **Any Additional Text**: Taglines, brand messages, etc.

Extract everything exactly as it appears in the image, preserving exact wording. Also provide your analysis of visual elements that aren't captured in text."""

    # Call OpenAI API
    print(f"  - Calling OpenAI API...")
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=2000
    )

    # Extract and save result
    result = response.choices[0].message.content

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("EXPERIMENT 1: MULTIMODAL LLM ONLY (GPT-4O)\n")
        f.write("="*80 + "\n\n")
        f.write(f"Image: {os.path.basename(image_path)}\n")
        f.write(f"Method: Direct image → {OPENAI_MODEL} → Text output\n")
        f.write("="*80 + "\n\n")
        f.write(result)

    print(f"  - OK: Saved to: {os.path.basename(output_path)}")
    return result


def get_all_images():
    """Get all image files from the Concept Images directory"""
    images = []
    for filename in os.listdir(CONCEPT_IMAGES_DIR):
        if any(filename.endswith(ext) for ext in IMAGE_EXTENSIONS):
            images.append(filename)
    return sorted(images)


def run_batch_processing():
    """Run Experiment 1 on ALL images in the Concept Images folder"""

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get all images
    all_images = get_all_images()
    total_images = len(all_images)

    print("\n" + "="*80)
    print("BATCH PROCESSING: MULTIMODAL LLM FOR ALL PRODUCT IMAGES")
    print("="*80)
    print(f"\nFound {total_images} images in: {CONCEPT_IMAGES_DIR}")
    print(f"Output directory: {OUTPUT_DIR}\n")
    print("="*80 + "\n")

    results = {}
    successful = 0
    failed = 0

    start_time = time.time()

    for idx, image_name in enumerate(all_images, 1):
        image_path = os.path.join(CONCEPT_IMAGES_DIR, image_name)

        # Create safe filename for output
        safe_name = os.path.splitext(image_name)[0].replace(' ', '_').replace('&', 'and')
        output_filename = f"exp1_{safe_name}.txt"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        print(f"[{idx}/{total_images}] Processing: {image_name}")

        try:
            result = extract_with_multimodal_llm(image_path, output_path)
            results[image_name] = {
                'status': 'success',
                'output_file': output_filename,
                'result': result
            }
            successful += 1

        except Exception as e:
            print(f"  - ERROR: {str(e)}")
            results[image_name] = {
                'status': 'failed',
                'error': str(e)
            }
            failed += 1

        print()  # Blank line between images

    elapsed_time = time.time() - start_time

    # Create summary file
    summary_path = os.path.join(OUTPUT_DIR, "BATCH_SUMMARY.txt")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("BATCH PROCESSING SUMMARY\n")
        f.write("="*80 + "\n\n")
        f.write(f"Total images processed: {total_images}\n")
        f.write(f"Successful: {successful}\n")
        f.write(f"Failed: {failed}\n")
        f.write(f"Time elapsed: {elapsed_time:.2f} seconds\n")
        f.write(f"Average time per image: {elapsed_time/total_images:.2f} seconds\n\n")
        f.write("="*80 + "\n")
        f.write("PROCESSED FILES\n")
        f.write("="*80 + "\n\n")

        for image_name, result_info in results.items():
            f.write(f"\n{image_name}\n")
            f.write(f"  Status: {result_info['status']}\n")
            if result_info['status'] == 'success':
                f.write(f"  Output: {result_info['output_file']}\n")
            else:
                f.write(f"  Error: {result_info.get('error', 'Unknown error')}\n")

    print("="*80)
    print("BATCH PROCESSING COMPLETE!")
    print("="*80)
    print(f"\nResults:")
    print(f"  - Total images: {total_images}")
    print(f"  - Successful: {successful}")
    print(f"  - Failed: {failed}")
    print(f"  - Time elapsed: {elapsed_time:.2f} seconds")
    print(f"  - Average per image: {elapsed_time/total_images:.2f} seconds")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"Summary file: {summary_path}")
    print("\n" + "="*80 + "\n")

    return results


if __name__ == "__main__":
    run_batch_processing()
