"""
Convert the batch vision processing results to a structured CSV file
Parses all text files and extracts structured information into CSV format
"""
import os
import csv
import re
from pathlib import Path

# Configuration
BASE_DIR = r"C:\Users\d.zhang\Desktop\Experiments"
INPUT_DIR = os.path.join(BASE_DIR, "concept_image_experiments", "results", "batch_all")
OUTPUT_CSV = os.path.join(BASE_DIR, "concept_image_experiments", "results", "vision_extraction_results.csv")


def parse_text_file(file_path):
    """
    Parse a single text file and extract structured information
    Returns a dictionary with all extracted fields
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract image name from header
    image_name_match = re.search(r'Image: (.+?)\.(?:jpg|JPG|jpeg|JPEG)', content)
    image_name = image_name_match.group(1) if image_name_match else os.path.basename(file_path)

    # Initialize data dictionary
    data = {
        'image_filename': image_name,
        'product_name': '',
        'brand': '',
        'product_description': '',
        'product_category': '',
        'key_claims_benefits': '',
        'ingredients': '',
        'packaging_size': '',
        'packaging_price': '',
        'usage_instructions': '',
        'color_scheme': '',
        'imagery_type': '',
        'badges_labels': '',
        'design_style': '',
        'target_audience': '',
        'additional_text': '',
        'full_extraction': ''
    }

    # Extract the main content (after the header)
    content_match = re.search(r'={80}\n\n(.+)', content, re.DOTALL)
    if content_match:
        main_content = content_match.group(1)
        data['full_extraction'] = main_content.strip()
    else:
        main_content = content
        data['full_extraction'] = content.strip()

    # Parse Product Name and Brand (Section 1)
    product_name_section = re.search(r'\*\*Product Name and Brand\*\*:?\s*\n(.*?)(?=\n\d+\.|$)', main_content, re.DOTALL)
    if product_name_section:
        section_text = product_name_section.group(1)
        # Extract brand and product name from bullet points or plain text
        brand_match = re.search(r'[-•]\s*(.+?)(?=\n|$)', section_text)
        lines = [line.strip() for line in section_text.split('\n') if line.strip() and not line.strip().startswith('-') or line.strip().startswith('•')]

        if brand_match:
            potential_brand = brand_match.group(1).strip('- •')
            potential_name = ''
            # Look for second line
            lines_clean = [l.strip('- •') for l in section_text.split('\n') if l.strip()]
            if len(lines_clean) >= 2:
                potential_name = lines_clean[0]
                potential_brand = lines_clean[1]
            else:
                potential_name = potential_brand

            data['product_name'] = potential_name
            data['brand'] = potential_brand if 'Soap' in potential_brand or 'GLORY' in potential_brand else ''
        else:
            data['product_name'] = section_text.strip().replace('\n', ' ')

    # Parse Product Description (Section 2)
    desc_match = re.search(r'\*\*Product Description\*\*:?\s*\n\s*[-•]?\s*(.+?)(?=\n\d+\.|$)', main_content, re.DOTALL)
    if desc_match:
        data['product_description'] = desc_match.group(1).strip().replace('\n', ' ')

    # Parse Product Category (Section 3)
    category_match = re.search(r'\*\*Product Category\*\*:?\s*\n\s*[-•]?\s*(.+?)(?=\n\d+\.|$)', main_content, re.DOTALL)
    if category_match:
        data['product_category'] = category_match.group(1).strip().replace('\n', ' ')

    # Parse Key Claims/Benefits (Section 4)
    claims_match = re.search(r'\*\*Key Claims/Benefits\*\*:?\s*\n(.*?)(?=\n\d+\.|$)', main_content, re.DOTALL)
    if claims_match:
        claims_text = claims_match.group(1).strip()
        # Clean up bullet points
        claims_lines = [line.strip('- •').strip() for line in claims_text.split('\n') if line.strip()]
        data['key_claims_benefits'] = '; '.join(claims_lines)

    # Parse Ingredients (Section 5)
    ingredients_match = re.search(r'\*\*Ingredients\*\*:?\s*\n(.*?)(?=\n\d+\.|$)', main_content, re.DOTALL)
    if ingredients_match:
        ingredients_text = ingredients_match.group(1).strip()
        ingredients_lines = [line.strip('- •').strip() for line in ingredients_text.split('\n') if line.strip()]
        data['ingredients'] = '; '.join(ingredients_lines)

    # Parse Packaging Information (Section 6)
    packaging_match = re.search(r'\*\*Packaging Information\*\*:?\s*\n(.*?)(?=\n\d+\.|$)', main_content, re.DOTALL)
    if packaging_match:
        packaging_text = packaging_match.group(1).strip()
        # Extract size
        size_match = re.search(r'(\d+\s*(?:ml|g|oz|ML|G|OZ))', packaging_text, re.IGNORECASE)
        if size_match:
            data['packaging_size'] = size_match.group(1)
        # Extract price
        price_match = re.search(r'[£$€]\s*[\d.]+', packaging_text)
        if price_match:
            data['packaging_price'] = price_match.group(0)

    # Parse Usage Instructions (Section 7)
    usage_match = re.search(r'\*\*Usage Instructions\*\*:?\s*\n(.*?)(?=\n\d+\.|$)', main_content, re.DOTALL)
    if usage_match:
        usage_text = usage_match.group(1).strip()
        usage_lines = [line.strip('- •').strip() for line in usage_text.split('\n') if line.strip() and not re.match(r'^\d+\.$', line.strip())]
        data['usage_instructions'] = ' '.join(usage_lines)

    # Parse Visual Design Elements (Section 8)
    visual_match = re.search(r'\*\*Visual Design Elements\*\*:?\s*\n(.*?)(?=\n\d+\.|$)', main_content, re.DOTALL)
    if visual_match:
        visual_text = visual_match.group(1)

        # Color scheme
        color_match = re.search(r'\*\*Color scheme.*?\*\*:?\s*(.+?)(?=\n\s*[-•]\s*\*\*|$)', visual_text, re.DOTALL)
        if color_match:
            data['color_scheme'] = color_match.group(1).strip().replace('\n', ' ')

        # Imagery type
        imagery_match = re.search(r'\*\*(?:Lifestyle imagery|Is this lifestyle).*?\*\*:?\s*(.+?)(?=\n\s*[-•]\s*\*\*|$)', visual_text, re.DOTALL)
        if imagery_match:
            data['imagery_type'] = imagery_match.group(1).strip().replace('\n', ' ')

        # Badges/labels
        badges_match = re.search(r'\*\*(?:Any badges|Badges).*?\*\*:?\s*(.+?)(?=\n\s*[-•]\s*\*\*|$)', visual_text, re.DOTALL)
        if badges_match:
            data['badges_labels'] = badges_match.group(1).strip().replace('\n', ' ')

        # Design style
        style_match = re.search(r'\*\*Overall design style\*\*:?\s*(.+?)(?=\n\s*[-•]\s*\*\*|\n\d+\.|$)', visual_text, re.DOTALL)
        if style_match:
            data['design_style'] = style_match.group(1).strip().replace('\n', ' ')

    # Parse Target Audience (Section 9)
    audience_match = re.search(r'\*\*Target Audience.*?\*\*:?\s*\n(.*?)(?=\n\d+\.|$)', main_content, re.DOTALL)
    if audience_match:
        audience_text = audience_match.group(1).strip()
        audience_lines = [line.strip('- •').strip() for line in audience_text.split('\n') if line.strip()]
        data['target_audience'] = ' '.join(audience_lines)

    # Parse Additional Text (Section 10)
    additional_match = re.search(r'\*\*Any Additional Text\*\*:?\s*\n(.*?)(?=\n\n|$)', main_content, re.DOTALL)
    if additional_match:
        additional_text = additional_match.group(1).strip()
        additional_lines = [line.strip('- •').strip() for line in additional_text.split('\n') if line.strip()]
        data['additional_text'] = ' '.join(additional_lines)

    return data


def convert_all_to_csv():
    """
    Convert all text files in the batch_all directory to a single CSV file
    """
    print("\n" + "="*80)
    print("CONVERTING VISION RESULTS TO CSV")
    print("="*80 + "\n")

    # Get all .txt files (excluding summary)
    txt_files = [f for f in os.listdir(INPUT_DIR)
                 if f.endswith('.txt') and f.startswith('exp1_') and 'SUMMARY' not in f]

    total_files = len(txt_files)
    print(f"Found {total_files} result files to process\n")

    all_data = []
    successful = 0
    failed = 0

    for idx, filename in enumerate(sorted(txt_files), 1):
        file_path = os.path.join(INPUT_DIR, filename)
        print(f"[{idx}/{total_files}] Processing: {filename}")

        try:
            data = parse_text_file(file_path)
            all_data.append(data)
            successful += 1
            print(f"  - OK: Extracted {data['product_name'] or 'Unknown'}")
        except Exception as e:
            print(f"  - ERROR: {str(e)}")
            failed += 1

    # Write to CSV
    if all_data:
        print(f"\n{'-'*80}")
        print(f"Writing {len(all_data)} records to CSV...")

        fieldnames = [
            'image_filename',
            'product_name',
            'brand',
            'product_description',
            'product_category',
            'key_claims_benefits',
            'ingredients',
            'packaging_size',
            'packaging_price',
            'usage_instructions',
            'color_scheme',
            'imagery_type',
            'badges_labels',
            'design_style',
            'target_audience',
            'additional_text',
            'full_extraction'
        ]

        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_data)

        print(f"  - OK: CSV saved to: {OUTPUT_CSV}")

    print("\n" + "="*80)
    print("CONVERSION COMPLETE!")
    print("="*80)
    print(f"\nResults:")
    print(f"  - Total files processed: {total_files}")
    print(f"  - Successful: {successful}")
    print(f"  - Failed: {failed}")
    print(f"  - CSV output: {OUTPUT_CSV}")
    print(f"  - Total records: {len(all_data)}")
    print("\n" + "="*80 + "\n")

    return all_data


if __name__ == "__main__":
    convert_all_to_csv()
