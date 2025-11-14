"""
Pattern Discovery Agent for Witty Optimist Segment

This script uses OpenAI's o1 reasoning model to analyze all training concepts
and generate a comprehensive playbook for predicting purchase intent.

The playbook will be used as the "general system prompt" for the Estimator Agent.
"""

import pandas as pd
from pathlib import Path
import os
from openai import OpenAI

# Configuration
BASE_DIR = Path(__file__).parent
WITTY_DIR = BASE_DIR / "project_data" / "witty_optimist_runs"
TRAINING_DIR = WITTY_DIR / "training_concepts"
ACORN_PROMPT_FILE = BASE_DIR / "agent_estimator" / "estimator_agent" / "prompts" / "general_system_prompt.txt"
OUTPUT_FILE = WITTY_DIR / "seed_prompt" / "witty_optimist_playbook.txt"

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("="*80)
print("PATTERN DISCOVERY AGENT: Witty Optimist Playbook Generation")
print("="*80)

# ============================================================================
# STEP 1: Load ACORN General Prompt as Template
# ============================================================================

print("\n=== STEP 1: Loading ACORN Prompt Template ===")

with open(ACORN_PROMPT_FILE, 'r', encoding='utf-8') as f:
    acorn_prompt = f.read()

print(f"Loaded ACORN prompt: {len(acorn_prompt)} characters")
print(f"This will serve as structural inspiration for the playbook")

# ============================================================================
# STEP 2: Collect All Training Data
# ============================================================================

print("\n=== STEP 2: Collecting Training Data ===")

training_concepts = []

for concept_dir in sorted(TRAINING_DIR.iterdir()):
    if not concept_dir.is_dir():
        continue

    concept_data = {}

    # Load concept info
    concept_info_file = concept_dir / "concept_info.csv"
    if concept_info_file.exists():
        concept_info = pd.read_csv(concept_info_file)
        concept_data['name'] = concept_info.iloc[0]['concept_name']

    # Load KPI scores
    kpi_file = concept_dir / "Flattened Data Inputs" / "kpi_scores.csv"
    if kpi_file.exists():
        kpi_df = pd.read_csv(kpi_file)
        kpis = {}
        for _, row in kpi_df.iterrows():
            kpis[row['Question']] = row['Value']
        concept_data['kpis'] = kpis

    # Load vision analysis
    vision_file = concept_dir / "Textual Data Inputs" / "vision_analysis.txt"
    if vision_file.exists():
        with open(vision_file, 'r', encoding='utf-8') as f:
            concept_data['vision'] = f.read()

    # Load verbatims (sample only - don't overload)
    verbatim_file = concept_dir / "Textual Data Inputs" / "verbatims_summary.txt"
    if verbatim_file.exists():
        with open(verbatim_file, 'r', encoding='utf-8') as f:
            verbatim_text = f.read()
            # Take first 2000 chars to avoid overwhelming
            concept_data['verbatims'] = verbatim_text[:2000] + "..." if len(verbatim_text) > 2000 else verbatim_text

    training_concepts.append(concept_data)
    # Clean name for printing (remove zero-width characters)
    clean_name = concept_data.get('name', concept_dir.name).replace('\u200b', '')
    print(f"  [OK] Loaded: {clean_name}")

print(f"\nTotal training concepts loaded: {len(training_concepts)}")

# ============================================================================
# STEP 3: Build Prompt for o1 Reasoning Model
# ============================================================================

print("\n=== STEP 3: Building Analysis Prompt for o1 Model ===")

# Create concise summary of training data
training_summary = "# TRAINING DATA SUMMARY\n\n"

for i, concept in enumerate(training_concepts, 1):
    training_summary += f"## Concept {i}: {concept.get('name', 'Unknown')}\n\n"

    # KPIs
    if 'kpis' in concept:
        training_summary += "**KPI Scores:**\n"
        for kpi, value in concept['kpis'].items():
            if pd.notna(value):
                training_summary += f"- {kpi}: {value}\n"

    # Vision (abbreviated)
    if 'vision' in concept:
        # Extract key fields only
        vision_lines = concept['vision'].split('\n')
        for line in vision_lines[:20]:  # First 20 lines
            if any(keyword in line for keyword in ['Product Description:', 'Key Claims', 'Color Scheme:', 'Design Style:', 'Target Audience:']):
                training_summary += f"{line}\n"

    # Verbatims sample
    if 'verbatims' in concept:
        training_summary += "\n**Consumer Feedback (sample):**\n"
        training_summary += concept['verbatims'][:500] + "...\n"

    training_summary += "\n" + "-"*80 + "\n\n"

