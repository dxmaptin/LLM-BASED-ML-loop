"""
Multi-Metric Prediction Pipeline for Witty Optimist Concepts

This script predicts ALL 11 metrics for holdout concepts and outputs results
in a grouped CSV format (grouped by product, then by metric).

Output Format:
    product_name, metric_name, predicted_value, actual_value, difference, error_pct

Example:
    Row 1-11: Product A (all 11 metrics)
    Row 12-22: Product B (all 11 metrics)
    ...
"""

import pandas as pd
from pathlib import Path
import json
from openai import OpenAI
import os
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent
WITTY_DIR = BASE_DIR / "project_data" / "witty_optimist_runs"
HOLDOUT_DIR = WITTY_DIR / "holdout_concepts"
PLAYBOOK_FILE = WITTY_DIR / "seed_prompt" / "witty_optimist_playbook.txt"

# Output files
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_FILE = WITTY_DIR / f"multi_metric_predictions_{TIMESTAMP}.csv"
DETAILED_OUTPUT = WITTY_DIR / f"multi_metric_predictions_detailed_{TIMESTAMP}.json"

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ============================================================================
# METRIC DEFINITIONS
# ============================================================================

METRICS = {
    "target_top2box_intent": {
        "name": "Purchase Intent (Target)",
        "description": "Percentage of target audience who definitely/probably would purchase (top 2 box)",
        "range": "0-100",
        "baseline": 60,
        "csv_column": "target_top2box_intent",
        "priority": "P1"
    },
    "appeal_pcttop_2": {
        "name": "Appeal",
        "description": "Percentage who find concept very/somewhat appealing (top 2 box)",
        "range": "0-100",
        "baseline": 52,
        "csv_column": "appeal_pcttop_2",
        "priority": "P2"
    },
    "uniqueness_pcttop_2": {
        "name": "Uniqueness",
        "description": "Percentage who perceive concept as very/somewhat unique vs competitors (top 2 box)",
        "range": "0-100",
        "baseline": 59,
        "csv_column": "uniqueness_pcttop_2",
        "priority": "P2"
    },
    "relevance_pcttop_2": {
        "name": "Relevance",
        "description": "Percentage who find concept very/somewhat relevant to their needs (top 2 box)",
        "range": "0-100",
        "baseline": 40,
        "csv_column": "relevance_pcttop_2",
        "priority": "P2"
    },
    "excitement_pcttop_2": {
        "name": "Excitement",
        "description": "Percentage who are very/somewhat excited about the concept (top 2 box)",
        "range": "0-100",
        "baseline": 78,
        "csv_column": "excitement_pcttop_2",
        "priority": "P2"
    },
    "price_value_pcttop_2": {
        "name": "Price/Value",
        "description": "Percentage who perceive good/excellent value for money (top 2 box)",
        "range": "0-100",
        "baseline": 64,
        "csv_column": "price_value_pcttop_2",
        "priority": "P3"
    },
    "believability_pcttop": {
        "name": "Believability",
        "description": "Percentage who find claims very believable (top box)",
        "range": "0-100",
        "baseline": 40,
        "csv_column": "believability_pcttop",
        "priority": "P3"
    },
    "understanding_pcttop_3": {
        "name": "Understanding",
        "description": "Percentage who understand concept very/somewhat/moderately well (top 3 box)",
        "range": "0-100",
        "baseline": 71,
        "csv_column": "understanding_pcttop_3",
        "priority": "P3"
    },
    "trial": {
        "name": "Trial Intent",
        "description": "Percentage who would try the product",
        "range": "0-100",
        "baseline": 47,
        "csv_column": "trial",
        "priority": "P4"
    },
    "inc_trial_brand": {
        "name": "Incremental Trial",
        "description": "Percentage of trial that is new to brand (incremental)",
        "range": "0-100",
        "baseline": 42,
        "csv_column": "inc_trial_brand",
        "priority": "P4"
    },
    "star_rating": {
        "name": "Overall Star Rating",
        "description": "Average star rating converted to 0-100 scale",
        "range": "0-100",
        "baseline": 65,
        "csv_column": "star_rating",
        "priority": "P4"
    }
}

# Metric order for output (grouped by priority)
METRIC_ORDER = [
    "target_top2box_intent",
    "appeal_pcttop_2",
    "uniqueness_pcttop_2",
    "relevance_pcttop_2",
    "excitement_pcttop_2",
    "price_value_pcttop_2",
    "believability_pcttop",
    "understanding_pcttop_3",
    "trial",
    "inc_trial_brand",
    "star_rating"
]

