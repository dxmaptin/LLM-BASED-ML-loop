"""
Organize all project data into a single consolidated data folder structure
Moves images, processed results, CSVs, and other data files from root into organized folders
"""
import os
import shutil
from pathlib import Path

BASE_DIR = r"C:\Users\d.zhang\Desktop\Experiments"

# Define the new organized structure
DATA_STRUCTURE = {
    'concept_vision_data': {
        'raw_images': 'Concept Images',  # Source folder for images
        'processed_txt': 'concept_image_experiments/results/batch_all',  # Processed text files
        'processed_csv': 'concept_image_experiments/results',  # CSV results
    },
    'acorn_data': {
        'ground_truth': [
            'ACORN_ground_truth_22classes.csv',
            'ACORN_ground_truth_named.csv',
            'Accorn.txt',
        ],
        'results': [
            'ACORN_r2_results.json',
            'ACORN_v3_r2_results.json',
            'ACORN_v4_r2_results.json',
        ],
        'analysis': [
            'v2_error_analysis_for_v3_improvements.json',
            'v3_comprehensive_analysis.json',
            'v3_underperforming_classes.json',
            'v4_underperforming_classes.json',
        ],
        'prompt_analysis': 'ACORN_prompt_analysis',  # Directory
    },
    'demographic_data': {
        'runs': 'demographic_runs_ACORN',  # Directory
        'results': [
            'all_12_demographics_results.csv',
        ],
    },
    'training_data': {
        'splits': [
            'attitude_questions_train_test_split.json',
        ],
        'results': [
            'v10_training_results.txt',
            'holdout_test_result.txt',
            'holdout_results.json',
        ],
    },
    'batch_results': {
        'batch2_3': [
            'batch2_3_results_batched.json',
            'batch2_results_batched.txt',
        ],
        'batch3': [
            'batch3_result.txt',
            'batch3_results.json',
        ],
        'multi_class': [
            'multi_class_results.txt',
        ],
    },
    'v10_results': {
        'detailed': [
            'v10_detailed_all_21_classes.csv',
        ],
        'missing_classes': [
            'v10_missing_3_complete_results.txt',
            'v10_missing_3_results.txt',
            'v10_missing_3_classes_results.csv',
        ],
        'remaining': [
            'v10_remaining_results.txt',
            'v10_remaining_classes_results.csv',
        ],
        'comprehensive': [
            'v10_all_classes_comprehensive_results.csv',
        ],
        'three_new_classes': [
            'three_new_classes_results.txt',
        ],
    },
    'handpicked_data': {
        'input': [
            'Handpicked_ACORN_10.csv',
        ],
    },
    'misc_data': {
        'verification': [
            'exclusive_addresses_verification.txt',
        ],
        'concepts': [
            'concepts_to_test.csv',
        ],
        'initial_questions': [
            'initial_10_questions.csv',
        ],
        'model_comparison': [
            'model_comparison_all_results.csv',
        ],
    },
}


