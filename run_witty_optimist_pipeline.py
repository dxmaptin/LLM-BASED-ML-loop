"""
Run prediction pipeline for Witty Optimist holdout concepts.

This script runs the full IR → Estimator → Critic pipeline on the 4 holdout concepts
to predict purchase intent.
"""

import pandas as pd
from pathlib import Path
import json
from openai import OpenAI
import os

# Configuration
BASE_DIR = Path(__file__).parent
WITTY_DIR = BASE_DIR / "project_data" / "witty_optimist_runs"
HOLDOUT_DIR = WITTY_DIR / "holdout_concepts"
PLAYBOOK_FILE = WITTY_DIR / "seed_prompt" / "witty_optimist_playbook.txt"
OUTPUT_FILE = WITTY_DIR / "predictions.csv"
DETAILED_OUTPUT = WITTY_DIR / "predictions_detailed.json"

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("="*80)
print("WITTY OPTIMIST PREDICTION PIPELINE")
print("="*80)

# ============================================================================
# STEP 1: Load Playbook
# ============================================================================

print("\n=== STEP 1: Loading Playbook ===")

with open(PLAYBOOK_FILE, 'r', encoding='utf-8') as f:
    playbook = f.read()

print(f"Loaded playbook: {len(playbook)} characters")

# ============================================================================
# STEP 2: Load Holdout Concepts
# ============================================================================

print("\n=== STEP 2: Loading Holdout Concepts ===")

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

    # Load ground truth KPIs
    kpi_file = concept_dir / "Flattened Data Inputs" / "kpi_scores.csv"
    if kpi_file.exists():
        kpi_df = pd.read_csv(kpi_file)
        kpis = {}
        for _, row in kpi_df.iterrows():
            kpis[row['Question']] = row['Value']
        concept_data['ground_truth_kpis'] = kpis
        concept_data['ground_truth_intent'] = kpis.get('pur_intent_pcttop')

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
    print(f"  [OK] Loaded: {clean_name} (Ground truth: {concept_data.get('ground_truth_intent')}%)")

print(f"\nTotal holdout concepts: {len(holdout_concepts)}")

# ============================================================================
# STEP 3: Run Predictions (IR → Estimator → Critic)
# ============================================================================

print("\n=== STEP 3: Running Predictions ===")

predictions = []

for i, concept in enumerate(holdout_concepts, 1):
    clean_name = concept.get('name', 'Unknown').replace('\u200b', '')
    print(f"\n[{i}/{len(holdout_concepts)}] Predicting: {clean_name}")
    print("-" * 80)

    # Build prediction prompt
    prediction_prompt = f"""You are predicting purchase intent for a new Soap & Glory product concept.

# PLAYBOOK

{playbook}

# CONCEPT TO ANALYZE

**Concept Name:** {concept.get('name', 'Unknown')}

**Vision Analysis:**
{concept.get('vision', 'No vision data available')}

**Consumer Verbatim Feedback:**
{concept.get('verbatims', 'No verbatim data available')[:3000]}

# YOUR TASK

Using the playbook above, predict the purchase intent percentage (pur_intent_pcttop) for this concept.

Follow the decision workflow:
1. Extract visual and verbal signals
2. Classify concept type (premium/budget, functional/indulgent)
3. Analyze consumer feedback patterns
4. Select baseline intent range
5. Apply adjustments based on unique features
6. Output prediction with rationale

# OUTPUT FORMAT

Return your prediction as JSON:

{{
  "predicted_purchase_intent": <number 0-100>,
  "confidence": <number 0-100>,
  "reasoning": {{
    "visual_signals": ["signal1", "signal2", ...],
    "verbatim_themes": ["theme1", "theme2", ...],
    "concept_type": "description",
    "baseline_range": "X-Y%",
    "adjustments": ["adjustment1 +X%", "adjustment2 -Y%"],
    "final_rationale": "2-3 sentence explanation"
  }}
}}

Analyze the concept now and provide your prediction.
"""

    try:
        # Call GPT-4o for prediction
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at predicting product concept purchase intent using structured analysis."},
                {"role": "user", "content": prediction_prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content
        result = json.loads(result_text)

        predicted_intent = result.get('predicted_purchase_intent', 0)
        confidence = result.get('confidence', 0)
        reasoning = result.get('reasoning', {})

        print(f"  [OK] Predicted Intent: {predicted_intent}%")
        print(f"       Ground Truth: {concept.get('ground_truth_intent')}%")
        print(f"       Error: {abs(predicted_intent - concept.get('ground_truth_intent', 0)):.1f}pp")
        print(f"       Confidence: {confidence}%")

        predictions.append({
            'concept_id': concept.get('concept_id'),
            'concept_name': concept.get('name'),
            'predicted_intent': predicted_intent,
            'ground_truth_intent': concept.get('ground_truth_intent'),
            'error': abs(predicted_intent - concept.get('ground_truth_intent', 0)),
            'confidence': confidence,
            'reasoning': reasoning
        })

    except Exception as e:
        print(f"  [ERROR] Prediction failed: {e}")
        predictions.append({
            'concept_id': concept.get('concept_id'),
            'concept_name': concept.get('name'),
            'predicted_intent': None,
            'ground_truth_intent': concept.get('ground_truth_intent'),
            'error': None,
            'confidence': None,
            'reasoning': {'error': str(e)}
        })

# ============================================================================
# STEP 4: Save Results
# ============================================================================

print("\n=== STEP 4: Saving Results ===")

# Save summary CSV
summary_df = pd.DataFrame([{
    'concept_id': p['concept_id'],
    'concept_name': p['concept_name'],
    'predicted_intent': p['predicted_intent'],
    'ground_truth_intent': p['ground_truth_intent'],
    'error_pp': p['error'],
    'confidence': p['confidence']
} for p in predictions])

summary_df.to_csv(OUTPUT_FILE, index=False)
print(f"[OK] Saved summary: {OUTPUT_FILE}")

# Save detailed JSON
with open(DETAILED_OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(predictions, f, indent=2)
print(f"[OK] Saved detailed results: {DETAILED_OUTPUT}")

# ============================================================================
# Summary Statistics
# ============================================================================

print("\n" + "="*80)
print("PREDICTION COMPLETE!")
print("="*80)

valid_predictions = [p for p in predictions if p['predicted_intent'] is not None]

if valid_predictions:
    errors = [p['error'] for p in valid_predictions]
    mae = sum(errors) / len(errors)

    print(f"\nResults Summary:")
    print(f"  Total concepts: {len(predictions)}")
    print(f"  Successful predictions: {len(valid_predictions)}")
    print(f"  Mean Absolute Error (MAE): {mae:.2f} percentage points")

    print(f"\nPer-Concept Results:")
    for p in predictions:
        clean_name = p['concept_name'].replace('\u200b', '') if p['concept_name'] else 'Unknown'
        if p['predicted_intent'] is not None:
            print(f"  • {clean_name}")
            print(f"    Predicted: {p['predicted_intent']}% | Actual: {p['ground_truth_intent']}% | Error: {p['error']:.1f}pp")
        else:
            print(f"  • {clean_name}: FAILED")

print(f"\nNext step:")
print(f"  Run evaluation: python calculate_r2_witty_optimist.py")

print("\n" + "="*80)