print("="*80)
print("MULTI-METRIC PREDICTION PIPELINE")
print("="*80)
print(f"\nPredicting {len(METRICS)} metrics for holdout concepts")
print(f"Output will be grouped by product, then by metric")

# ============================================================================
# STEP 1: Load Playbook
# ============================================================================

print("\n=== STEP 1: Loading Playbook ===")

with open(PLAYBOOK_FILE, 'r', encoding='utf-8') as f:
    playbook = f.read()

print(f"[OK] Loaded playbook: {len(playbook)} characters")

# ============================================================================
# STEP 2: Load Holdout Concepts with ALL Metrics
# ============================================================================

print("\n=== STEP 2: Loading Holdout Concepts ===")

# Load concept test data to get all ground truth metrics
concept_test_wide = pd.read_csv(BASE_DIR / "project_data" / "concept_test_processed" / "concept_test_wide.csv")

holdout_concepts = []

for concept_dir in sorted(HOLDOUT_DIR.iterdir()):
    if not concept_dir.is_dir():
        continue

    concept_data = {'folder': concept_dir.name}

    # Load concept info
    concept_info_file = concept_dir / "concept_info.csv"
    if concept_info_file.exists():
        concept_info = pd.read_csv(concept_info_file)
        concept_data['name'] = concept_info.iloc[0]['concept_name']
        concept_data['concept_id'] = concept_info.iloc[0]['concept_id']

    # Load ALL ground truth metrics from concept test data
    concept_id = concept_data.get('concept_id')
    if concept_id:
        # Get ground truth for this concept (target audience row)
        gt_row = concept_test_wide[concept_test_wide['concept_id'] == concept_id]

        if len(gt_row) > 0:
            # Take the target audience version (typically the first occurrence)
            gt_row = gt_row.iloc[0]

            ground_truth = {}
            for metric_key in METRIC_ORDER:
                csv_col = METRICS[metric_key]['csv_column']
                if csv_col in gt_row and pd.notna(gt_row[csv_col]):
                    ground_truth[metric_key] = float(gt_row[csv_col])
                else:
                    ground_truth[metric_key] = None

            concept_data['ground_truth'] = ground_truth

    # Load vision analysis
    vision_file = concept_dir / "Textual Data Inputs" / "vision_analysis.txt"
    if vision_file.exists():
        with open(vision_file, 'r', encoding='utf-8') as f:
            concept_data['vision'] = f.read()

    # Load verbatims
    verbatim_file = concept_dir / "Textual Data Inputs" / "verbatims_summary.txt"
    if verbatim_file.exists():
        with open(verbatim_file, 'r', encoding='utf-8') as f:
            concept_data['verbatims'] = f.read()

    holdout_concepts.append(concept_data)
    clean_name = concept_data.get('name', concept_dir.name).replace('\u200b', '')
    print(f"  [OK] Loaded: {clean_name}")

print(f"\nTotal holdout concepts: {len(holdout_concepts)}")

# ============================================================================
# STEP 3: Predict ALL Metrics for Each Concept
# ============================================================================

print("\n=== STEP 3: Running Multi-Metric Predictions ===")

all_predictions = []