def create_organized_structure():
    """Create the organized data folder structure"""

    print("\n" + "="*80)
    print("ORGANIZING PROJECT DATA INTO CONSOLIDATED STRUCTURE")
    print("="*80 + "\n")

    # Main data directory
    data_dir = os.path.join(BASE_DIR, "project_data")
    os.makedirs(data_dir, exist_ok=True)
    print(f"Created main data directory: {data_dir}\n")

    moved_count = 0
    skipped_count = 0
    error_count = 0

    # Process each category
    for category, contents in DATA_STRUCTURE.items():
        category_path = os.path.join(data_dir, category)
        os.makedirs(category_path, exist_ok=True)
        print(f"\n[{category.upper()}]")
        print("-" * 80)

        for subcat, items in contents.items():
            subcat_path = os.path.join(category_path, subcat)
            os.makedirs(subcat_path, exist_ok=True)

            # Handle both single items (directories) and lists of files
            if isinstance(items, str):
                items = [items]

            for item in items:
                source = os.path.join(BASE_DIR, item)

                # Check if it's a directory or file
                if os.path.isdir(source):
                    dest = os.path.join(subcat_path, os.path.basename(item))
                    try:
                        if os.path.exists(dest):
                            print(f"  SKIP: {item} (already exists)")
                            skipped_count += 1
                        else:
                            shutil.copytree(source, dest)
                            print(f"  COPY: {item} -> {category}/{subcat}/")
                            moved_count += 1
                    except Exception as e:
                        print(f"  ERROR: {item} - {str(e)}")
                        error_count += 1

                elif os.path.isfile(source):
                    dest = os.path.join(subcat_path, os.path.basename(item))
                    try:
                        if os.path.exists(dest):
                            print(f"  SKIP: {item} (already exists)")
                            skipped_count += 1
                        else:
                            shutil.copy2(source, dest)
                            print(f"  COPY: {item} -> {category}/{subcat}/")
                            moved_count += 1
                    except Exception as e:
                        print(f"  ERROR: {item} - {str(e)}")
                        error_count += 1
                else:
                    print(f"  NOT FOUND: {item}")
                    skipped_count += 1

    print("\n" + "="*80)
    print("DATA ORGANIZATION COMPLETE!")
    print("="*80)
    print(f"\nSummary:")
    print(f"  - Items copied: {moved_count}")
    print(f"  - Items skipped: {skipped_count}")
    print(f"  - Errors: {error_count}")
    print(f"\nOrganized data location: {data_dir}")
    print("\n" + "="*80 + "\n")

    # Create a README in the data directory
    readme_path = os.path.join(data_dir, "README.txt")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("PROJECT DATA DIRECTORY STRUCTURE\n")
        f.write("="*80 + "\n\n")
        f.write("This directory contains all project data organized by category:\n\n")
        f.write("1. concept_vision_data/\n")
        f.write("   - raw_images/: Original product concept images\n")
        f.write("   - processed_txt/: GPT-4o vision extraction results (text files)\n")
        f.write("   - processed_csv/: Structured CSV with all extracted data\n\n")
        f.write("2. acorn_data/\n")
        f.write("   - ground_truth/: ACORN ground truth datasets\n")
        f.write("   - results/: ACORN model results and R2 scores\n")
        f.write("   - analysis/: Error analysis and performance evaluation\n")
        f.write("   - prompt_analysis/: Prompt engineering analysis\n\n")
        f.write("3. demographic_data/\n")
        f.write("   - runs/: Demographic experiment runs\n")
        f.write("   - results/: Results for all demographic categories\n\n")
        f.write("4. training_data/\n")
        f.write("   - splits/: Train/test split configurations\n")
        f.write("   - results/: Training and holdout test results\n\n")
        f.write("5. batch_results/\n")
        f.write("   - Various batch processing results\n\n")
        f.write("6. v10_results/\n")
        f.write("   - Version 10 model results and analysis\n\n")
        f.write("7. handpicked_data/\n")
        f.write("   - Curated datasets for specific experiments\n\n")
        f.write("8. misc_data/\n")
        f.write("   - Other project data files\n\n")
        f.write("="*80 + "\n")
        f.write(f"Created: {os.path.basename(__file__)}\n")
        f.write("="*80 + "\n")

    print(f"Created README: {readme_path}\n")

    return data_dir


def show_cleanup_instructions(data_dir):
    """Show instructions for cleaning up root directory"""
    print("\n" + "="*80)
    print("CLEANUP INSTRUCTIONS")
    print("="*80 + "\n")
    print("Data has been COPIED (not moved) to maintain safety.")
    print("\nTo clean up the root directory after verifying data integrity:\n")
    print("1. Verify all data in: project_data/")
    print("2. Review the files that were copied")
    print("3. Run the cleanup script to remove originals from root\n")
    print("Would you like to create a cleanup script? (Manual decision)\n")
    print("="*80 + "\n")


if __name__ == "__main__":
    data_dir = create_organized_structure()
    show_cleanup_instructions(data_dir)
