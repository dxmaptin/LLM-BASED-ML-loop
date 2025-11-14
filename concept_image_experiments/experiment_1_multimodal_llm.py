"""
Experiment 1: Multimodal LLM Only (gpt-4o)
Direct image interpretation without any preprocessing
"""
import os
import base64
from openai import OpenAI
from experiment_config import TEST_IMAGES, CONCEPT_IMAGES_DIR, OUTPUT_DIR, OPENAI_MODEL


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

    print(f"[OK] Experiment 1 completed for: {os.path.basename(image_path)}")
    return result


def run_experiment_1():
    """Run Experiment 1 on all test images"""
    print("\n" + "="*80)
    print("EXPERIMENT 1: MULTIMODAL LLM ONLY")
    print("="*80 + "\n")

    results = {}

    for image_name in TEST_IMAGES:
        image_path = os.path.join(CONCEPT_IMAGES_DIR, image_name)
        output_filename = f"exp1_multimodal_{os.path.splitext(image_name)[0]}.txt"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        print(f"\nProcessing: {image_name}")
        result = extract_with_multimodal_llm(image_path, output_path)
        results[image_name] = result
        print(f"Saved to: {output_filename}")

    print("\n" + "="*80)
    print("EXPERIMENT 1 COMPLETE")
    print("="*80 + "\n")

    return results


if __name__ == "__main__":
    run_experiment_1()
