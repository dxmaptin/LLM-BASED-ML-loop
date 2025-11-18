"""
Prompt Agent - Pattern Discovery and Prompt Generation

This agent analyzes quantitative and qualitative data to discover patterns
and generate baseline prompts for the Estimator Agent.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import os

from ..common.llm_providers import call_llm_provider


class PromptAgent:
    """
    Meta-learning agent that discovers patterns in data and generates
    optimized prompts for prediction.
    """

    def __init__(self, model: str = "gpt-5"):
        """
        Initialize Prompt Agent.

        Args:
            model: LLM model to use (default: gpt-5 for powerful analysis)
        """
        self.model = model
        print(f"[Prompt Agent] Initialized with model: {model}")

    def analyze_dataset(
        self,
        quant_dir: Path,
        qual_dir: Path,
        output_file: Path = None
    ) -> Dict[str, Any]:
        """
        Analyze entire dataset to discover patterns.

        Args:
            quant_dir: Directory with quantitative CSV files
            qual_dir: Directory with qualitative text files
            output_file: Where to save the generated prompt

        Returns:
            Dictionary with discovered patterns and generated prompt
        """
        print("\n" + "="*70)
        print("PROMPT AGENT: Dataset Analysis")
        print("="*70)

        # Step 1: Aggregate quantitative data
        print("\n[1/5] Aggregating quantitative data...")
        quant_summary = self._aggregate_quantitative(quant_dir)

        # Step 2: Aggregate qualitative data
        print("[2/5] Aggregating qualitative data...")
        qual_summary = self._aggregate_qualitative(qual_dir)

        # Step 3: Discover demographic patterns
        print("[3/5] Discovering demographic patterns...")
        demographic_patterns = self._discover_demographic_patterns(quant_summary, qual_summary)

        # Step 4: Discover concept-type patterns
        print("[4/5] Discovering concept-type patterns...")
        concept_patterns = self._discover_concept_patterns(quant_summary)

        # Step 5: Generate baseline prompt
        print("[5/5] Generating baseline prompt...")
        generated_prompt = self._generate_prompt(
            demographic_patterns,
            concept_patterns,
            quant_summary,
            qual_summary
        )

        # Save results
        results = {
            "demographic_patterns": demographic_patterns,
            "concept_patterns": concept_patterns,
            "generated_prompt": generated_prompt,
            "quantitative_summary": quant_summary,
            "qualitative_summary": qual_summary
        }

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n[OK] Results saved to: {output_file}")

        print("\n" + "="*70)
        print("ANALYSIS COMPLETE")
        print("="*70)

        return results

    def _aggregate_quantitative(self, quant_dir: Path) -> Dict[str, Any]:
        """Aggregate quantitative data from all class CSVs."""
        all_data = []
        class_dirs = [d for d in quant_dir.parent.iterdir() if d.is_dir()]

        for class_dir in class_dirs:
            csv_files = list((class_dir / "Flattened Data Inputs").glob("*.csv"))
            if csv_files:
                df = pd.read_csv(csv_files[0])
                df['class_name'] = class_dir.name
                all_data.append(df)

        if not all_data:
            return {}

        combined = pd.concat(all_data, ignore_index=True)

        # Analyze by category
        summary = {
            "total_classes": len(class_dirs),
            "total_rows": len(combined),
            "categories": {},
            "value_ranges": {},
            "high_variance_questions": []
        }

        for category in combined['Category'].unique():
            cat_data = combined[combined['Category'] == category]
            summary["categories"][category] = {
                "count": len(cat_data),
                "unique_questions": cat_data['Question'].nunique(),
                "unique_answers": cat_data['Answer'].nunique()
            }

        # Find high-variance questions (differ significantly across classes)
        for question in combined['Question'].unique()[:50]:  # Sample
            q_data = combined[combined['Question'] == question]
            if len(q_data) > 0 and 'Value' in q_data.columns:
                values = pd.to_numeric(q_data['Value'], errors='coerce').dropna()
                if len(values) > 5:
                    variance = values.var()
                    if variance > 0.05:  # High variance threshold
                        summary["high_variance_questions"].append({
                            "question": question,
                            "variance": float(variance),
                            "mean": float(values.mean()),
                            "min": float(values.min()),
                            "max": float(values.max())
                        })

        return summary

    def _aggregate_qualitative(self, qual_dir: Path) -> Dict[str, Any]:
        """Aggregate qualitative data from all pen portraits."""
        all_profiles = []
        class_dirs = [d for d in qual_dir.parent.iterdir() if d.is_dir()]

        for class_dir in class_dirs:
            txt_files = list((class_dir / "Textual Data Inputs").glob("*.txt"))
            if txt_files:
                with open(txt_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    all_profiles.append({
                        "class_name": class_dir.name,
                        "content": content[:2000]  # First 2000 chars
                    })

        summary = {
            "total_profiles": len(all_profiles),
            "sample_profiles": all_profiles[:5]  # Send sample to LLM
        }

        return summary

    def _discover_demographic_patterns(
        self,
        quant_summary: Dict,
        qual_summary: Dict
    ) -> Dict[str, Any]:
        """Use LLM to discover patterns across demographics."""

        prompt = f"""You are analyzing a dataset with {quant_summary.get('total_classes', 0)} demographic classes to discover patterns for prediction calibration.