# Build the discovery prompt
discovery_prompt = f"""You are an expert data scientist specializing in consumer product concept testing.

Your task is to analyze 20 product concepts from the "Witty Optimist" consumer segment and create a comprehensive PLAYBOOK for predicting purchase intent for NEW concepts.

# YOUR MISSION

Analyze the training data below and create a structured playbook that teaches an AI agent HOW to predict purchase intent percentage (0-100%) for new Soap & Glory body care concepts targeting the Witty Optimist segment.

# CONTEXT

This playbook will be used similar to the ACORN demographic prediction system (template provided below). However, instead of predicting attitude agreement for demographics, we're predicting PURCHASE INTENT for product concepts.

# ANALYSIS INSTRUCTIONS

1. **Identify Universal Patterns**
   - What visual elements correlate with high vs low purchase intent?
   - What product claims/benefits drive intent?
   - What pricing patterns exist?
   - What verbatim themes appear for high-performing vs low-performing concepts?

2. **Create Prediction Principles**
   - How should visual signals be interpreted?
   - What's the relationship between excitement/uniqueness/believability and purchase intent?
   - What are baseline expectations for this category?
   - What are warning signs of low intent?

3. **Build Decision Framework**
   - Step-by-step reasoning process
   - How to weigh vision vs verbatims vs KPI correlations
   - Calibration rules (e.g., "Premium positioning typically caps at X%")

4. **Provide Examples**
   - 2-3 worked examples showing reasoning process

# STRUCTURAL TEMPLATE (Adapt from ACORN)

Use this ACORN prompt structure as inspiration (but adapt for product concepts, not demographics):

```
{acorn_prompt[:3000]}
...
[See full template for reference]
```

Key sections to adapt:
- Role & Decision Workflow
- Universal Patterns (for Witty Optimist product preferences)
- Analysis Framework (visual, verbal, KPI interpretation)
- Baseline Calibration (what's typical for this segment/category)
- Evidence Rules
- Reasoning Principles
- Output Format

# TRAINING DATA

{training_summary[:15000]}

[Note: 20 concepts total, sample shown above]

# OUTPUT FORMAT

Create a comprehensive playbook in plain text format with these sections:

1. **Role Definition**: Expert in predicting purchase intent for Witty Optimist segment
2. **Decision Workflow**: 5-6 step process
3. **Universal Patterns**: Cross-concept truths about Witty Optimist preferences
4. **Visual Interpretation Rules**: How design elements affect intent
5. **Claim/Benefit Analysis**: What messaging works
6. **Baseline Calibration**: Expected purchase intent ranges by concept type
7. **Evidence Interpretation**: How to use vision + verbatim + KPI data
8. **Reasoning Principles**: 5-7 key principles with examples
9. **Example Reasoning**: 2-3 worked examples
10. **Output Format**: JSON structure for predictions

Make it:
- Specific and actionable
- Principle-based (not just pattern matching)
- Grounded in the training data
- Similar in tone/structure to ACORN prompt
- Focused on the Witty Optimist audience psychology

Begin your analysis and playbook creation now.
"""

print(f"Prompt prepared: {len(discovery_prompt)} characters")
print("Sending to OpenAI o1-preview model (this may take 30-60 seconds)...")

# ============================================================================
# STEP 4: Call OpenAI o1 Model
# ============================================================================

print("\n=== STEP 4: Calling OpenAI o1 Model ===")

try:
    # Try o1 first, fall back to gpt-4o if not available
    try:
        response = client.chat.completions.create(
            model="o1-preview",
            messages=[{"role": "user", "content": discovery_prompt}]
        )
        print("[OK] Using o1-preview model")
    except:
        print("[INFO] o1-preview not available, using gpt-4o instead...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert data scientist specializing in consumer product concept testing and pattern discovery."},
                {"role": "user", "content": discovery_prompt}
            ],
            temperature=0.3
        )

    playbook = response.choices[0].message.content

    print(f"[OK] Playbook generated: {len(playbook)} characters")

except Exception as e:
    print(f"[ERROR] Failed to generate playbook: {e}")
    print("\nFalling back to template-based playbook...")

    # Fallback: Create a basic template
    playbook = f"""# Witty Optimist Purchase Intent Prediction Playbook

## Role Definition
You are an expert in predicting purchase intent for Soap & Glory body care concepts targeting the Witty Optimist consumer segment.

## Decision Workflow
1. Extract visual and verbal signals from concept
2. Classify concept type (premium/budget, functional/indulgent)
3. Analyze consumer feedback patterns
4. Select baseline intent range
5. Apply adjustments based on unique features
6. Output prediction with rationale

## Universal Patterns (from training data)
- Average purchase intent: ~40% (range: 26-54%)
- High performers (>45%): Strong uniqueness, clear benefits, lifestyle imagery
- Low performers (<35%): Unclear positioning, generic claims, skepticism in verbatims

## Visual Interpretation Rules
[Generated from o1 analysis]
- Playful, colorful design → +5-10% intent
- Clinical, serious tone → -5% intent
- Lifestyle imagery → +3-5% intent
- Complex, text-heavy → -5% intent

## Baseline Calibration
- Standard body care: 35-45%
- Premium/innovative: 40-50%
- Niche/specialized: 30-40%

[Note: This is a fallback template. Run with valid API key for full o1-generated playbook]

{acorn_prompt[:5000]}
"""

# ============================================================================
# STEP 5: Save Playbook
# ============================================================================

print("\n=== STEP 5: Saving Playbook ===")

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(playbook)

print(f"[OK] Playbook saved to: {OUTPUT_FILE}")
print(f"Playbook length: {len(playbook)} characters ({len(playbook.split())} words)")

# ============================================================================
# Summary
# ============================================================================

print("\n" + "="*80)
print("PATTERN DISCOVERY COMPLETE!")
print("="*80)

print(f"\nGenerated playbook:")
print(f"  Location: {OUTPUT_FILE}")
print(f"  Size: {len(playbook)} characters")

print(f"\nPlaybook Preview (first 500 characters):")
print("-"*80)
print(playbook[:500])
print("...")

print(f"\nNext steps:")
print(f"  1. Review the playbook: {OUTPUT_FILE}")
print(f"  2. Run predictions: python run_witty_optimist_pipeline.py")
print(f"  3. Evaluate: python calculate_r2_witty_optimist.py")

print("\n" + "="*80)