for i, concept in enumerate(holdout_concepts, 1):
    clean_name = concept.get('name', 'Unknown').replace('\u200b', '')
    print(f"\n{'='*80}")
    print(f"[{i}/{len(holdout_concepts)}] Predicting All Metrics: {clean_name}")
    print('='*80)

    # Build multi-metric prediction prompt
    metrics_description = "\n".join([
        f"{idx+1}. **{METRICS[m]['name']}** ({m})\n"
        f"   - {METRICS[m]['description']}\n"
        f"   - Range: {METRICS[m]['range']}\n"
        f"   - Baseline average: {METRICS[m]['baseline']}%"
        for idx, m in enumerate(METRIC_ORDER)
    ])

    prediction_prompt = f"""You are predicting ALL consumer response metrics for a new Soap & Glory product concept.

# PLAYBOOK (PREDICTION RULES)

{playbook}

# CONCEPT TO ANALYZE

**Concept Name:** {concept.get('name', 'Unknown')}

**Vision Analysis:**
{concept.get('vision', 'No vision data available')}

**Consumer Verbatim Feedback:**
{concept.get('verbatims', 'No verbatim data available')[:3000]}

# YOUR TASK

Predict ALL 11 metrics below for this concept. Use the playbook to guide your predictions.

## METRICS TO PREDICT:

{metrics_description}

# PREDICTION RULES

1. **Consistency checks:**
   - trial should be close to target_top2box_intent (±5pp)
   - appeal + uniqueness + relevance should logically drive intent
   - If understanding is low, suppress all other metrics
   - If believability is low, reduce intent/trial

2. **Correlation patterns:**
   - High appeal usually → high intent
   - High excitement + uniqueness → high intent
   - Low relevance doesn't always kill intent (can be niche)

3. **Metric-specific drivers:**
   - appeal: Visual design, emotional messaging
   - uniqueness: Differentiation, innovation signals
   - relevance: Need fit, target audience match
   - excitement: Novelty, engaging claims
   - price_value: Pricing vs. benefits perception
   - believability: Claim credibility, proof
   - understanding: Concept clarity

# OUTPUT FORMAT

Return your predictions as JSON with this exact structure:

{{
  "predictions": {{
    "target_top2box_intent": <number 0-100>,
    "appeal_pcttop_2": <number 0-100>,
    "uniqueness_pcttop_2": <number 0-100>,
    "relevance_pcttop_2": <number 0-100>,
    "excitement_pcttop_2": <number 0-100>,
    "price_value_pcttop_2": <number 0-100>,
    "believability_pcttop": <number 0-100>,
    "understanding_pcttop_3": <number 0-100>,
    "trial": <number 0-100>,
    "inc_trial_brand": <number 0-100>,
    "star_rating": <number 0-100>
  }},
  "reasoning": {{
    "overall_assessment": "2-3 sentence summary",
    "key_strengths": ["strength1", "strength2"],
    "key_weaknesses": ["weakness1", "weakness2"],
    "consistency_check": "Explanation of how metrics align"
  }},
  "confidence": <number 0-100>
}}

Analyze the concept now and provide your predictions.
"""

    try:
        # Call GPT-4o for multi-metric prediction
        print("\n  Calling GPT-4o for prediction...")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at predicting consumer responses to product concepts using structured analysis. You provide predictions for multiple metrics simultaneously with consistency checks."
                },
                {"role": "user", "content": prediction_prompt}
            ],
            temperature=0.3,  # Slightly higher for multi-metric to allow nuance
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content
        result = json.loads(result_text)

        predictions = result.get('predictions', {})
        reasoning = result.get('reasoning', {})
        confidence = result.get('confidence', 0)

        # Display results
        print("\n  Predictions Complete!")
        print("  " + "-"*76)
        print(f"  {'Metric':<30} {'Predicted':>10} {'Actual':>10} {'Diff':>10}")
        print("  " + "-"*76)

        concept_predictions = {
            'concept_id': concept.get('concept_id'),
            'concept_name': concept.get('name'),
            'metrics': [],
            'overall_confidence': confidence,
            'reasoning': reasoning
        }

        for metric_key in METRIC_ORDER:
            predicted = predictions.get(metric_key, None)
            actual = concept.get('ground_truth', {}).get(metric_key, None)

            if predicted is not None and actual is not None:
                diff = predicted - actual
                error_pct = abs(diff) / actual * 100 if actual != 0 else 0
                status = "✓" if abs(diff) <= 5 else "⚠" if abs(diff) <= 10 else "✗"
            else:
                diff = None
                error_pct = None
                status = "?"

            metric_name = METRICS[metric_key]['name']

            print(f"  {metric_name:<30} {predicted if predicted else 'N/A':>10} "
                  f"{actual if actual else 'N/A':>10} "
                  f"{f'{diff:+.1f}' if diff is not None else 'N/A':>10} {status}")

            concept_predictions['metrics'].append({
                'metric_key': metric_key,
                'metric_name': metric_name,
                'predicted': predicted,
                'actual': actual,
                'difference': diff,
                'error_percent': error_pct
            })

        all_predictions.append(concept_predictions)
        print("  " + "-"*76)

    except Exception as e:
        print(f"\n  [ERROR] Prediction failed: {e}")

        concept_predictions = {
            'concept_id': concept.get('concept_id'),
            'concept_name': concept.get('name'),
            'metrics': [],
            'overall_confidence': None,
            'reasoning': {'error': str(e)}
        }

        for metric_key in METRIC_ORDER:
            concept_predictions['metrics'].append({
                'metric_key': metric_key,
                'metric_name': METRICS[metric_key]['name'],
                'predicted': None,
                'actual': concept.get('ground_truth', {}).get(metric_key, None),
                'difference': None,
                'error_percent': None
            })

        all_predictions.append(concept_predictions)