QUANTITATIVE SUMMARY:
{json.dumps(quant_summary.get('categories', {}), indent=2)}

HIGH-VARIANCE QUESTIONS (differ significantly across classes):
{json.dumps(quant_summary.get('high_variance_questions', [])[:10], indent=2)}

QUALITATIVE SAMPLES (first 5 classes):
{json.dumps(qual_summary.get('sample_profiles', []), indent=2)}

TASK: Identify demographic patterns that would help calibrate predictions.

Analyze:
1. Which demographic factors correlate with higher/lower values?
2. Are there income-based patterns? (wealthy vs budget-constrained)
3. Are there age-based patterns? (young vs elderly)
4. Are there location-based patterns? (urban vs rural)
5. Are there lifecycle patterns? (families vs singles vs retirees)

Output JSON format:
{{
  "income_patterns": {{
    "high_income": "description and calibration (+Xpp for Y concepts)",
    "low_income": "description and calibration"
  }},
  "age_patterns": {{
    "young": "description and calibration",
    "middle_aged": "description and calibration",
    "elderly": "description and calibration"
  }},
  "lifestyle_patterns": {{
    "pattern_name": "description and calibration"
  }},
  "key_differentiators": ["factor 1", "factor 2", ...]
}}
"""

        print("  Calling LLM for demographic pattern discovery...")
        response = call_llm_provider(
            system_prompt="You are a data analyst discovering patterns across demographics.",
            user_prompt=prompt,
            model=self.model,
            temperature=0.3,
            max_tokens=2000
        )

        try:
            patterns = json.loads(response)
        except:
            patterns = {"raw_response": response}

        return patterns

    def _discover_concept_patterns(self, quant_summary: Dict) -> Dict[str, Any]:
        """Use LLM to discover concept-type patterns."""

        prompt = f"""You are analyzing survey data to discover patterns in how people respond to different types of questions/concepts.

CATEGORIES IN DATA:
{json.dumps(list(quant_summary.get('categories', {}).keys()), indent=2)}

SAMPLE HIGH-VARIANCE QUESTIONS:
{json.dumps(quant_summary.get('high_variance_questions', [])[:15], indent=2)}

TASK: Identify concept-type patterns for prediction allocation.

Analyze:
1. How do people respond to ATTITUDE questions? (opinions, beliefs)
2. How do people respond to BEHAVIOR questions? (actions, habits)
   - Low-friction behaviors (easy: "use", "prefer", "browse")
   - High-friction behaviors (hard: "switch", "invest", "purchase")
3. How do people respond to IDENTITY questions? ("I am...", "I consider myself...")
4. Are there category-specific patterns? (Financial vs Environment vs Lifestyle)

