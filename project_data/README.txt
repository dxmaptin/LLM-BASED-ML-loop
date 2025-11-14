================================================================================
PROJECT DATA DIRECTORY STRUCTURE
================================================================================

This directory contains all project data organized by category:

1. concept_vision_data/
   - raw_images/: Original product concept images
   - processed_txt/: GPT-4o vision extraction results (text files)
   - processed_csv/: Structured CSV with all extracted data

2. acorn_data/
   - ground_truth/: ACORN ground truth datasets
   - results/: ACORN model results and R2 scores
   - analysis/: Error analysis and performance evaluation
   - prompt_analysis/: Prompt engineering analysis

3. demographic_data/
   - runs/: Demographic experiment runs
   - results/: Results for all demographic categories

4. training_data/
   - splits/: Train/test split configurations
   - results/: Training and holdout test results

5. batch_results/
   - Various batch processing results

6. v10_results/
   - Version 10 model results and analysis

7. handpicked_data/
   - Curated datasets for specific experiments

8. misc_data/
   - Other project data files

================================================================================
Created: organize_data_structure.py
================================================================================