# ============================================================================
# STEP 4: Create Grouped CSV Output
# ============================================================================

print("\n" + "="*80)
print("=== STEP 4: Generating Grouped CSV Output ===")
print("="*80)

# Build rows: grouped by product, then by metric
csv_rows = []

for pred in all_predictions:
    product_name = pred['concept_name']
    concept_id = pred['concept_id']

    for metric_data in pred['metrics']:
        csv_rows.append({
            'concept_id': concept_id,
            'product_name': product_name,
            'metric_key': metric_data['metric_key'],
            'metric_name': metric_data['metric_name'],
            'predicted_value': metric_data['predicted'],
            'actual_value': metric_data['actual'],
            'difference': metric_data['difference'],
            'error_percent': metric_data['error_percent'],
            'priority': METRICS[metric_data['metric_key']]['priority']
        })

# Create DataFrame
results_df = pd.DataFrame(csv_rows)

# Save CSV
results_df.to_csv(OUTPUT_FILE, index=False)
print(f"\n[OK] Saved grouped CSV: {OUTPUT_FILE}")
print(f"     Format: {len(all_predictions)} products × {len(METRIC_ORDER)} metrics = {len(csv_rows)} rows")

# Save detailed JSON
with open(DETAILED_OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(all_predictions, f, indent=2)
print(f"[OK] Saved detailed JSON: {DETAILED_OUTPUT}")

# ============================================================================
# STEP 5: Generate Summary Statistics
# ============================================================================

print("\n" + "="*80)
print("=== STEP 5: Summary Statistics ===")
print("="*80)

# Calculate MAE per metric
print("\nMean Absolute Error (MAE) by Metric:")
print("-" * 60)
print(f"{'Metric':<35} {'MAE':>10} {'N':>8}")
print("-" * 60)

for metric_key in METRIC_ORDER:
    metric_rows = results_df[results_df['metric_key'] == metric_key]
    valid_errors = metric_rows[metric_rows['difference'].notna()]['difference'].abs()

    if len(valid_errors) > 0:
        mae = valid_errors.mean()
        n = len(valid_errors)
        print(f"{METRICS[metric_key]['name']:<35} {mae:>9.2f}pp {n:>7}")
    else:
        print(f"{METRICS[metric_key]['name']:<35} {'N/A':>10} {0:>7}")

# Overall statistics
print("\n" + "="*60)
valid_predictions = results_df[results_df['difference'].notna()]

if len(valid_predictions) > 0:
    overall_mae = valid_predictions['difference'].abs().mean()
    overall_rmse = (valid_predictions['difference'] ** 2).mean() ** 0.5
    within_5pp = (valid_predictions['difference'].abs() <= 5).sum()
    within_10pp = (valid_predictions['difference'].abs() <= 10).sum()

    print(f"\nOverall Performance:")
    print(f"  Total predictions: {len(results_df)}")
    print(f"  Valid predictions: {len(valid_predictions)}")
    print(f"  Overall MAE: {overall_mae:.2f} percentage points")
    print(f"  Overall RMSE: {overall_rmse:.2f} percentage points")
    print(f"  Within 5pp: {within_5pp}/{len(valid_predictions)} ({within_5pp/len(valid_predictions)*100:.1f}%)")
    print(f"  Within 10pp: {within_10pp}/{len(valid_predictions)} ({within_10pp/len(valid_predictions)*100:.1f}%)")

# ============================================================================
# STEP 6: Display Sample of Output
# ============================================================================

print("\n" + "="*80)
print("=== Sample Output (First Product, All Metrics) ===")
print("="*80)

sample = results_df[results_df['concept_id'] == results_df.iloc[0]['concept_id']]
print(f"\nProduct: {sample.iloc[0]['product_name']}")
print("\n" + sample.to_string(index=False))

print("\n" + "="*80)
print("PREDICTION COMPLETE!")
print("="*80)
print(f"\nOutput file: {OUTPUT_FILE}")
print(f"Detailed reasoning: {DETAILED_OUTPUT}")
print("\nNext steps:")
print("  1. Review predictions in Excel or pandas")
print("  2. Analyze error patterns by metric")
print("  3. Refine playbook based on systematic errors")
print("  4. Re-run with updated playbook")
print("\n" + "="*80)