Output JSON format:
{{
  "attitude_pattern": {{
    "description": "...",
    "distribution_template": "SA X%, A Y%, N Z%, SD W%, SDD V%",
    "calibration_rules": ["rule 1", "rule 2"]
  }},
  "behavior_low_friction": {{ ... }},
  "behavior_high_friction": {{ ... }},
  "identity_pattern": {{ ... }},
  "category_specific": {{
    "Environment": "pattern",
    "Finance": "pattern",
    "Lifestyle": "pattern"
  }}
}}
"""

        print("  Calling LLM for concept pattern discovery...")
        response = call_llm_provider(
            system_prompt="You are a data analyst discovering concept-type patterns in survey data.",
            user_prompt=prompt,
            model=self.model,
            temperature=0.3,
            max_tokens=2000
        )

        try:
            patterns = json.loads(response)
        except:
            patterns = {"raw_response": response}

        return patterns

    def _generate_prompt(
        self,
        demographic_patterns: Dict,
        concept_patterns: Dict,
        quant_summary: Dict,
        qual_summary: Dict
    ) -> str:
        """Use LLM to generate the final baseline prompt."""

        prompt = f"""You are generating a SYSTEM PROMPT for an AI prediction agent that estimates survey responses across demographic segments.

INPUT DATA ANALYSIS:
- Total demographic classes: {quant_summary.get('total_classes', 0)}
- Categories: {list(quant_summary.get('categories', {}).keys())}

DISCOVERED DEMOGRAPHIC PATTERNS:
{json.dumps(demographic_patterns, indent=2)}

DISCOVERED CONCEPT PATTERNS:
{json.dumps(concept_patterns, indent=2)}

TASK: Generate a comprehensive GENERAL SYSTEM PROMPT that will be used by the Estimator Agent.

The prompt should include:

1. **OVERVIEW**: Brief description of the task
2. **DECISION WORKFLOW**: Step-by-step process (8 steps recommended)
3. **CONCEPT TYPE CLASSIFICATION**: Rules for identifying attitude/behavior/identity
4. **CONCEPT TYPE ALLOCATION**: Distribution templates per type
5. **DEMOGRAPHIC CALIBRATIONS**: General rules based on discovered patterns
6. **PROXIMAL GUARDRAILS**: Rules for handling exact data matches
7. **EVIDENCE HIERARCHY**: How to weight different evidence types
8. **CONFLICT HANDLING**: What to do when signals conflict
9. **OUTPUT FORMAT**: How to structure the response

IMPORTANT:
- Use the discovered patterns to inform calibrations
- Be specific with percentage adjustments (e.g., "+15pp", "LIFT by 20pp")
- Include reasoning for each rule
- Make it actionable and clear

Output the complete prompt as a string (not JSON).
"""

        print("  Calling LLM for prompt generation...")
        try:
            response = call_llm_provider(
                system_prompt="You are an expert prompt engineer creating system prompts for prediction agents.",
                user_prompt=prompt,
                model=self.model,
                temperature=0.2,
                max_tokens=4000
            )
            # call_llm_provider returns parsed JSON, but we want raw text
            # If it successfully parsed as JSON, convert back to string
            if isinstance(response, dict):
                return json.dumps(response, indent=2)
            return str(response)
        except:
            # If JSON parsing failed (which we expect for text), get raw content
            from ..common.llm_providers import call_openai_api
            response_obj = call_openai_api(
                system_prompt="You are an expert prompt engineer creating system prompts for prediction agents.",
                user_prompt=prompt,
                model=self.model,
                temperature=0.2,
                max_tokens=4000
            )
            return response_obj.content

    def generate_demographic_specific_prompt(
        self,
        class_name: str,
        quant_csv: Path,
        qual_txt: Path
    ) -> str:
        """
        Generate demographic-specific prompt for a single class.

        Args:
            class_name: Name of the demographic class
            quant_csv: Path to class-specific quantitative data
            qual_txt: Path to class pen portrait

        Returns:
            Demographic-specific prompt string
        """
        print(f"\n[Prompt Agent] Generating prompt for: {class_name}")

        # Load class-specific data
        df = pd.read_csv(quant_csv)

        # Convert Value column to numeric upfront to avoid dtype issues
        if 'Value' in df.columns:
            df['Value'] = pd.to_numeric(df['Value'], errors='coerce')

        with open(qual_txt, 'r', encoding='utf-8', errors='ignore') as f:
            pen_portrait = f.read()[:3000]

        # Analyze key attributes
        key_attributes = []

        # Age analysis
        age_data = df[df['Question'] == 'Age'].copy()
        age_data = age_data.dropna(subset=['Value'])  # Drop rows where conversion failed
        if len(age_data) > 0:
            age_dist = age_data.nlargest(min(3, len(age_data)), 'Value')[['Answer', 'Value']]
            key_attributes.append(f"Age: {age_dist.to_dict('records')}")

        # Income analysis
        income_data = df[df['Category'] == 'Economy']
        if len(income_data) > 0:
            key_attributes.append(f"Income indicators: {len(income_data)} datapoints")

        # Financial attitudes
        fin_att = df[df['Question'] == 'Financial Attitudes'].copy()
        fin_att = fin_att.dropna(subset=['Value'])  # Drop rows where conversion failed
        if len(fin_att) > 0:
            top_fin = fin_att.nlargest(min(5, len(fin_att)), 'Value')[['Answer', 'Value']]
            key_attributes.append(f"Top financial attitudes: {top_fin.to_dict('records')}")

        prompt_gen = f"""Generate a demographic-specific prompt for the class: {class_name}

