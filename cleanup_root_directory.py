"""
Cleanup script to remove data files from root directory after they've been copied to project_data/
This script will DELETE files and folders from the root, so verify project_data/ first!
"""
import os
import shutil

BASE_DIR = r"C:\Users\d.zhang\Desktop\Experiments"

# Files and folders to remove from root (already copied to project_data)
ITEMS_TO_REMOVE = [
    # Concept vision - folder
    'Concept Images',

    # ACORN data files
    'ACORN_ground_truth_22classes.csv',
    'ACORN_ground_truth_named.csv',
    'Accorn.txt',
    'ACORN_r2_results.json',
    'ACORN_v4_r2_results.json',

    # Analysis files
    'v2_error_analysis_for_v3_improvements.json',
    'v3_comprehensive_analysis.json',
    'v4_underperforming_classes.json',

    # Demographic data
    'demographic_runs_ACORN',

    # Training data
    'attitude_questions_train_test_split.json',
    'v10_training_results.txt',
    'holdout_test_result.txt',

    # Batch results
    'batch2_results_batched.txt',
    'batch3_result.txt',
    'multi_class_results.txt',

    # V10 results
    'v10_detailed_all_21_classes.csv',
    'v10_missing_3_complete_results.txt',
    'v10_missing_3_results.txt',
    'v10_remaining_results.txt',
    'three_new_classes_results.txt',

    # Misc
    'exclusive_addresses_verification.txt',
]


def confirm_cleanup():
    """Ask user to confirm cleanup"""
    print("\n" + "="*80)
    print("CLEANUP ROOT DIRECTORY - CONFIRMATION REQUIRED")
    print("="*80 + "\n")
    print("This script will DELETE the following items from the root directory:\n")

    for item in ITEMS_TO_REMOVE:
        item_path = os.path.join(BASE_DIR, item)
        if os.path.exists(item_path):
            if os.path.isdir(item_path):
                print(f"  [FOLDER] {item}")
            else:
                print(f"  [FILE]   {item}")
        else:
            print(f"  [NOT FOUND] {item}")

    print("\n" + "="*80)
    print("IMPORTANT: Verify that all data is safely copied to project_data/ first!")
    print("="*80 + "\n")

    response = input("Type 'DELETE' to proceed with cleanup (or anything else to cancel): ")
    return response.strip() == 'DELETE'


def cleanup_root():
    """Remove files and folders from root directory"""

    if not confirm_cleanup():
        print("\nCleanup cancelled. No files were deleted.\n")
        return

    print("\n" + "="*80)
    print("CLEANING UP ROOT DIRECTORY")
    print("="*80 + "\n")

    deleted_count = 0
    skipped_count = 0
    error_count = 0

    for item in ITEMS_TO_REMOVE:
        item_path = os.path.join(BASE_DIR, item)

        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                print(f"  DELETED: {item}/ (folder)")
                deleted_count += 1
            elif os.path.isfile(item_path):
                os.remove(item_path)
                print(f"  DELETED: {item}")
                deleted_count += 1
            else:
                print(f"  SKIPPED: {item} (not found)")
                skipped_count += 1
        except Exception as e:
            print(f"  ERROR: {item} - {str(e)}")
            error_count += 1

    print("\n" + "="*80)
    print("CLEANUP COMPLETE!")
    print("="*80)
    print(f"\nSummary:")
    print(f"  - Items deleted: {deleted_count}")
    print(f"  - Items skipped: {skipped_count}")
    print(f"  - Errors: {error_count}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    cleanup_root()