PEN PORTRAIT:
{pen_portrait}

KEY QUANTITATIVE ATTRIBUTES:
{json.dumps(key_attributes, indent=2)}

TASK: Create a concise demographic-specific prompt with:
1. [Profile]: Age, income, key characteristics (2-3 sentences)
2. [Learned Calibrations]: Specific adjustments for this demographic
   - Digital behaviors: LIFT/REDUCE by Xpp
   - Financial attitudes: adjustments
   - Category-specific patterns
3. [Behavioral Patterns]: How this demographic makes decisions

Keep it under 300 words, actionable, specific.
"""

        try:
            response = call_llm_provider(
                system_prompt="You are creating demographic-specific prompts for prediction agents.",
                user_prompt=prompt_gen,
                model=self.model,
                temperature=0.2,
                max_tokens=1000
            )
            if isinstance(response, dict):
                return json.dumps(response, indent=2)
            return str(response)
        except:
            from ..common.llm_providers import call_openai_api
            response_obj = call_openai_api(
                system_prompt="You are creating demographic-specific prompts for prediction agents.",
                user_prompt=prompt_gen,
                model=self.model,
                temperature=0.2,
                max_tokens=1000
            )
            return response_obj.content


def run_prompt_discovery(
    dataset_dir: Path,
    output_dir: Path = None,
    model: str = "gpt-5"
):
    """
    Convenience function to run full prompt discovery on a dataset.

    Args:
        dataset_dir: Path to demographic_runs_ACORN or similar
        output_dir: Where to save outputs (default: dataset_dir/prompt_analysis)
        model: LLM model to use
    """
    if output_dir is None:
        output_dir = dataset_dir / "prompt_analysis"

    output_dir.mkdir(exist_ok=True)

    agent = PromptAgent(model=model)

    # Analyze full dataset
    results = agent.analyze_dataset(
        quant_dir=dataset_dir / "exclusive_addresses" / "Flattened Data Inputs",  # Use first as reference
        qual_dir=dataset_dir / "exclusive_addresses" / "Textual Data Inputs",
        output_file=output_dir / "analysis_results.json"
    )

    # Save generated prompt
    prompt_file = output_dir / "generated_baseline_prompt.txt"
    with open(prompt_file, 'w') as f:
        f.write(results["generated_prompt"])

    print(f"\n[OK] Generated baseline prompt saved to: {prompt_file}")

    # Generate class-specific prompts
    print("\n" + "="*70)
    print("Generating class-specific prompts...")
    print("="*70)

    class_prompts = {}
    for class_dir in sorted(dataset_dir.iterdir()):
        if not class_dir.is_dir():
            continue

        quant_csv = list((class_dir / "Flattened Data Inputs").glob("*.csv"))
        qual_txt = list((class_dir / "Textual Data Inputs").glob("*.txt"))

        if quant_csv and qual_txt:
            class_prompt = agent.generate_demographic_specific_prompt(
                class_name=class_dir.name,
                quant_csv=quant_csv[0],
                qual_txt=qual_txt[0]
            )
            class_prompts[class_dir.name] = class_prompt

    # Save class-specific prompts
    class_prompts_file = output_dir / "class_specific_prompts.json"
    with open(class_prompts_file, 'w') as f:
        json.dump(class_prompts, f, indent=2)

    print(f"\n[OK] Class-specific prompts saved to: {class_prompts_file}")

    return results, class_prompts
